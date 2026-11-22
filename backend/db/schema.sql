-- SQLite schema, transcribed from sad.md §4 "Data" and "Data model: the happy path" (DL-50, DL-53).
-- It adds no table and no content the SAD does not name.
--
-- Rules carried over from the SAD:
--   * Every business table carries fund_id, and the main foreign keys include it, so a row
--     cannot point at another fund's run.
--   * SQLite has no enum: an enum is a TEXT column with a CHECK on its allowed values.
--   * Decision tables allow one decision per row / verdict (UNIQUE, CR-009).
--   * audit_log and trace are append-only: triggers refuse UPDATE and DELETE (CR-013).
--
-- `trace` came with B3 step 6, with the columns in sad.md §4 "The `trace` columns" (H-035).
-- Every statement uses IF NOT EXISTS, so applying the file twice is harmless.

-- The fund is a config file (config/fund/FND-DEMO-01.yaml), not a table (DL-50 item 1).

CREATE TABLE IF NOT EXISTS runs (
    run_id            TEXT PRIMARY KEY,                -- RUN-yyyymmdd-n
    fund_id           TEXT NOT NULL,
    status            TEXT NOT NULL CHECK (status IN
                        ('ACTIVE', 'FAILED', 'ABANDONED', 'DECLINED', 'COMPLETED')),
    phase             TEXT NOT NULL CHECK (phase IN
                        ('A_RUNNING', 'AT_G1', 'B_RUNNING', 'AT_G2', 'C_RUNNING', 'AT_G3')),
    run_version       INTEGER NOT NULL DEFAULT 1,      -- goes up at every gate event
    demo_planted_row  INTEGER NOT NULL DEFAULT 0 CHECK (demo_planted_row IN (0, 1)),
    agents_mode       TEXT NOT NULL CHECK (agents_mode IN ('stand_in', 'real')),
    cost_so_far       REAL NOT NULL DEFAULT 0,
    started_by        TEXT NOT NULL,                   -- DL-53
    started_at        TEXT NOT NULL,                   -- DL-53, ISO 8601 UTC
    demo_fail_step1   INTEGER NOT NULL DEFAULT 0 CHECK (demo_fail_step1 IN (0, 1)),  -- DL-52
    stage_attempt     INTEGER NOT NULL DEFAULT 1 CHECK (stage_attempt IN (1, 2)),    -- DL-51
    spend_activity    TEXT,                            -- DL-51, real mode only
    UNIQUE (run_id, fund_id)                           -- lets other tables point at (run, fund)
);

CREATE TABLE IF NOT EXISTS units (
    run_id          TEXT NOT NULL,
    stage           TEXT NOT NULL CHECK (stage IN ('A', 'B', 'C')),
    stage_attempt   INTEGER NOT NULL CHECK (stage_attempt IN (1, 2)),
    unit_id         TEXT NOT NULL,                     -- a document ID, a row ID or the calendar
    fund_id         TEXT NOT NULL,
    label           TEXT NOT NULL,                     -- DL-53, document title or obligation name
    status          TEXT NOT NULL CHECK (status IN ('waiting', 'running', 'done', 'failed')),
    attempts        INTEGER NOT NULL DEFAULT 0,        -- call attempts, 1 or 2
    failure_reason  TEXT CHECK (failure_reason IS NULL OR failure_reason IN (
                        'model service', 'stage time limit', 'invalid output', 'cost cap',
                        'service restarted', 'calendar generation', 'demo failure')),
    PRIMARY KEY (run_id, stage, stage_attempt, unit_id),
    FOREIGN KEY (run_id, fund_id) REFERENCES runs (run_id, fund_id)
);

CREATE TABLE IF NOT EXISTS paragraphs (
    run_id          TEXT NOT NULL,
    paragraph_id    TEXT NOT NULL,                     -- for example SRC-X-P2
    fund_id         TEXT NOT NULL,
    document_id     TEXT NOT NULL,
    paragraph_text  TEXT NOT NULL,
    PRIMARY KEY (run_id, paragraph_id),
    FOREIGN KEY (run_id, fund_id) REFERENCES runs (run_id, fund_id)
);

CREATE TABLE IF NOT EXISTS rows (
    row_id               TEXT PRIMARY KEY,             -- ROW-run-n, set by the backend
    run_id               TEXT NOT NULL,
    fund_id              TEXT NOT NULL,
    source_paragraph_id  TEXT NOT NULL,                -- exactly one, in the same run
    obligation_name      TEXT NOT NULL,
    frequency            TEXT,
    anchor               TEXT,
    "offset"             TEXT,                         -- quoted: OFFSET is an SQL keyword
    recipient_code       TEXT,
    responsible_role     TEXT,                         -- or "not stated in source"
    applicability_rule   TEXT,
    business_day_rule    TEXT,                         -- as the source states it, else not_confirmed
    quote                TEXT NOT NULL,                -- the source quote, verbatim
    origin               TEXT NOT NULL CHECK (origin IN ('model', 'demo')),
    version              INTEGER NOT NULL DEFAULT 1,
    UNIQUE (row_id, fund_id),
    FOREIGN KEY (run_id, fund_id) REFERENCES runs (run_id, fund_id),
    FOREIGN KEY (run_id, source_paragraph_id) REFERENCES paragraphs (run_id, paragraph_id)
);

CREATE TABLE IF NOT EXISTS quote_checks (
    row_id    TEXT PRIMARY KEY,                        -- one per row
    fund_id   TEXT NOT NULL,
    result    TEXT NOT NULL CHECK (result IN ('pass', 'fail')),  -- fail blocks approval
    mismatch  TEXT,
    FOREIGN KEY (row_id, fund_id) REFERENCES rows (row_id, fund_id)
);

CREATE TABLE IF NOT EXISTS flags (
    flag_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id              TEXT NOT NULL,
    run_id              TEXT NOT NULL,                 -- so other_paragraph_id can point at paragraphs
    fund_id             TEXT NOT NULL,
    flag_type           TEXT NOT NULL CHECK (flag_type IN ('internal', 'cross_source')),
    explanation         TEXT NOT NULL,
    field               TEXT,                          -- internal only
    row_value           TEXT,                          -- internal only
    quote_says          TEXT,                          -- internal only
    other_paragraph_id  TEXT,                          -- cross_source only
    other_quote         TEXT,                          -- cross_source only
    FOREIGN KEY (row_id, fund_id) REFERENCES rows (row_id, fund_id),
    FOREIGN KEY (run_id, other_paragraph_id) REFERENCES paragraphs (run_id, paragraph_id)
);

CREATE TABLE IF NOT EXISTS row_decisions (
    decision_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id             TEXT NOT NULL UNIQUE,           -- one per row (CR-009)
    fund_id            TEXT NOT NULL,
    decision           TEXT NOT NULL CHECK (decision IN ('approve', 'reject')),
    business_day_rule  TEXT CHECK (business_day_rule IS NULL OR business_day_rule IN
                         ('roll_forward', 'roll_backward', 'no_roll')),  -- on approve (DL-47)
    who_files          TEXT,                           -- when the source is silent (DL-39)
    reason             TEXT,
    row_version        INTEGER NOT NULL,
    decided_by         TEXT NOT NULL,
    decided_at         TEXT NOT NULL,
    FOREIGN KEY (row_id, fund_id) REFERENCES rows (row_id, fund_id)
);

CREATE TABLE IF NOT EXISTS verdicts (
    verdict_id           TEXT PRIMARY KEY,
    row_id               TEXT NOT NULL UNIQUE,         -- approved rows only
    fund_id              TEXT NOT NULL,
    verdict              TEXT NOT NULL CHECK (verdict IN ('applies', 'does_not_apply', 'unsure')),
    reasoning            TEXT NOT NULL,
    cited_fact_ids       TEXT NOT NULL,                -- one or more
    missing_information  TEXT,                         -- unsure only
    version              INTEGER NOT NULL DEFAULT 1,
    UNIQUE (verdict_id, fund_id),
    FOREIGN KEY (row_id, fund_id) REFERENCES rows (row_id, fund_id)
);

CREATE TABLE IF NOT EXISTS verdict_decisions (
    decision_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    verdict_id       TEXT NOT NULL UNIQUE,             -- one per verdict (CR-009)
    fund_id          TEXT NOT NULL,
    decision         TEXT NOT NULL CHECK (decision IN ('confirm', 'override', 'decide')),
    final_value      TEXT NOT NULL CHECK (final_value IN ('applies', 'does_not_apply')),
    reason           TEXT,
    verdict_version  INTEGER NOT NULL,
    decided_by       TEXT NOT NULL,
    decided_at       TEXT NOT NULL,
    FOREIGN KEY (verdict_id, fund_id) REFERENCES verdicts (verdict_id, fund_id)
);

CREATE TABLE IF NOT EXISTS calendar_versions (
    calendar_id   TEXT PRIMARY KEY,
    run_id        TEXT NOT NULL UNIQUE,                -- at most one per run
    fund_id       TEXT NOT NULL,
    version       INTEGER NOT NULL DEFAULT 1,
    generated_at  TEXT NOT NULL,
    UNIQUE (calendar_id, fund_id),
    FOREIGN KEY (run_id, fund_id) REFERENCES runs (run_id, fund_id)
);

CREATE TABLE IF NOT EXISTS calendar_entries (
    calendar_id        TEXT NOT NULL,
    entry_id           TEXT NOT NULL,                  -- ENT-fund-paragraph-recipient-period
    row_id             TEXT NOT NULL,                  -- DL-50, a row whose final G2 value is applies
    fund_id            TEXT NOT NULL,
    period             TEXT NOT NULL,                  -- anchor period or event ID
    unadjusted_date    TEXT,                           -- DL-50, before the business-day rule
    due_date           TEXT NOT NULL,                  -- after the business-day rule
    business_day_rule  TEXT CHECK (business_day_rule IS NULL OR business_day_rule IN
                         ('roll_forward', 'roll_backward', 'no_roll')),
    moved              INTEGER NOT NULL DEFAULT 0 CHECK (moved IN (0, 1)),
    precautionary      INTEGER NOT NULL DEFAULT 0 CHECK (precautionary IN (0, 1)),
    open_question_id   TEXT,                           -- for example OQ-7 (CR-027)
    PRIMARY KEY (calendar_id, entry_id),
    FOREIGN KEY (calendar_id, fund_id) REFERENCES calendar_versions (calendar_id, fund_id),
    FOREIGN KEY (row_id, fund_id) REFERENCES rows (row_id, fund_id)
);

CREATE TABLE IF NOT EXISTS publications (
    publication_id                     INTEGER PRIMARY KEY AUTOINCREMENT,  -- newest is live
    fund_id                            TEXT NOT NULL,
    calendar_id                        TEXT NOT NULL UNIQUE,
    acknowledged_rejected_row_ids      TEXT NOT NULL DEFAULT '[]',
    acknowledged_uncited_paragraph_ids TEXT NOT NULL DEFAULT '[]',
    published_by                       TEXT NOT NULL,
    published_at                       TEXT NOT NULL,
    FOREIGN KEY (calendar_id, fund_id) REFERENCES calendar_versions (calendar_id, fund_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id         INTEGER PRIMARY KEY AUTOINCREMENT,  -- append-only (CR-013)
    run_id           TEXT,                               -- empty for an event outside a run
    fund_id          TEXT NOT NULL,
    at               TEXT NOT NULL,
    actor            TEXT NOT NULL,                      -- specialist-1, gp-1, a stage or the system
    event_type       TEXT NOT NULL CHECK (event_type IN
                       ('decision', 'agent_output', 'gate_event', 'refusal', 'system')),
    subject_id       TEXT,                               -- a row, verdict, calendar or run ID
    subject_version  INTEGER,
    refusal_code     TEXT,                               -- refusals only
    reason           TEXT,
    trace_ref        TEXT,                               -- agent outputs only
    FOREIGN KEY (run_id, fund_id) REFERENCES runs (run_id, fund_id)
);

-- Append-only: the database itself refuses to change or remove an audit entry.
CREATE TRIGGER IF NOT EXISTS audit_log_no_update
BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only');
END;

CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only');
END;

-- One line per model call attempt (CR-018), stand-in calls included, so the cost count and the
-- audit link work the same way in both modes; the run's stored mode tells them apart.
-- Columns from sad.md §4 "The `trace` columns" (H-035). B3 step 6.
CREATE TABLE IF NOT EXISTS trace (
    trace_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            TEXT NOT NULL,
    fund_id           TEXT NOT NULL,
    step              TEXT NOT NULL,                     -- extract_rows, check_conflicts, judge_applicability
    stage_attempt     INTEGER NOT NULL CHECK (stage_attempt IN (1, 2)),   -- DL-51
    unit_id           TEXT NOT NULL,
    attempt_n         INTEGER NOT NULL,                  -- the call attempt (a retry is 2)
    at                TEXT NOT NULL,                     -- when the call started, ISO 8601 UTC
    prompt_version    TEXT NOT NULL,                     -- hash of the agent and task content used
    model             TEXT NOT NULL DEFAULT '',          -- empty in stand-in mode
    model_returned    TEXT NOT NULL DEFAULT '',          -- empty in stand-in mode (DL-40)
    settings_json     TEXT NOT NULL DEFAULT '{}',
    max_tokens        INTEGER,                           -- empty in stand-in mode
    input_hash        TEXT NOT NULL,
    raw_output        TEXT,
    parsed_output     TEXT,                              -- or validation_error, never both
    validation_error  TEXT,
    tokens_in         INTEGER NOT NULL DEFAULT 0,
    tokens_out        INTEGER NOT NULL DEFAULT 0,
    cost_usd          REAL NOT NULL DEFAULT 0,
    duration_ms       INTEGER NOT NULL DEFAULT 0,
    spend_activity    TEXT CHECK (spend_activity IS NULL OR spend_activity IN
                        ('spike', 'tuning', 'evaluation', 'rehearsal', 'demo')),  -- CR-030
    eval_case         TEXT CHECK (eval_case IS NULL OR eval_case IN
                        ('altered_quote', 'I-1', 'injection')),                   -- DL-45
    late              INTEGER NOT NULL DEFAULT 0 CHECK (late IN (0, 1)),          -- DL-43, rule 9
    -- Added by B3 step 7b PR 5 (additive only: nothing above was renamed or dropped). The first
    -- three columns' defaults are what a stand-in line holds, so stand-in lines look as before.
    -- `attempt_n` now counts HTTP requests of one unit: 1, 2, ... (a retry, or CrewAI's own repeat).
    stop_reason       TEXT NOT NULL DEFAULT '',          -- the API's finish reason ('stop', 'length'); empty if no answer
    provider_error    TEXT,                              -- why this attempt got no answer (HTTP status, timeout); empty if it did
    cost_estimated    INTEGER NOT NULL DEFAULT 0 CHECK (cost_estimated IN (0, 1)),  -- 1: no usage data came; worst case charged
    -- Step 4: 1 when the request did NOT carry the pinned settings (DL-40), e.g. CrewAI's silent repeat
    -- without `reasoning_effort` (H-064 condition c). A flag only: it does not fail the call.
    off_pinned_setting INTEGER NOT NULL DEFAULT 0 CHECK (off_pinned_setting IN (0, 1)),
    request_path      TEXT NOT NULL DEFAULT '',          -- the request's URL path, e.g. /v1/chat/completions (spike fix, step D); empty for a stand-in line
    UNIQUE (run_id, step, stage_attempt, unit_id, attempt_n),                     -- the record key
    FOREIGN KEY (run_id, fund_id) REFERENCES runs (run_id, fund_id)
);

CREATE TRIGGER IF NOT EXISTS trace_no_update
BEFORE UPDATE ON trace
BEGIN
    SELECT RAISE(ABORT, 'trace is append-only');
END;

CREATE TRIGGER IF NOT EXISTS trace_no_delete
BEFORE DELETE ON trace
BEGIN
    SELECT RAISE(ABORT, 'trace is append-only');
END;
