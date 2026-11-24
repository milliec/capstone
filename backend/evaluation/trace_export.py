"""The trace export of an evaluation run (sad.md D4, T-D4-1; H-097 PR 2).

Why a file at all? The model's outputs live in the database, which is the one store (and the trace
table inside it is append-only). D4 adds ONE copy for the evaluation cycle: every evaluation run
exports its trace to `project-context/2.build/logs/<run_id>/`, so the report and the trace travel
together. The database stays the truth; the export is checked against it.

    export_trace(conn, run_id, out)   writes  <out>/<run_id>/trace.jsonl   one record per model call
                                              <out>/<run_id>/trace-export.json   a small note
    check_export(conn, run_id, out)   says whether that export is there and matches the store.

`trace.jsonl` is "JSON Lines": one JSON object per line, one line per trace row (every attempt,
retries and late calls included, because the store keeps them too).

An evaluation run without a good export is reported as FAILED and the report says why
(`ExportCheck.why`). This module only judges and writes; it starts no run, calls no model, and
reads the database without changing it.
"""

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from backend.evaluation.report import DEFAULT_OUT
from backend.evaluation.stage_a import NotGradable

TRACE_FILE = "trace.jsonl"
NOTE_FILE = "trace-export.json"
REMOVED = "[removed]"

# What a secret looks like when we were not told its exact value: a provider key ("sk-..."), and
# whatever follows "Bearer " (the word in an Authorization header, which can show up in error text).
_KEY_SHAPE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
_BEARER = re.compile(r"(Bearer\s+)\S+", re.IGNORECASE)


@dataclass(frozen=True)
class ExportResult:
    exported: bool          # True when the files were written
    records: int            # how many trace records the export holds
    why: str                # when nothing was written: the reason, in words
    folder: Path | None = None


@dataclass(frozen=True)
class ExportCheck:
    ok: bool
    why: str                # empty when ok; otherwise what is wrong, ready for the report

    @property
    def failed(self) -> bool:
        """The evaluation run is reported FAILED, and `why` is what the report says (D4)."""
        return not self.ok


def remove_secrets(text: str, secrets=()) -> str:
    """Replace every secret in `text` with [removed]: each exact value given, then anything shaped
    like a provider key or a bearer token. The rest of the text is left as it was."""
    for value in secrets:
        if value:
            text = text.replace(value, REMOVED)
    text = _BEARER.sub(lambda m: m.group(1) + REMOVED, text)
    return _KEY_SHAPE.sub(REMOVED, text)


def _clean(value, secrets):
    return remove_secrets(value, secrets) if isinstance(value, str) else value


def _key(record: dict) -> tuple:
    """The trace record key (CR-018): run, step, stage attempt, unit, attempt number."""
    return (record["run_id"], record["step"], record["stage_attempt"], record["unit_id"],
            record["attempt_n"])


def _stored(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    if conn.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone() is None:
        raise NotGradable(f"there is no run {run_id} in this database")
    return [dict(r) for r in conn.execute(
        "SELECT * FROM trace WHERE run_id = ? ORDER BY trace_id", (run_id,))]


def export_trace(conn: sqlite3.Connection, run_id: str, out=DEFAULT_OUT, *, secrets=(),
                 enabled: bool = True) -> ExportResult:
    """Write the run's trace to `<out>/<run_id>/`. `secrets` are exact values to remove (the API
    key); key-shaped text is removed anyway. With `enabled=False` nothing is written: the run then
    has no export, and `check_export` reports it failed (T-D4-1)."""
    records = _stored(conn, run_id)              # raises NotGradable for an unknown run
    if not enabled:
        return ExportResult(False, 0, "the trace export is switched off")
    folder = Path(out) / run_id
    folder.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({k: _clean(v, secrets) for k, v in r.items()}, ensure_ascii=False)
             for r in records]
    _write(folder / TRACE_FILE, "".join(line + "\n" for line in lines))
    note = {"run_id": run_id, "records": len(records), "secrets_removed": True,
            "exported_at": datetime.now(UTC).isoformat(timespec="seconds")}
    _write(folder / NOTE_FILE, json.dumps(note, indent=2) + "\n")
    return ExportResult(True, len(records), "", folder)


def _write(path: Path, text: str) -> None:
    """Write to a side file, then rename, so a half-written export is never left under the name."""
    side = path.with_name(path.name + ".part")
    side.write_text(text, encoding="utf-8")
    side.replace(path)


def check_export(conn: sqlite3.Connection, run_id: str, out=DEFAULT_OUT) -> ExportCheck:
    """Is the export there, and does it hold exactly the records the trace store holds? The
    comparison is by record key, because removing a secret changes a record's text, not its key."""
    stored = _stored(conn, run_id)
    path = Path(out) / run_id / TRACE_FILE
    if not path.is_file():
        return ExportCheck(False, f"the trace export is missing for {run_id}: no {path}")
    try:
        exported = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()]
        exported_keys = [_key(r) for r in exported]
    except (ValueError, KeyError, TypeError):
        return ExportCheck(False, f"the trace export for {run_id} cannot be read: {path}")
    if len(exported) != len(stored):
        return ExportCheck(False, f"the trace export for {run_id} holds {len(exported)} records "
                                  f"but the trace store holds {len(stored)}")
    if sorted(exported_keys) != sorted(_key(r) for r in stored):
        return ExportCheck(False, f"the trace export for {run_id} does not match the trace store "
                                  "(a record key differs)")
    return ExportCheck(True, "")
