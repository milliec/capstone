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

The verifier's flag is sent as TWO shapes (spike fix, 2026-11-22). Strict mode requires every
property on every object, so a single flag shape with five optional keys makes the model write all
five, and nothing in a JSON schema can say "an internal flag has no `other_quote`". The first real
verifier call (`gpt-5.6-terra`) caught the planted conflict but filled `field` and `row_value` on a
cross-source flag, and our check (rightly) refused it. Now the schema lists an internal flag
(`field`, `row_value`, `quote_says`, all strings) and a cross-source flag (`other_paragraph_id`,
`other_quote`, both strings) as separate shapes, each with exactly its own keys, so the model cannot
mix them. Our Pydantic check is unchanged and still runs on every answer.

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


# Which keys belong to which kind of flag (backend/domain/schemas.py, `Flag`): the same split its own
# validator enforces.
_INTERNAL_ONLY = ("field", "row_value", "quote_says")
_CROSS_SOURCE_ONLY = ("other_paragraph_id", "other_quote")
_FLAG_REF = {"$ref": "#/$defs/Flag"}


def _without_null(prop: dict) -> dict:
    """`{"anyOf": [X, {"type": "null"}]}` (how an optional field is written) becomes X."""
    options = [o for o in prop.get("anyOf", []) if o != {"type": "null"}]
    return options[0] if prop.get("anyOf") and len(options) == 1 else prop


def _flag_shapes(flag: dict) -> dict:
    """The two shapes of a flag, built from the strict schema of `Flag` itself so that its value sets
    (for example the three row fields) cannot drift from the validator's."""
    props = flag["properties"]

    def shape(kind: str, own_keys: tuple) -> dict:
        properties = {"flag_type": {"type": "string", "enum": [kind]},
                      "explanation": props["explanation"],
                      **{key: _without_null(props[key]) for key in own_keys}}
        return {"type": "object", "properties": properties, "required": list(properties),
                "additionalProperties": False}
    return {"InternalFlag": shape("internal", _INTERNAL_ONLY),
            "CrossSourceFlag": shape("cross_source", _CROSS_SOURCE_ONLY)}


def _use_the_two_flag_shapes(schema: dict) -> None:
    """In place: replace the one `Flag` definition with its two shapes, and every use of it with
    "either shape". Only the verifier's result has a `Flag`; the other steps are left untouched."""
    defs = schema.get("$defs", {})
    if "Flag" not in defs:
        return
    defs.update(_flag_shapes(defs.pop("Flag")))
    either = {"anyOf": [{"$ref": "#/$defs/InternalFlag"}, {"$ref": "#/$defs/CrossSourceFlag"}]}

    def replace(node):
        if isinstance(node, dict):
            return either if node == _FLAG_REF else {k: replace(v) for k, v in node.items()}
        if isinstance(node, list):
            return [replace(item) for item in node]
        return node
    for key in [k for k in schema if k != "$defs"]:
        schema[key] = replace(schema[key])
    schema["$defs"] = {name: replace(sub) for name, sub in defs.items()}


def wire_schema(model: type[BaseModel]) -> dict:
    """The `response_format` value for one step's result class."""
    # Imported late: only a real call needs it. Private path, pinned with crewai's openai; a test
    # fails if a CrewAI upgrade moves it.
    from openai.lib._pydantic import to_strict_json_schema
    schema = _clean(to_strict_json_schema(model))
    _use_the_two_flag_shapes(schema)
    return {"type": "json_schema",
            "json_schema": {"name": _snake(model.__name__), "strict": True, "schema": schema}}
