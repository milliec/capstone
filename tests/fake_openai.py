"""A fake OpenAI server for tests (B3 step 7b, PR 3).

It speaks just enough of OpenAI's chat completions API (`POST /v1/chat/completions`) for the
`openai` client, which CrewAI uses, to talk to it. It runs on this machine only (127.0.0.1) in a
background thread of the test, so a test can make the "model" answer, fail, be slow or refuse a
setting, and then COUNT the requests that actually arrived. That count is the point (H-065): one
unit sends exactly one request, except our one DL-43 retry and CrewAI's silent repeat.

No real key and no real model: the key a test sends is a placeholder, and nothing here reaches
the outside world. A request nobody scripted gets an error and is written down in `unscripted`,
so an extra call can never pass unnoticed.

Use the `fake_openai` fixture (tests/conftest.py). Example:

    def test_one_call(fake_openai):
        fake_openai.script(Reply({"rows": []}, tokens_in=900, tokens_out=40))
        ... send one request to fake_openai.base_url ...
        assert len(fake_openai.requests) == 1
"""

import copy
import json
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TEST_API_KEY = "test-key-not-a-real-key"


@dataclass
class Reply:
    """The model answers. `content` is text, or a dict/list that is sent as JSON text (what a
    structured-output answer looks like). `delay_s` makes the server slow before it answers."""
    content: object
    tokens_in: int = 1000
    tokens_out: int = 100
    finish_reason: str = "stop"
    model: str | None = None          # the model string the API returns; None echoes the request's
    delay_s: float = 0.0


@dataclass
class Failure:
    """The provider answers with an error. 429 and 5xx carry a `retry-after-ms` of 1 so a client
    that retries does not make the test wait."""
    status: int = 500
    message: str = "The server had an error"
    error_type: str = "server_error"
    param: str | None = None
    code: str | None = None
    delay_s: float = 0.0


@dataclass
class SeenRequest:
    """One request that reached the fake."""
    path: str
    body: dict
    api_key: str                      # what the client sent as its key (always the test placeholder)

    @property
    def model(self) -> str:
        return self.body.get("model", "")


@dataclass
class FakeOpenAI:
    reject_params: frozenset = frozenset()   # a request carrying one of these gets a 400, as OpenAI
    requests: list = field(default_factory=list)          # does for a model that refuses a setting
    unscripted: list = field(default_factory=list)
    _script: list = field(default_factory=list)
    _responder: object = None         # asked FIRST for every chat request; see `answer_with`
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _server: ThreadingHTTPServer | None = None
    _thread: threading.Thread | None = None

    # --- Writing the script -------------------------------------------------------------------

    def script(self, *behaviours: "Reply | Failure") -> None:
        """Queue answers, used one per request, in order."""
        with self._lock:
            self._script.extend(behaviours)

    def answer_with(self, responder) -> None:
        """Answer by LOOKING at the request, instead of in the order of a queue.

        `responder(body)` gets a copy of the request body (the model and the messages) and returns a
        `Reply`, a `Failure`, or `None` for "no opinion", in which case the request falls through to
        the queue (`script`) exactly as before. The point (spike fix, integration): a whole review
        sends about 18 requests to three models, so a queue would tie a test to the exact ORDER of the
        calls. A responder says "the extractor's model, asked about this document" and answers that.

        It is called from the server's own threads, so it must not change shared state. A request that
        the responder answers is still written down in `requests`; one it declines can still end up in
        `unscripted`."""
        self._responder = responder

    def unused(self) -> int:
        """How many scripted answers no request has used (0 when the test sent what it planned)."""
        with self._lock:
            return len(self._script)

    # --- Starting and stopping ----------------------------------------------------------------

    @property
    def base_url(self) -> str:
        """What the client is pointed at (the `base_url` of the OpenAI client)."""
        return f"http://127.0.0.1:{self._server.server_address[1]}/v1"

    def start(self) -> "FakeOpenAI":
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):        # keep the test output quiet
                pass

            def do_POST(self):
                length = int(self.headers.get("content-length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
                key = (self.headers.get("authorization") or "").removeprefix("Bearer ")
                status, payload, headers = fake._answer(self.path, body, key)
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(data)))
                for name, value in headers.items():
                    self.send_header(name, value)
                self.end_headers()
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass                          # the client gave up first (a timeout test)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(
            target=lambda: self._server.serve_forever(poll_interval=0.01), daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()

    # --- Answering one request ----------------------------------------------------------------

    def _answer(self, path: str, body: dict, api_key: str):
        """(status, JSON payload, extra headers). The request is written down FIRST, so a request
        that is refused or times out is still counted."""
        if path.endswith("/input_tokens"):
            # OpenAI's "count this prompt's tokens" endpoint. CrewAI calls it as a pre-flight when
            # it believes it is talking to OpenAI itself (see the `as_openai` fixture). It is written
            # down like any request, so a test can see it, but it takes no scripted answer.
            with self._lock:
                self.requests.append(SeenRequest(path, body, api_key))
            return 200, {"object": "response.input_tokens", "input_tokens": 1500}, {}
        with self._lock:
            self.requests.append(SeenRequest(path, body, api_key))
            refused = sorted(p for p in self.reject_params if p in body)
        behaviour = None
        if not refused and self._responder is not None:
            behaviour = self._responder(copy.deepcopy(body))     # outside the lock: it may take a moment
        if not refused and behaviour is None:
            with self._lock:
                behaviour = self._script.pop(0) if self._script else None
                if behaviour is None:
                    self.unscripted.append(SeenRequest(path, body, api_key))
        if refused:
            return self._error(Failure(400, f"Unsupported parameter: '{refused[0]}'",
                                       "invalid_request_error", refused[0], "unsupported_parameter"))
        if behaviour is None:
            return self._error(Failure(500, "The fake OpenAI had no scripted answer for this request"))
        if behaviour.delay_s:
            time.sleep(behaviour.delay_s)
        if isinstance(behaviour, Failure):
            return self._error(behaviour)
        return self._completion(behaviour, body)

    @staticmethod
    def _error(failure: Failure):
        headers = {"retry-after-ms": "1"} if failure.status == 429 or failure.status >= 500 else {}
        return failure.status, {"error": {"message": failure.message, "type": failure.error_type,
                                          "param": failure.param, "code": failure.code}}, headers

    @staticmethod
    def _completion(reply: Reply, body: dict):
        content = reply.content if isinstance(reply.content, str) else json.dumps(reply.content)
        return 200, {
            "id": "chatcmpl-fake", "object": "chat.completion", "created": 1_700_000_000,
            "model": reply.model or body.get("model", ""),
            "choices": [{"index": 0, "finish_reason": reply.finish_reason,
                         "message": {"role": "assistant", "content": content, "refusal": None}}],
            "usage": {"prompt_tokens": reply.tokens_in, "completion_tokens": reply.tokens_out,
                      "total_tokens": reply.tokens_in + reply.tokens_out},
        }, {}
