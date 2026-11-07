# Learning Notes

A running journal of lessons from building this capstone. Written for a product designer learning how
AI agent systems and product requirements are put together. Newest themes can be added at the end of any
section.

> These are general lessons. No confidential details belong here.

---

## 1. Product and requirements practice

**Traceability: bucket → requirement → test.** Every requirement links back to a reason and forward to
a test. Example: MD-006 ("dates by deterministic code") → FR-011/FR-012 → AC-010 ("Sunday rolls to
Monday"). Anyone can ask "why does this test exist?" and follow the chain back to the brief. It is the
same idea as linking a design decision to a research insight.

**One source of truth, then link to it.** The PRD *refers* to the system description ("SD AC-010")
instead of copying it. Copies drift apart the first time someone edits only one. It's like using
components in a design system instead of detached copies.

**Scope hammering (Shape Up).** When a feature is valuable but outside the core question, don't drop it
silently. Name it, say why it waits, and protect the path back. *Example:* filing status was put out of
scope, but every calendar entry got a stable ID so status can be attached later.

**Inferred needs are hypotheses, not findings.** A PRD restates user needs; it doesn't collect them.
When no one has been interviewed, say so openly. Labelling needs as "inferred" tells everyone
downstream what is still unproven, and what to update after even 2–3 interviews.

**Surface conflicts, don't resolve them silently.** When an instruction ("one approval gate") clashed
with an earlier decision ("three gates"), the right move was to ask, then record the decision and the
reason. A reviewer can then tell a deliberate choice from a mistake.

**Writing exact tests exposes hidden assumptions.** Turning the PRD into stories with exact pass/fail
values revealed that "18 calendar entries" silently depended on a human decision at a gate. Vague
requirements hide that kind of dependency.

**Trace features to evidence, not just to other requirements.** The readiness check found that every
PRD feature traced to the system description, but none traced directly to the evidence (MRD). A chain
of requirements pointing at requirements can look complete while its "why" is missing. Each feature
now says which user need and which piece of evidence it serves.

**A good readiness test: could you argue with it?** Documents are ready when they make specific claims
someone could disagree with ("22 entries", "tax deadlines don't roll"). Vague documents can't be argued
with, so they can't be checked either. Listing the calls the PM made alone, and asking the owner to
confirm them, turns hidden assumptions into decisions.

**Name the stakeholders you leave out.** The filing parties (AIFM, administrator, auditor) do most of the
real work, but they aren't MVP users. Listing them explicitly, with what they get now (a "who files" field)
and later (notifications), shows they were excluded on purpose, not forgotten.

**Background context explains the problem; it isn't a requirement.** Notes on overlapping regulatory
layers made the problem clearer, so they went into the evidence note, labelled "not verified". Nothing
in the requirements depends on them.

**Don't cut scope before there's an estimate.** Six-week fit was unproven, but cutting features without
an estimate is guessing. The decision was to keep full scope, ask the architect for an estimate, and
keep a proposed cut line ready in case it's needed.

**New features can break old absolutes.** Adding "reopen a rejected rule" contradicted a criterion
saying a rejected row is "never" sent on. "The system never changes an entry" clashed with the system
marking entries out of date. When adding a capability, search for "never", "only" and "always" in what
already exists, and reword them so they say exactly what is forbidden.

**A new action belongs in every list of actions.** Adding "reopen" and "decline" updated the stories
for them, but two lists elsewhere still named only the old actions: who may act (the access rule) and
which decisions need a logged reason (the audit log). Searching for the new requirement's ID won't find
these, because they never mention it. After adding an action, also search for the old list, such as
"approve, edit, reject", and add the new action wherever it appears.

## 2. Designing AI agent systems

**Use AI where judgement is needed, plain code where correctness is needed.** Agents read text and
judge applicability. Dates are calculated by ordinary code, because code gives the same answer every
time and can be tested without a model.

**A quote check is not a meaning check.** Checking that a quote really exists in the source is like
checking that a citation is in the bibliography. It doesn't prove the sentence citing it says the same
thing. Extraction errors usually happen exactly there: right paragraph, read wrongly. That's why the
verifier also checks that a row's fields match its own quote.

**A separate checker catches what the maker misses.** The verifier must not be the agent that
extracted the row, for the same reason a designer doesn't usability-test their own work.

**Under uncertainty, choose the cheaper mistake** (design principle P-1). In compliance, an extra
calendar entry costs minutes; a missed filing is a breach. So: unsure if an obligation applies → include
it as a precaution; unsure if a deadline rolls past a weekend → keep the earlier date. Good systems make
the cheap mistake the default.

**Workflow or agent? Ask who decides the next step.** In a workflow the path is fixed by design, even
if each step uses AI judgement (extract → verify → judge applicability, always in that order). In an
agent the model decides what to look at next and when it's done. Change monitoring is agentic: an
amendment might affect one duty, several or none, and the system has to work out how far it reaches. The
product manager requires the behaviour. The architect decides whether it is built as an agent.

**Test the "none" case.** When a system decides its own scope, over-reaching is the likely failure. A
test where the right answer is "nothing is affected" is as important as one where something is.

**Words that mean two things cause bugs.** "Pending confirmation" (a precaution the GP should see) clashed
with "pending" (not yet approved, which the GP must never see). Renaming it "precautionary" removed the
contradiction. This is UX writing as a correctness tool.

**A skill on disk is not a skill in use.** Cursor finds project skills in `.cursor/skills/`, but an
agent only reads one when it decides the description fits the task. Personas don't load skills
automatically. A short rule that names the skill and the files it matters for makes it reliable. Even
then, a rule is guidance: approvals are only enforced by code that refuses the action.

**"Never" means the button doesn't exist.** In an approval map, an action marked Never (an agent
publishing, approving a row whose quote failed) must be missing from the system, not hidden behind a
confirmation. A confirmation is an Ask; a missing capability is a Never.

**Recovery paths need the same guards as the main path.** Reopening a rejected rule needs a reason. If
editing that rule had also sent it back for review, it would have been a second way back with no reason
asked for. The fix was to make rejected rules read-only until they are reopened. And a warning notice
reduces harm without preventing it, so the requirement says so.

## 3. Testing and evaluation

**An answer key is how you prove the agents work.** QA runs the agents on the mock sources and compares
the output to the expected results, row by row, like checking a prototype against the spec rather than
judging it by eye.

**Plant problems on purpose.** The mock data includes a paragraph with no obligation, a decoy that
should not apply, an ambiguous case, two planted conflicts, and an agreeing source (to test for false
alarms). Each one tests a specific behaviour.

**Date maths needs a script, not a person.** Month ends, leap years and weekends are easy to get wrong
by hand. A script found that "2 months after 30 June" gives 30 August with plain maths but 31 August under
the end-of-month convention.

**Make every "done" check scoreable from the record, not from being in the room.** A check timed by
hand can only be scored by someone watching the clock. Measuring review time from audit-log timestamps
turns it into something anyone can check from the evaluation report later.

**Ask whether a metric measures the system or the setup.** In a scripted demo, the specialist's edits
are decided in advance, so a "rows approved without edits" rate would measure the script, not the
agents. A metric like that only means something with real users on material nobody prepared.

## 4. Data, privacy and public repositories

**A public repo is published forever.** Treat anything committed as public, even if deleted later.
Anonymisation isn't just swapping names: dates, row counts, version numbers and feature lists can also
identify an organisation.

**`.gitignore` only works once git is switched on.** It tells git what to skip, but has no effect until
`git init`. Always check `git status` before the first push.

**Keep the real-to-fake mapping out of the repo.** A list matching real names to mock names would itself
leak the real names. The private identifier list lives only in the git-ignored `reference/` folder.

**Disagreements in internal documents are evidence.** Conflicting lead times across internal documents
became both the proof that the problem is real (MRD) and test data for the verifier.

## 5. Domain: fund compliance calendars

**Anchor + offset.** A deadline is stored as a rule ("year-end + 6 months"), not a date, so the same
rule works for funds with different year-ends.

**Business-day rolls depend on the authority.** CSSF and BCL deadlines that fall on a weekend roll to the
next business day; tax deadlines do not. Never apply one global rule.

**End-of-month convention.** For deadlines in months from a month end, the due date is the last day of
the target month (30 June + 2 months = 31 August).

---

## Audit

- 2026-11-06 · started during the Define phase; collects all learning notes from the session so far
- 2026-11-07 · added two notes from the approval-map session (skill discovery; Never vs Ask)
- 2026-11-07 · added two notes from the approval-decisions session (recovery paths need guards; new
  features can break old absolutes)
- 2026-11-07 · added one note from the consistency sweep (a new action belongs in every list of actions)
