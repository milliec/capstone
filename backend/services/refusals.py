"""Refusal codes and their HTTP statuses (SAD §4 "Refusals").

A service refuses a request by returning a Refusal: a code (for tests and the audit log) and one
plain sentence for the person (shown on the page). Every refusal is written to the audit log.

App shell: only FORBIDDEN has its sentence (ux.md §1.7). B2 adds the other sentences from ux.md §5.
"""

from dataclasses import dataclass

HTTP_STATUS = {
    "FORBIDDEN": 403,
    "VALIDATION": 422,
    "REASON_REQUIRED": 422,
    "ALREADY_DECIDED": 409,
    "VERSION_MISMATCH": 409,
    "GATE_INCOMPLETE": 409,
    "QUOTE_CHECK_FAILED": 409,
    "WHO_FILES_REQUIRED": 422,
    "BUSINESS_DAY_RULE_REQUIRED": 422,
    "DEMO_ROW_NOT_APPROVABLE": 409,
    "ACK_REQUIRED": 409,
    "RUN_ACTIVE": 409,
    "RUN_NOT_ACTIVE": 409,
    "RUN_STAGE_RUNNING": 409,
    "RUN_NOT_FAILED": 409,
    "RETRY_LIMIT_REACHED": 409,
    "RETRY_NOT_ALLOWED": 409,
}

SENTENCES = {
    "FORBIDDEN": ("This page is for the compliance specialist. You are signed in as the General "
                  "Partner, so you can view the published calendar only."),
}


@dataclass(frozen=True)
class Refusal:
    code: str
    sentence: str

    @property
    def http_status(self) -> int:
        return HTTP_STATUS[self.code]
