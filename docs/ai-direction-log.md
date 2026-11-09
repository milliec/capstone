# AI Direction Log

A diary of moments when I directed the AI tools building this capstone: the rule I gave, what the AI
did, why the result was subtly wrong (or right), and how I tightened the rule so it doesn't recur.

It feeds Chapter 03, "Directing the agents", of the case study. The learning notes
(`docs/learning-notes.md`) hold general lessons. This log holds the evidence: dates, files and
before/after.

> Public repo: no real names or internal details. The real-name scan in `CLAUDE.md` applies here too.

## How to add an entry

Write it while the moment is fresh. Two minutes is enough. Copy this template to the end of the log
and give it the next ID.

```markdown
## AID-000 · YYYY-MM-DD · Phase
**Persona / tool:** which agent or tool (e.g. @backend.eng in Cursor, Claude Code)
**The rule I gave:** what the instruction, rule or skill said
**What the AI did:** what it produced
**Why it was subtly wrong:** the gap between "looks right" and "is right"
**How I caught it:** review, a test, the validator, a screenshot…
**How I tightened it:** the rule or check I changed, so it can't recur
**Recorded in:** file and ID
```

Positive entries are welcome too: a case where the set-up made the AI behave well shows why the
set-up works.

---

## AID-001 · Define phase · A skill on disk is not a skill in use
**Persona / tool:** AAMAD personas in Cursor
**The rule I gave:** Use the agentic-approval-design skill when working on approvals.
**What the AI did:** The persona worked on approvals without reading the skill.
**Why it was subtly wrong:** The skill sat in `.cursor/skills/`, so it looked installed. But an agent
only reads a skill when it decides the description fits the task, and personas don't load skills
automatically.
**How I caught it:** Reviewing the output against the skill's method.
**How I tightened it:** Added a short rule that names the skill and the files it applies to. Also
recorded that a rule is still only guidance: real enforcement has to be code that refuses the action.
**Recorded in:** `.cursor/rules/approval-design.mdc` · `docs/learning-notes.md` §2

## AID-002 · Define phase · Asking instead of choosing silently (positive)
**Persona / tool:** @product-mgr
**The rule I gave:** An earlier decision of three approval gates, then a later instruction that
mentioned "one approval gate".
**What the AI did:** It stopped and asked which one applied, instead of quietly picking one.
**Why it matters:** A silent choice would have looked like a mistake to any reviewer, and the earlier
decision could have been lost without anyone noticing.
**How I tightened it:** The decision and its reason were recorded, so a deliberate choice can be told
apart from an error.
**Recorded in:** `docs/learning-notes.md` §1

## AID-003 · 2026-11-09 · Define phase · Anonymised is not the same as not confidential
**Persona / tool:** @product-mgr (MRD and PRD), later Claude Code
**The rule I gave:** The public-repo rules in `CLAUDE.md`: never commit real names *or other internal
details*, and never copy from `reference/` into committed files.
**What the AI did:** It wrote the MRD evidence from my employer's internal working documents. It
replaced every name with a role ("the operator", "a GP") and cited the documents as a private source.
But it kept specific figures and document disagreements from them, and the PRD repeated the claim. An
earlier quality pass even "reduced detail on internal sources", yet the specifics stayed.
**Why it was subtly wrong:** It followed the half of the rule that can be checked (no names) and missed
the half that needs judgement (no internal details). The real-name scan passed, so everything looked
safe. But specific figures can still identify their source, and confidential material doesn't become
public just because the names are gone. It was already merged to `main` on a public repo.
**How I caught it:** My own business review of the PRD, reading it as a portfolio piece rather than as a
requirements document.
**How I tightened it:** The evidence is now an illustrative scenario for a fictional firm (SRC-ILLUS),
built only from the conflicts planted in the mock data. A PRD §5 rule says no employer documents are cited
or summarised. The rule is listed in the stories README for `@security.eng` to check, because a scan
can't. The old wording is still in the git history; how to handle that is a separate decision.
**Recorded in:** `project-context/1.define/decision-log.md` DL-07 · `docs/learning-notes.md` · PRD §5

---

## Audit

- 2026-11-08 · created with the template and two entries from the Define phase
- 2026-11-09 · added AID-003 (employer details in the evidence, caught in the business review)
