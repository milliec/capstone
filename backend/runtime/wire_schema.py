"""The strict `response_format` each step sends to OpenAI (B3 step 7b, PR 4; H-065).

H-065 settled that a step's schema goes to the provider as a STRICT `response_format`, and that our
own code then checks the answer with the same Pydantic classes (backend/domain/schemas.py). This
file turns a Pydantic class into the JSON schema OpenAI's strict mode accepts. Plain code: no
CrewAI, no network, no model call.

How: the `openai` library's own helper makes every property required, forbids extra properties
and writes an optional field as "this type or null". Strict mode then does not accept a few
keywords, so those are dropped here: `minLength` and `maxLength`, `discriminator`, and `oneOf`
(rewritten as the `anyOf` it means). Dropping them loses nothing: our Pydantic check runs on every
answer and enforces them (a model that sends an empty explanation is refused there).

Why not CrewAI's own `response_format=<class>`: its schema builder removes `null` from every type,
so an optional field such as the verifier's `field` could never be null, and the model would have
to invent a value for it.

Known limit: this was written against OpenAI's documented strict-mode rules and tested against the
fake server. Whether the provider accepts it is shown only by the first real call (the spike): a
400 "invalid schema" there means this file needs one more keyword dropped.
"""

import re

from pydantic import BaseModel

# Keywords strict mode does not accept. Dropped; the Pydantic check enforces them instead.
_DROPPED = {"minLength", "maxLength", "discriminator", "title", "default"}


def _clean(node):
    """Drop the unsupported keywords everywhere in the schema, and turn `oneOf` into `anyOf`."""
    if isinstance(node, dict):
        cleaned = {("anyOf" if k == "oneOf" else k): _clean(v)
                   for k, v in node.items() if k not in _DROPPED}
        # A property NAMED "title" or "default" is a field, not a keyword: keep it.
        if isinstance(node.get("properties"), dict):
            cleaned["properties"] = {name: _clean(sub) for name, sub in node["properties"].items()}
        return cleaned
    if isinstance(node, list):
        return [_clean(item) for item in node]
    return node


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def wire_schema(model: type[BaseModel]) -> dict:
    """The `response_format` value for one step's result class."""
    # Imported late: only a real call needs it. Private path, pinned with crewai's openai; a test
    # fails if a CrewAI upgrade moves it.
    from openai.lib._pydantic import to_strict_json_schema
    return {"type": "json_schema",
            "json_schema": {"name": _snake(model.__name__), "strict": True,
                            "schema": _clean(to_strict_json_schema(model))}}
