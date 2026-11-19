"""Row decisions (G1) and verdict decisions (G2), once each (CR-009), and the G1/G2 page data.

B2: decisions are stored in `row_decisions` and `verdict_decisions`, which refuse a second decision
for the same row or verdict (a UNIQUE key). The views read the stored rows and verdicts that
stage A and B saved (stage_store, rule 9).

A decision is checked BEFORE anything is written, in this order (the first that applies wins):
the review has ended (RUN_NOT_ACTIVE) → it is not at this gate (RUN_STAGE_RUNNING) → the item is
already decided (ALREADY_DECIDED) → no answer chosen, or an answer the form cannot make
(VALIDATION) → the checks for the chosen answer. A refusal is audited and changes nothing.

Not here yet: DEMO_ROW_NOT_APPROVABLE and "Approval blocked" (B7, which uses the refusal object).
"""

import sqlite3

from backend.domain import sources, wording
from backend.domain.fund_facts import load_fund_facts
from backend.services import FUND_ID, guards, runs
from backend.services.audit import now_utc, write_audit
from backend.services.refusals import NotFound, refuse

# H-036 V-8 `filing_parties`: [value, label] in the fund's order, "not known" last (DL-39, CR-007).
# STUB: fixed list; the real one is built from the fund configuration.
FILING_PARTIES = [["AIFM", "AIFM"], ["Fund administrator", "Fund administrator"],
                  ["Auditor", "Auditor"],
                  ["Local reporting agent (Spain)", "Local reporting agent (Spain)"],
                  ["Tax advisor", "Tax advisor"], ["not known", "Not known"]]
BUSINESS_DAY_RULES = ("roll_forward", "roll_backward", "no_roll")   # "not_confirmed" does not count
SOURCE_SILENT = "not stated in source"

# ux.md page 5 item 8: the decided outcome in words, keyed by "<decision> <value>".
ANSWER_WORDS = {"confirm applies": "Confirmed: applies",
                "confirm does_not_apply": "Confirmed: doesn't apply",
                "override applies": "Overruled: applies",
                "override does_not_apply": "Overruled: doesn't apply",
                "decide applies": "Added, marked 'May not be required'",
                "decide does_not_apply": "Left off"}
# Override at G2 flips the verdict to its opposite; there is no third value (ux.md Assumptions).
OPPOSITE = {"applies": "does_not_apply", "does_not_apply": "applies"}

# Words for a row's decision (ux.md page 4) and the tone of each (ux.md §1.5).
ROW_STATUS = {"approve": ("Approved", "success"), "reject": ("Rejected", "problem")}


def _n(item_id: str) -> int:
    """ROW-RUN-20261117-1-3 or VER-RUN-20261117-1-3 → 3 (the number inside the run)."""
    return int(item_id.rsplit("-", 1)[1])


def _titles(conn: sqlite3.Connection, run_id: str) -> dict[str, str]:
    """Source document titles by document ID, from the regulation config (DL-53).

    Not from stage A's unit lines (as in the shell): the secondary guide is never extracted, so it
    has no unit, and its paragraphs showed the bare ID. `conn` and `run_id` stay for the callers.
    """
    return {d["id"]: d["title"] for d in sources.list_documents()}


# --- Paragraphs, rejected rules -----------------------------------------------------------

def unused_paragraphs(conn: sqlite3.Connection, run: dict) -> list[dict]:
    """Paragraphs no rule uses: no rule that is approved or still undecided cites them (W-03b).

    Shown at G1 and again at G3. A rule that is rejected stops counting as using its paragraph.
    """
    titles = _titles(conn, run["run_id"])
    rows = conn.execute(
        """SELECT p.paragraph_id, p.document_id, p.paragraph_text FROM paragraphs p
           WHERE p.run_id = ? AND NOT EXISTS (
               SELECT 1 FROM rows r LEFT JOIN row_decisions d ON d.row_id = r.row_id
               WHERE r.run_id = p.run_id AND r.source_paragraph_id = p.paragraph_id
                 AND COALESCE(d.decision, '') != 'reject')
           ORDER BY p.rowid""", (run["run_id"],))
    return [{"paragraph_id": r["paragraph_id"],
             "document": titles.get(r["document_id"], r["document_id"]),
             "text": r["paragraph_text"]} for r in rows]


def rejected_rows(conn: sqlite3.Connection, run: dict) -> list[dict]:
    """H-036 V-10 `rejected_rows`: [{row_id, label, reason, is_demo}] for rules rejected at G1."""
    rows = conn.execute(
        """SELECT r.row_id, r.obligation_name, r.origin, d.reason FROM rows r
           JOIN row_decisions d ON d.row_id = r.row_id
           WHERE r.run_id = ? AND d.decision = 'reject' ORDER BY r.rowid""", (run["run_id"],))
    return [{"row_id": r["row_id"], "label": r["obligation_name"], "reason": r["reason"],
             "is_demo": r["origin"] == "demo"} for r in rows]


# --- G1 -------------------------------------------------------------------------------------

def _flags(conn: sqlite3.Connection, row_id: str) -> list[dict]:
    rows = conn.execute("SELECT * FROM flags WHERE row_id = ? ORDER BY flag_id", (row_id,))
    return [{"flag_type": f["flag_type"], "row_value": f["row_value"] or f["explanation"],
             "quote_says": f["quote_says"] or f["other_quote"],
             "other_paragraph_id": f["other_paragraph_id"]} for f in rows]


def _decided_line(d: sqlite3.Row) -> dict:
    """H-036 V-8 `decided`: {by_label, at, business_day_rule, who_files, reason}."""
    return {"by_label": runs.actor_label(d["decided_by"]), "at": d["decided_at"],
            "business_day_rule": d["business_day_rule"], "who_files": d["who_files"],
            "reason": d["reason"]}


def get_g1_view(conn: sqlite3.Connection, run: dict) -> dict:
    """The rows to check at G1, read from what stage A stored, with the H-036 V-8 view fields.

    Since B3 step 5 the rows, quote checks and flags are stage A's real (stand-in) outputs. The
    row's codes are sent as words (backend/domain/wording.py) and the recipient's display name
    comes from the regulation config (DL-53). Before stage A has stored its rows, the list is empty.
    """
    titles = _titles(conn, run["run_id"])
    recipients = sources.list_recipients()
    # CR-027 (B4): a rule whose paragraph and recipient match an open convention says at G1 that
    # its business-day rule depends on that open question. Derived here, never stored (SOQ-33).
    open_questions = {(c["source_paragraph_id"], c["recipient_code"]): c["question_id"]
                      for c in sources.load_regulation_config()["open_conventions"]}
    records = conn.execute(
        """SELECT r.*, q.result AS quote_result, p.paragraph_text, p.document_id,
                  d.decision AS g1_decision, d.business_day_rule AS d_rule, d.who_files AS d_who,
                  d.reason AS d_reason, d.decided_by, d.decided_at
           FROM rows r JOIN quote_checks q ON q.row_id = r.row_id
           JOIN paragraphs p ON p.run_id = r.run_id AND p.paragraph_id = r.source_paragraph_id
           LEFT JOIN row_decisions d ON d.row_id = r.row_id
           WHERE r.run_id = ? ORDER BY r.rowid""", (run["run_id"],)).fetchall()
    rows = []
    for r in records:
        decision = r["g1_decision"]
        status, tone = ROW_STATUS.get(decision, ("To decide", "action"))
        flags = _flags(conn, r["row_id"])
        d = {"business_day_rule": r["d_rule"], "who_files": r["d_who"], "reason": r["d_reason"],
             "decided_by": r["decided_by"], "decided_at": r["decided_at"]}
        rows.append({
            "n": _n(r["row_id"]), "row_id": r["row_id"], "version": r["version"],
            "obligation_name": r["obligation_name"],
            "frequency": wording.FREQUENCY_WORDS.get(r["frequency"], r["frequency"]),
            "anchor": wording.ANCHOR_WORDS.get(r["anchor"], r["anchor"]),
            "offset": wording.offset_words(r["offset"]),
            "due": wording.due_words(r["offset"], r["anchor"]),   # for the calendar's "why" line
            "recipient_code": r["recipient_code"],
            "responsible_role": r["responsible_role"], "business_day_rule": r["business_day_rule"],
            "source_paragraph_id": r["source_paragraph_id"], "quote": r["quote"],
            "origin": r["origin"], "decision": decision,
            "status": status, "status_tone": tone,
            "quote_check": {"passed": r["quote_result"] == "pass"},
            "paragraph": {"document": titles.get(r["document_id"], r["document_id"]),
                          "text": r["paragraph_text"]},
            "flags": flags, "has_flag": bool(flags),
            "needs_who_files": r["responsible_role"] == SOURCE_SILENT,
            "filing_parties": FILING_PARTIES,
            "open_question": open_questions.get((r["source_paragraph_id"], r["recipient_code"]),
                                                False),
            "needs_attention": ["Demo"] if r["origin"] == "demo" else [], "tags": [],
            "recipient_name": recipients.get(r["recipient_code"], r["recipient_code"]),
            "decided": _decided_line(d) if decision else None,
        })
    return {
        "rows": rows,
        "stage": runs.page_stage(run, "g1"),
        "summary": {"flags": sum(1 for r in rows if r["has_flag"])},
        "unused_paragraphs": unused_paragraphs(conn, run),
    }


def decide_row(conn: sqlite3.Connection, *, row_id: str, version: int, decision: str,
               business_day_rule: str | None, who_files: str | None,
               approve_reason: str | None, reject_reason: str | None, actor: str) -> str:
    """Approve or reject one row at G1, once (CR-005, CR-007, CR-009). Returns the row's run ID.

    Approve needs: a quote check that passed (QUOTE_CHECK_FAILED); a business-day rule
    (BUSINESS_DAY_RULE_REQUIRED); a filing party when the source is silent and one the page offers
    (WHO_FILES_REQUIRED, VALIDATION); and a reason when the rule is flagged (REASON_REQUIRED).
    Reject needs a reason. The fields of the answer not chosen are ignored (DL-48).
    """
    row = conn.execute(
        """SELECT r.*, q.result AS quote_result FROM rows r
           JOIN quote_checks q ON q.row_id = r.row_id WHERE r.row_id = ?""", (row_id,)).fetchone()
    if row is None:
        raise NotFound(row_id)
    run = runs.get_run(conn, row["run_id"])
    n = _n(row_id)
    here = {"subject_id": row_id, "anchor": f"row-{n}", "target_label": f"rule {n}",
            "typed": {"approve_reason": approve_reason or "", "reject_reason": reject_reason or ""}}
    guards.require_active(conn, run, actor, subject_id=row_id)
    guards.require_phase(conn, run, "AT_G1", actor, subject_id=row_id)

    def refuse_here(code, context="", **values):
        refuse(conn, code, context, actor=actor, fund_id=run["fund_id"], run_id=run["run_id"],
               **here, **values)

    if conn.execute("SELECT 1 FROM row_decisions WHERE row_id = ?", (row_id,)).fetchone():
        refuse_here("ALREADY_DECIDED", "rule")
    if decision not in ("approve", "reject"):
        refuse_here("VALIDATION", "no_answer")

    reason = (approve_reason if decision == "approve" else reject_reason) or ""
    reason = reason.strip()
    if decision == "reject":
        if not reason:
            refuse_here("REASON_REQUIRED", "reject_rule")
        rule, filer = None, None
    else:
        if row["quote_result"] != "pass":
            refuse_here("QUOTE_CHECK_FAILED", para_id=row["source_paragraph_id"])
        if business_day_rule not in BUSINESS_DAY_RULES:
            refuse_here("BUSINESS_DAY_RULE_REQUIRED")
        silent = row["responsible_role"] == SOURCE_SILENT
        if silent and not (who_files or "").strip():
            refuse_here("WHO_FILES_REQUIRED")
        if silent and who_files not in [value for value, _ in FILING_PARTIES]:
            refuse_here("VALIDATION", "field", field="who files")
        if _flags(conn, row_id) and not reason:
            refuse_here("REASON_REQUIRED", "approve_flag")
        rule, filer = business_day_rule, (who_files if silent else None)

    try:
        conn.execute(
            """INSERT INTO row_decisions (row_id, fund_id, decision, business_day_rule, who_files,
                                          reason, row_version, decided_by, decided_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (row_id, run["fund_id"], decision, rule, filer, reason or None, row["version"], actor,
             now_utc()))
    except sqlite3.IntegrityError:    # a second request got in first: the table allows one decision
        conn.rollback()
        refuse_here("ALREADY_DECIDED", "rule")
    write_audit(conn, fund_id=run["fund_id"], actor=actor, event_type="decision",
                run_id=run["run_id"], subject_id=row_id, subject_version=row["version"],
                reason=f"{decision}" + (f" ({rule}; {filer})" if rule and filer else
                                        f" ({rule})" if rule else "") + (f": {reason}" if reason else ""))
    conn.commit()
    return run["run_id"]


# --- G2 -------------------------------------------------------------------------------------

def get_g2_view(conn: sqlite3.Connection, run: dict) -> dict:
    """The verdicts to confirm at G2, read from what stage B stored (H-036 V-9 view fields).

    Since B3 step 5 the verdicts are stage B's real (stand-in) outputs, and each cited fact or
    event is shown with its text and value from the fund profile (the same loader the judge reads).
    """
    known = {f["fact_id"]: (f["fact"], f["value"]) for f in load_fund_facts(run["fund_id"])["facts"]}
    known |= {e["event_id"]: (e["event"], "Recorded in the event log")
              for e in load_fund_facts(run["fund_id"])["events"]}
    records = conn.execute(
        """SELECT v.*, r.obligation_name, r.quote, r.source_paragraph_id,
                  d.decision AS g2_decision, d.final_value, d.reason AS d_reason, d.decided_by,
                  d.decided_at
           FROM verdicts v JOIN rows r ON r.row_id = v.row_id
           LEFT JOIN verdict_decisions d ON d.verdict_id = v.verdict_id
           WHERE r.run_id = ? ORDER BY v.rowid""", (run["run_id"],)).fetchall()
    verdicts = []
    for v in records:
        unsure = v["verdict"] == "unsure"
        outcome = (ANSWER_WORDS[f"{v['g2_decision']} {v['final_value']}"]
                   if v["g2_decision"] else None)
        verdicts.append({
            "n": _n(v["verdict_id"]), "verdict_id": v["verdict_id"], "version": v["version"],
            "row_id": v["row_id"], "obligation_name": v["obligation_name"],
            "verdict": v["verdict"], "reasoning": v["reasoning"],
            "cited_fact_ids": v["cited_fact_ids"], "missing_information": v["missing_information"],
            "decision": v["g2_decision"],
            "cited_facts": [{"fact_id": fid, "label": known.get(fid, (fid, ""))[0],
                             "value": known.get(fid, (fid, ""))[1]}
                            for fid in (i.strip() for i in v["cited_fact_ids"].split(","))],
            "approved_rule": {"text": v["obligation_name"], "quote": v["quote"],
                              "paragraph_id": v["source_paragraph_id"]},
            "missing_fact": v["missing_information"] if unsure else None,
            "overrule_value": None if unsure else OPPOSITE[v["verdict"]],
            "decided": ({"outcome": outcome, "by_label": runs.actor_label(v["decided_by"]),
                         "at": v["decided_at"], "reason": v["d_reason"]}
                        if v["g2_decision"] else None),
        })
    return {"verdicts": verdicts, "stage": runs.page_stage(run, "g2")}


def decide_verdict(conn: sqlite3.Connection, *, verdict_id: str, version: int, decision: str,
                   value: str | None, confirm_reason: str | None, override_reason: str | None,
                   decide_reason: str | None, actor: str) -> str:
    """Confirm, overrule or decide one verdict at G2, once (CR-009). Returns the run ID.

    The answer must fit AI's verdict: confirm repeats it, overrule gives the opposite, and decide
    is only for "AI can't tell" (otherwise VALIDATION). Overrule and decide need a written reason
    (REASON_REQUIRED); confirm needs none. Each answer has its own reason field and only the
    chosen one is read (DL-48).
    """
    v = conn.execute(
        """SELECT v.*, r.run_id FROM verdicts v JOIN rows r ON r.row_id = v.row_id
           WHERE v.verdict_id = ?""", (verdict_id,)).fetchone()
    if v is None:
        raise NotFound(verdict_id)
    run = runs.get_run(conn, v["run_id"])
    n = _n(verdict_id)
    here = {"subject_id": verdict_id, "anchor": f"verdict-{n}", "target_label": f"rule {n}",
            "typed": {"confirm_reason": confirm_reason or "", "override_reason": override_reason or "",
                      "decide_reason": decide_reason or ""}}
    guards.require_active(conn, run, actor, subject_id=verdict_id)
    guards.require_phase(conn, run, "AT_G2", actor, subject_id=verdict_id)

    def refuse_here(code, context="", **values):
        refuse(conn, code, context, actor=actor, fund_id=run["fund_id"], run_id=run["run_id"],
               **here, **values)

    if conn.execute("SELECT 1 FROM verdict_decisions WHERE verdict_id = ?", (verdict_id,)).fetchone():
        refuse_here("ALREADY_DECIDED", "answer")
    if decision not in ("confirm", "override", "decide"):
        refuse_here("VALIDATION", "no_answer")
    ai = v["verdict"]
    fits = {"confirm": ai != "unsure" and value == ai,
            "override": ai != "unsure" and value == OPPOSITE.get(ai),
            "decide": ai == "unsure" and value in OPPOSITE}[decision]
    if not fits:
        refuse_here("VALIDATION", "field", field="the answer")

    reason = {"confirm": confirm_reason, "override": override_reason,
              "decide": decide_reason}[decision]
    reason = (reason or "").strip()
    if decision != "confirm" and not reason:
        refuse_here("REASON_REQUIRED", "g2_applies" if value == "applies" else "g2_does_not_apply")

    try:
        conn.execute(
            """INSERT INTO verdict_decisions (verdict_id, fund_id, decision, final_value, reason,
                                              verdict_version, decided_by, decided_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (verdict_id, run["fund_id"], decision, value, reason or None, v["version"], actor,
             now_utc()))
    except sqlite3.IntegrityError:
        conn.rollback()
        refuse_here("ALREADY_DECIDED", "answer")
    write_audit(conn, fund_id=run["fund_id"], actor=actor, event_type="decision",
                run_id=run["run_id"], subject_id=verdict_id, subject_version=v["version"],
                reason=f"{decision} {value}" + (f": {reason}" if reason else ""))
    conn.commit()
    return run["run_id"]


# --- Counting what is left, for finishing a gate ---------------------------------------------

def count_undecided(conn: sqlite3.Connection, run_id: str, gate: str) -> tuple[int, int]:
    """(undecided, of which 'AI can't tell') at G1 or G2. The second number is 0 at G1."""
    if gate == "G1":
        (x,) = conn.execute(
            """SELECT COUNT(*) FROM rows r LEFT JOIN row_decisions d ON d.row_id = r.row_id
               WHERE r.run_id = ? AND d.row_id IS NULL""", (run_id,)).fetchone()
        return x, 0
    row = conn.execute(
        """SELECT COUNT(*), COALESCE(SUM(v.verdict = 'unsure'), 0) FROM verdicts v
           JOIN rows r ON r.row_id = v.row_id
           LEFT JOIN verdict_decisions d ON d.verdict_id = v.verdict_id
           WHERE r.run_id = ? AND d.verdict_id IS NULL""", (run_id,)).fetchone()
    return row[0], row[1]
