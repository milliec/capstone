"""T-WIRE-1 (Tier 1): the verifier's flag is sent as TWO shapes (spike fix, 2026-11-22).
Fake OpenAI only: no real key, no real model, no paid call.

The first real verifier call (`gpt-5.6-terra`, SRC-UCILAW-P3#1) caught the planted conflict C-1 but
wrote `field` and `row_value` on a cross-source flag, and our validator refused the answer. Strict
mode makes every key on an object required, so with ONE flag shape the model had to fill five
optional keys and nothing in the schema said which. Now an internal flag and a cross-source flag are
separate shapes with exactly their own keys, so the model cannot mix them.

What these tests protect:
  * the shapes: exactly the keys the validator expects, none nullable, `flags` takes either;
  * the wire schema and the validator AGREE, checked with a real JSON-Schema checker: whatever the
    schema allows, the validator accepts, and the mixed flag of the first real call is refused by both;
  * the validator is UNCHANGED: a mixed flag that got through anyway is still refused and recorded;
  * the other two steps' schemas do not change;
  * the request a verifier call sends carries the two shapes.
They cannot prove OpenAI accepts a nested `anyOf` in strict mode. Only a real call shows that, and a
400 there is free (a refused request costs 0) and fires the spike's stop rule.
"""

import json

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from backend.domain.schemas import ExtractionResult, Verdict, VerificationResult
from backend.runtime import agents, crews, spike
from backend.runtime.wire_schema import wire_schema
from tests.fake_openai import TEST_API_KEY, Reply
from tests.tier1.test_one_request import CHAT

SCHEMA = wire_schema(VerificationResult)["json_schema"]["schema"]
INTERNAL_KEYS = {"flag_type", "explanation", "field", "row_value", "quote_says"}
CROSS_KEYS = {"flag_type", "explanation", "other_paragraph_id", "other_quote"}

# The answer the first real verifier call returned, exactly as the trace stored it (trace line 4).
FIRST_REAL_ANSWER = (
    '{"flags":[{"flag_type":"cross_source","explanation":"SRC-PRACT-P1 states that the audited '
    'annual report must be published within four months of financial year-end, while the row states '
    'a six-month offset.","field":"offset","row_value":"6 months","quote_says":null,'
    '"other_paragraph_id":"SRC-PRACT-P1","other_quote":"Funds must publish their audited annual '
    'report within four months of financial year-end."}]}')

CROSS = {"flag_type": "cross_source", "explanation": "A different offset.",
         "other_paragraph_id": "SRC-PRACT-P1", "other_quote": "within four months"}
INTERNAL = {"flag_type": "internal", "explanation": "The offset disagrees.", "field": "offset",
            "row_value": "6 months", "quote_says": "within five months"}


def wire_accepts(answer) -> bool:
    return Draft202012Validator(SCHEMA).is_valid(answer)


def validator_accepts_shape(answer) -> bool:
    """Pydantic's shape check only (the quote evidence checks are the guardrail's, tested elsewhere)."""
    try:
        VerificationResult.model_validate(answer)
    except ValidationError:
        return False
    return True


# --- The shapes ---------------------------------------------------------------------------------

def test_there_are_two_flag_shapes_and_no_single_flag_any_more():
    assert set(SCHEMA["$defs"]) == {"InternalFlag", "CrossSourceFlag"}
    assert SCHEMA["properties"]["flags"]["items"] == {"anyOf": [
        {"$ref": "#/$defs/InternalFlag"}, {"$ref": "#/$defs/CrossSourceFlag"}]}


@pytest.mark.parametrize("name,keys,kind", [("InternalFlag", INTERNAL_KEYS, "internal"),
                                            ("CrossSourceFlag", CROSS_KEYS, "cross_source")])
def test_each_shape_has_exactly_its_own_keys_all_required_and_nothing_nullable(name, keys, kind):
    shape = SCHEMA["$defs"][name]
    assert set(shape["properties"]) == keys and sorted(shape["required"]) == sorted(keys)
    assert shape["additionalProperties"] is False
    assert shape["properties"]["flag_type"] == {"type": "string", "enum": [kind]}
    assert "null" not in json.dumps(shape)                      # no key is "this type or null"


def test_the_internal_shape_keeps_the_three_row_fields_from_the_validators_own_class():
    assert SCHEMA["$defs"]["InternalFlag"]["properties"]["field"]["enum"] == [
        "frequency", "anchor", "offset"]


def test_every_reference_resolves():
    text = json.dumps(SCHEMA)
    for name in ("InternalFlag", "CrossSourceFlag"):
        assert f'"#/$defs/{name}"' in text and name in SCHEMA["$defs"]
    assert '"#/$defs/Flag"' not in text


def test_the_other_two_steps_schemas_have_no_flag_shapes():
    for model in (ExtractionResult, Verdict):
        text = json.dumps(wire_schema(model))
        assert "InternalFlag" not in text and "CrossSourceFlag" not in text


# --- The schema and the validator agree --------------------------------------------------------

def test_an_empty_list_and_a_flag_of_either_shape_are_accepted_by_both():
    for answer in ({"flags": []}, {"flags": [CROSS]}, {"flags": [INTERNAL]},
                   {"flags": [CROSS, INTERNAL]}):
        assert wire_accepts(answer) and validator_accepts_shape(answer), answer


def test_the_mixed_flag_of_the_first_real_call_is_refused_by_the_schema_and_by_the_validator():
    mixed = json.loads(FIRST_REAL_ANSWER)
    assert not wire_accepts(mixed)                  # a model held to this schema cannot send it now
    assert not validator_accepts_shape(mixed)       # and if one still did, we still refuse it


@pytest.mark.parametrize("flag", [
    {**CROSS, "field": "offset"},                           # a cross-source flag with an internal key
    {**CROSS, "field": "offset", "row_value": "6 months"},
    {**INTERNAL, "other_quote": "within four months"},      # an internal flag with a cross-source key
    {k: v for k, v in INTERNAL.items() if k != "quote_says"},      # an internal flag missing a key
    {k: v for k, v in CROSS.items() if k != "other_quote"},        # a cross-source flag missing one
    {**CROSS, "flag_type": "something_else"},
    {**INTERNAL, "field": "recipient"},                     # not one of the three row fields
    {**CROSS, "field": None, "row_value": None, "quote_says": None},    # the old all-keys shape
])
def test_whatever_the_schema_refuses_the_validator_never_has_to_accept(flag):
    """The safe direction: if the wire schema allowed it, the validator accepts it. Here the schema
    refuses every one of these. (The last one the validator still tolerates, since null means 'not
    given'; the schema is deliberately stricter than the validator, never looser.)"""
    answer = {"flags": [flag]}
    assert not wire_accepts(answer)


def test_nothing_the_schema_allows_is_something_the_validator_refuses():
    candidates = [CROSS, INTERNAL, {**CROSS, "field": "offset"}, {**INTERNAL, "other_quote": "x"},
                  {k: v for k, v in CROSS.items() if k != "other_quote"}]
    for flag in candidates:
        answer = {"flags": [flag]}
        if wire_accepts(answer):
            assert validator_accepts_shape(answer), flag


def test_every_flag_in_our_own_stand_in_answers_passes_the_wire_schema():
    """The answer key's flags are what a good answer looks like; the schema must accept them."""
    seen = 0
    for flags in agents._stand_in("verifier").values():
        for flag in flags:
            assert wire_accepts({"flags": [flag]}), flag
            seen += 1
    assert seen >= 1


# --- Through a verifier call, against the fake --------------------------------------------------

ENV = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
       "LLM_MODEL_VERIFY": "gpt-6-test-v"}


@pytest.fixture(autouse=True)
def aimed_at_the_fake_as_openai(as_openai, monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)
    return as_openai


def run_verify(db, typed="verify SRC-UCILAW-P3"):
    printed: list[str] = []
    code = spike.main(["--step", "verify", "--go"], env=ENV, spike_db=db, out=printed.append,
                      read_line=lambda prompt: typed)
    return code, "\n".join(printed)


def test_the_request_a_verifier_call_sends_carries_the_two_shapes(fake_openai, tmp_path):
    fake_openai.script(Reply({"flags": [agents._stand_in("verifier")["SRC-UCILAW-P3"][0]]}))
    code, text = run_verify(tmp_path / "spike.db")
    assert code == 0 and "Planted C-1   : CAUGHT" in text
    (request,) = fake_openai.requests
    assert request.path == CHAT
    sent = request.body["response_format"]
    assert sent["type"] == "json_schema" and sent["json_schema"]["strict"] is True
    assert sent["json_schema"]["schema"] == SCHEMA          # exactly the schema the tests above checked


def test_a_mixed_flag_that_got_through_anyway_is_still_refused_and_recorded(fake_openai, tmp_path):
    """Defence in depth: the validator did not change. If a model (or a provider) ever sends the
    first real call's answer again, the unit still fails as invalid output, with the reason, billed."""
    fake_openai.script(Reply(json.loads(FIRST_REAL_ANSWER)))
    db = tmp_path / "spike.db"
    code, text = run_verify(db)
    assert code == 1 and "NOT USABLE - invalid output" in text
    assert "a cross_source flag needs other_paragraph_id and other_quote" in text
    assert len(fake_openai.requests) == 1                    # not asked again (D5)
