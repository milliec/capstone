"""Row decisions (G1) and verdict decisions (G2), once each (CR-009), and the G1/G2 page data.

All STUBS. A stub decision is written to the audit log only (the stand-in rows are not stored
until B3, so row_decisions and verdict_decisions stay empty). NO check: no decide-once
(ALREADY_DECIDED), VERSION_MISMATCH, REASON_REQUIRED, QUOTE_CHECK_FAILED, WHO_FILES_REQUIRED,
BUSINESS_DAY_RULE_REQUIRED or DEMO_ROW_NOT_APPROVABLE. B2 (and B7 for the demo row) adds them.
"""

import json
import sqlite3

from backend.domain.ids import run_id_from_child
from backend.services import FUND_ID, runs
from backend.services.audit import write_audit
from backend.stand_in import shell_data

# The stub keeps an approve's details (weekend rule, who files) in its audit text, after this
# marker, so the page can show the "decided" line. B2 stores them in row_decisions instead.
DETAILS_MARK = " | stub details: "

# H-036 V-8 `filing_parties`: [value, label] in the fund's order, "not known" last (DL-39, CR-007).
# STUB: fixed list; the real one is built from the fund configuration.
FILING_PARTIES = [["AIFM", "AIFM"], ["Fund administrator", "Fund administrator"],
                  ["Auditor", "Auditor"],
                  ["Local reporting agent (Spain)", "Local reporting agent (Spain)"],
                  ["Tax advisor", "Tax advisor"], ["not known", "Not known"]]

# Words for a row's decision (ux.md page 4) and the tone of each (ux.md §1.5).
ROW_STATUS = {"approve": ("Approved", "success"), "reject": ("Rejected", "problem")}


def _stub_decisions(conn: sqlite3.Connection, run_id: str) -> dict[str, str]:
    """subject_id → the latest stub decision text, read back from the audit log."""
    rows = conn.execute(
        "SELECT subject_id, reason FROM audit_log WHERE run_id = ? AND event_type = 'decision' "
        "ORDER BY audit_id", (run_id,))
    return {r["subject_id"]: r["reason"] for r in rows}


def _stub_records(conn: sqlite3.Connection, run_id: str) -> dict[str, dict]:
    """subject_id → who decided, when, and what, read back from the stub's audit entries."""
    rows = conn.execute(
        "SELECT subject_id, actor, at, reason FROM audit_log "
        "WHERE run_id = ? AND event_type = 'decision' ORDER BY audit_id", (run_id,))
    return {r["subject_id"]: dict(r) for r in rows}


def _decided_line(record: dict) -> dict:
    """H-036 V-8 `decided`: {by_label, at, business_day_rule, who_files, reason}."""
    text, _, details = record["reason"].partition(DETAILS_MARK)
    details = json.loads(details) if details else {}
    reason = text.partition(": ")[2] or None      # text is "approve (stub, not stored): <reason>"
    return {"by_label": runs.actor_label(record["actor"]), "at": record["at"],
            "business_day_rule": details.get("business_day_rule"),
            "who_files": details.get("who_files"), "reason": reason}


def get_g1_view(conn: sqlite3.Connection, run: dict) -> dict:
    """STUB — replace in B2/B3. The rows to check at G1 (placeholder data).

    H-036 V-8: the fields the page reads, so it works nothing out. In stand-in mode every quote
    check passes and there are no checker flags (B3 adds the real ones).
    """
    source = list(shell_data.ROWS) + ([shell_data.DEMO_ROW] if run["demo_planted_row"] else [])
    decided = _stub_decisions(conn, run["run_id"])
    records = _stub_records(conn, run["run_id"])
    rows = []
    for r in source:
        row_id = f"ROW-{run['run_id']}-{r['n']}"
        decision = decided.get(row_id)
        word = next((w for key, w in ROW_STATUS.items() if decision and decision.startswith(key)),
                    None)
        status, tone = word or ("To decide", "action")
        rows.append({
            **r, "row_id": row_id, "version": 1, "decision": decision,
            "status": status, "status_tone": tone,
            "quote_check": {"passed": True},
            "paragraph": {"document": f"Stand-in source document {r['n']}",
                          "text": f"Placeholder paragraph text for {r['source_paragraph_id']}."},
            "flags": [], "has_flag": False,
            "needs_who_files": r["responsible_role"] == "not stated in source",
            "filing_parties": FILING_PARTIES,
            "open_question": False,
            "needs_attention": ["Demo"] if r["origin"] == "demo" else [],
            "tags": [],
            "recipient_name": "Stand-in regulator" if r["recipient_code"] == "STUB-REG"
                              else r["recipient_code"],
            "decided": _decided_line(records[row_id]) if word else None,
        })
    return {
        "rows": rows,
        "stage": runs.page_stage(run, "g1"),
        "summary": {"flags": sum(1 for r in rows if r["has_flag"])},
        "unused_paragraphs": [
            {"paragraph_id": f"SRC-STUB-P{n}", "document": f"Stand-in source document {n}",
             "text": f"Placeholder paragraph text for SRC-STUB-P{n}."} for n in (5, 6)],
    }


def get_g2_view(conn: sqlite3.Connection, run: dict) -> dict:
    """STUB — replace in B2/B3. The verdicts to confirm at G2 (placeholder data)."""
    decided = _stub_decisions(conn, run["run_id"])
    names = {r["n"]: r["obligation_name"] for r in shell_data.ROWS}
    verdicts = []
    for v in shell_data.VERDICTS:
        verdict_id = f"VER-{run['run_id']}-{v['n']}"
        verdicts.append({**v, "verdict_id": verdict_id, "version": 1,
                         "row_id": f"ROW-{run['run_id']}-{v['n']}",
                         "obligation_name": names[v["n"]], "decision": decided.get(verdict_id)})
    return {"verdicts": verdicts}


def decide_row(conn: sqlite3.Connection, *, row_id: str, version: int, decision: str,
               business_day_rule: str | None, who_files: str | None,
               approve_reason: str | None, reject_reason: str | None, actor: str) -> str:
    """STUB — replace in B2. Approve or reject one row at G1. Returns the row's run ID.

    B2 writes one row_decisions line (on approve: business_day_rule, who_files, approve_reason;
    on reject: only reject_reason, DL-48) and every check listed at the top of this file.
    """
    run_id = run_id_from_child(row_id)
    reason = approve_reason if decision == "approve" else reject_reason
    text = f"{decision} (stub, not stored): {reason or ''}".strip()
    if decision == "approve":   # kept for the "decided" line, see DETAILS_MARK
        text += DETAILS_MARK + json.dumps({"business_day_rule": business_day_rule,
                                           "who_files": who_files})
    write_audit(conn, fund_id=FUND_ID, actor=actor, event_type="decision", run_id=run_id,
                subject_id=row_id, subject_version=version, reason=text)
    conn.commit()
    return run_id


def decide_verdict(conn: sqlite3.Connection, *, verdict_id: str, version: int, decision: str,
                   value: str | None, confirm_reason: str | None, override_reason: str | None,
                   decide_reason: str | None, actor: str) -> str:
    """STUB — replace in B2. Confirm, override or decide one verdict at G2. Returns the run ID.

    Each answer has its own reason field; only the chosen answer's field is read (DL-48).
    B2 writes one verdict_decisions line and adds the checks.
    """
    reason = {"confirm": confirm_reason, "override": override_reason,
              "decide": decide_reason}.get(decision)
    run_id = run_id_from_child(verdict_id)
    write_audit(conn, fund_id=FUND_ID, actor=actor, event_type="decision", run_id=run_id,
                subject_id=verdict_id, subject_version=version,
                reason=f"{decision} {value or ''} (stub, not stored): {reason or ''}".strip())
    conn.commit()
    return run_id
