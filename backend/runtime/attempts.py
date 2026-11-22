"""What one model call did on the wire: one `HttpAttempt` per HTTP request (B3 step 7b, PR 5).

CrewAI's `interceptor` hook (backend/runtime/crews.py) hands every request and every response to an
`AttemptLog`. The log is plain Python and never imports CrewAI. It is how the trace gets what the
provider really said, request by request, instead of CrewAI's own summary:

  * the model string the API returned (`model_returned`, DL-40) and its stop reason,
  * the token counts of THAT request (the usage data the cost cap counts, CR-017),
  * what the request actually carried (so a repeat without `reasoning_effort` shows),
  * and, for a request that got no answer (a timeout, no connection, a 500), why not.

Three kinds of attempt, because the cost cap needs to know which can have cost money:

  answered   a 200 with usage data            cost from the usage data
  rejected   a 4xx (a 429, 400, 401, 404...)  the provider refused before doing any work: cost 0
  unknown    a 5xx, a timeout, no connection  no usage data and the provider may have done the work:
                                              the worst case is charged and marked as an estimate
  refused    not a chat completion            BLOCKED before it was sent (spike fix, step D): cost 0

Only `POST .../chat/completions` is ever allowed out. The first real spike call sent CrewAI's own
pre-flight (`POST /v1/responses/input_tokens`) that no test had seen, because a fake server on this
machine never triggers it. Now any other request is refused before it leaves, and says so in the trace.
"""

import json
import threading
import time
from dataclasses import dataclass, field

from backend.services.audit import now_utc

# The settings a trace line reports for a request, when the request carried them (CR-018).
LOGGED_SETTINGS = ("max_completion_tokens", "reasoning_effort", "temperature")

ERROR_TEXT_LIMIT = 300         # a provider's error message can be long; the trace keeps the start


class RequestRefused(Exception):
    """A request that is not a chat completion was about to be sent, and was stopped (step D). Raised
    by the interceptor BEFORE the request leaves the machine, so nothing was sent and nothing costs."""


CHAT_COMPLETIONS = "/chat/completions"


def is_chat_completion(method: str, path: str) -> bool:
    """The one kind of request a unit may send: `POST <anything>/chat/completions` (the prefix is
    `/v1` for OpenAI itself and can differ behind a proxy). A GET, another endpoint, or a path that
    only STARTS with it (`.../chat/completions/extra`) is not."""
    return method.upper() == "POST" and path.rstrip("/").endswith(CHAT_COMPLETIONS)


@dataclass
class HttpAttempt:
    """One HTTP request to the provider, and what came back (nothing, until it is finished)."""
    n: int                              # 1, 2, 3... in the order sent, for the whole call
    at: str                             # when it was sent, ISO 8601 UTC
    started: float                      # time.monotonic() when it was sent
    request_bytes: int                  # size of the request body (for an estimate of its input)
    method: str = ""                    # POST, GET ...
    path: str = ""                      # the URL path, for example /v1/chat/completions (step D)
    refused: bool = False               # True: stopped before it was sent (step D); never reached the provider
    sent_model: str = ""
    sent_settings: dict = field(default_factory=dict)       # the LOGGED_SETTINGS the request carried
    sent_keys: frozenset = frozenset()  # every top-level key of the request body
    status_code: int | None = None      # None: no response came (timeout, no connection)
    model_returned: str = ""
    stop_reason: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    usage_known: bool = False
    text: str | None = None             # the answer's text, for a 200
    error: str | None = None            # why there is no answer, for everything but a 200
    duration_ms: int = 0
    finished: bool = False

    @property
    def answered(self) -> bool:
        return self.status_code == 200 and self.error is None

    @property
    def kind(self) -> str:
        """answered, rejected, unknown or refused: see the module docstring."""
        if self.refused:
            return "refused"
        if self.answered and self.usage_known:
            return "answered"
        if self.status_code is not None and 400 <= self.status_code < 500:
            return "rejected"
        return "unknown"


class AttemptLog:
    """Every HTTP request of one call (the DL-43 retry included), in order. One log per call, so
    two units running side by side never share one."""

    def __init__(self):
        self.attempts: list[HttpAttempt] = []
        self._lock = threading.Lock()

    # --- Called from the interceptor, once per request ----------------------------------------

    def begin(self, body: bytes, *, method: str = "POST", path: str = "") -> HttpAttempt:
        """A request is about to be sent. `method` and `path` say WHICH request (step D)."""
        try:
            sent = json.loads(body or b"{}")
            if not isinstance(sent, dict):
                sent = {}
        except ValueError:
            sent = {}
        with self._lock:
            attempt = HttpAttempt(
                n=len(self.attempts) + 1, at=now_utc(), started=time.monotonic(),
                request_bytes=len(body or b""), method=method, path=path,
                sent_model=str(sent.get("model", "")),
                sent_settings={k: sent[k] for k in LOGGED_SETTINGS if k in sent},
                sent_keys=frozenset(sent))
            self.attempts.append(attempt)
        return attempt

    def finish(self, status_code: int, body: bytes) -> None:
        """The response to the latest request arrived."""
        with self._lock:
            attempt = self._open()
            if attempt is None:
                return
            attempt.status_code = status_code
            _read_response(attempt, body)
            _close(attempt)

    def refuse(self, attempt: HttpAttempt) -> str:
        """Mark a request that is NOT a chat completion as stopped before it was sent. It is closed
        at once (it will get no response), and the reason is returned for the exception."""
        with self._lock:
            attempt.refused = True
            attempt.error = _short(
                f"refused before sending: {attempt.method} {attempt.path or '(no path)'} is not a "
                "chat completion; only POST .../chat/completions may be sent")
            _close(attempt)
            return attempt.error

    def fail(self, reason: str) -> None:
        """The latest request, if still open, got no response at all (a timeout, no connection):
        `reason` is the error that ended the call."""
        with self._lock:
            attempt = self._open()
            if attempt is not None:
                attempt.error = _short(reason)
                _close(attempt)

    def _open(self) -> HttpAttempt | None:
        return self.attempts[-1] if self.attempts and not self.attempts[-1].finished else None


def _close(attempt: HttpAttempt) -> None:
    attempt.duration_ms = int((time.monotonic() - attempt.started) * 1000)
    attempt.finished = True


def _short(text: str) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= ERROR_TEXT_LIMIT else text[:ERROR_TEXT_LIMIT - 1] + "…"


def _read_response(attempt: HttpAttempt, body: bytes) -> None:
    """Fill the attempt from the provider's answer. Never raises: a response we cannot read is
    recorded as such, and the call goes on exactly as it would without us."""
    try:
        data = json.loads(body or b"{}")
    except ValueError as error:
        attempt.error = _short(
            f"HTTP {attempt.status_code}: the response could not be read ({error})")
        return
    if not isinstance(data, dict):
        attempt.error = f"HTTP {attempt.status_code}: the response is not a JSON object"
        return
    if attempt.status_code != 200:
        problem = data.get("error") if isinstance(data.get("error"), dict) else {}
        kind, message = problem.get("type") or problem.get("code") or "", problem.get("message") or ""
        attempt.error = _short(f"HTTP {attempt.status_code} {kind}: {message}".replace("  ", " "))
        return
    attempt.model_returned = str(data.get("model") or "")
    choice = (data.get("choices") or [{}])[0]
    attempt.stop_reason = str(choice.get("finish_reason") or "")
    attempt.text = (choice.get("message") or {}).get("content")
    usage = data.get("usage")
    if isinstance(usage, dict) and "prompt_tokens" in usage and "completion_tokens" in usage:
        attempt.tokens_in, attempt.tokens_out = int(usage["prompt_tokens"]), int(usage["completion_tokens"])
        attempt.usage_known = True
