"""The strict `response_format` each step sends (B3 step 7b, PR 4; backend/runtime/wire_schema.py).

OpenAI's strict mode has rules: every object forbids extra properties and lists every property as
required, optional fields are written "this type or null", and a few keywords are not accepted.
These tests check the rules on all three result classes. They cannot prove the provider accepts
the schema (only a real call can: the spike); they stop a change from breaking the rules we know.
"""

import pytest

from backend.domain.schemas import ExtractionResult, Verdict, VerificationResult
from backend.runtime.wire_schema import wire_schema

CLASSES = [ExtractionResult, VerificationResult, Verdict]
NOT_ACCEPTED = {"minLength", "maxLength", "discriminator", "oneOf", "default", "title"}


def _walk(node, path="schema"):
    """Every dict in the schema, with where it is."""
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            yield from _walk(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{path}[{i}]")


def _keywords(schema):
    """Every schema keyword used, ignoring the NAMES of properties and definitions."""
    for _, node in _walk(schema):
        for key in node:
            if key not in ("properties", "$defs"):
                yield key


@pytest.mark.parametrize("model", CLASSES)
def test_the_envelope_is_a_strict_json_schema(model):
    wire = wire_schema(model)
    assert wire["type"] == "json_schema" and wire["json_schema"]["strict"] is True
    assert wire["json_schema"]["name"].replace("_", "") == model.__name__.lower()


@pytest.mark.parametrize("model", CLASSES)
def test_every_object_forbids_extras_and_requires_every_property(model):
    for where, node in _walk(wire_schema(model)["json_schema"]["schema"]):
        if node.get("type") == "object":
            assert node["additionalProperties"] is False, where
            assert sorted(node["required"]) == sorted(node["properties"]), where


@pytest.mark.parametrize("model", CLASSES)
def test_no_keyword_strict_mode_does_not_accept_is_left(model):
    assert not NOT_ACCEPTED & set(_keywords(wire_schema(model)["json_schema"]["schema"]))


def test_an_optional_field_can_still_be_null():
    """The verifier's `field` is only for internal flags. CrewAI's own builder would remove `null`
    from it and force the model to invent a value; ours keeps it."""
    flag = wire_schema(VerificationResult)["json_schema"]["schema"]["$defs"]["Flag"]
    for name in ("field", "row_value", "quote_says", "other_paragraph_id", "other_quote"):
        assert {"type": "null"} in flag["properties"][name]["anyOf"], name


def test_the_offsets_two_shapes_survive_as_an_anyof():
    """The row's offset is a period or a fixed day and month: two shapes, now an `anyOf`."""
    schema = wire_schema(ExtractionResult)["json_schema"]["schema"]
    row = schema["$defs"]["Row"]["properties"]["offset"]
    assert len(row["anyOf"]) == 2


def test_a_field_named_like_a_dropped_keyword_is_kept():
    """`title` and `default` are dropped as KEYWORDS, but a property with that name is a field."""
    from pydantic import BaseModel

    class Tricky(BaseModel):
        title: str
        default: int

    props = wire_schema(Tricky)["json_schema"]["schema"]["properties"]
    assert set(props) == {"title", "default"}


def test_the_value_sets_are_kept():
    schema = wire_schema(Verdict)["json_schema"]["schema"]
    assert schema["properties"]["verdict"]["enum"] == ["applies", "does_not_apply", "unsure"]
