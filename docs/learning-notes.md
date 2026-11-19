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

**"Extensible" is only checkable with scenarios.** A quality goal like "make it extensible" can't be
tested on its own. It became checkable once it had two concrete walkthroughs for the architect (a new
fund regime, a new marketing country) and rules any extension must pass (the old answer key still
matches, no check or approval is weakened). Sorting variation into regulation, fund terms and client
policy also helped, because each changes in a different way and has a different owner. Write paper
scenarios as questions for a specialist, not legal findings, so they don't read as a coverage promise.

**Cut scope by removing the text, not by labelling it.** The architecture document marked cut
features "future scope" but left their full design in place. An AI build agent reads the whole
document and builds what it finds described, so a label is a weak fence. Each later fix added more
text on top, and the file grew while it was being corrected. The repair was to rewrite it as a short
MVP version, list everything deferred once in a "Future Work" section, and keep the long version in
git history under a tag. It's the same reason a design file shouldn't keep abandoned screens on the
main page with a "not for build" sticker.

**A plan with no capacity number can't be checked.** "I'll commit the time it needs" sounded
reasonable, but it meant nobody could compare the estimate with anything. Once the number was written
down (five days against an estimate of about 45), the gap was obvious and the real trade-offs could
be decided. State how much time you have before judging whether a scope fits.

**Build last what you would cut first.** A plan can name what gets dropped if time runs short, but
that only works for work not yet started. The estimate listed the visual pass before the planted demo
row, while the drop order said the visual pass goes first. Built in the listed order, the time would
already be spent on the thing meant to be cut. Whenever you write a drop order, check that the build
order is its reverse, and say that the numbering of a list is not its sequence.

**A cap is not a budget.** I wanted model spend down to about US$15. Lowering the per-run cap helped
the worst case, but caps only limit what one run or one activity can cost; they can still add up past
the target. The real saving came from asking which model calls teach me something: building against
stand-in agents costs nothing, and real calls are kept for measuring, tuning, evaluating and the demo.
The total is enforced by the one thing that can enforce it, the prepaid balance. Lesson: set a cap for
the worst case, a call count for each activity, and let the money you load be the budget.

**Not every file needs to stay in sync: sort them into three tiers.** The architecture document grew
past 2,600 lines, and keeping every file up to date with it is not realistic. Sort files into
*sources of truth* (the PRD and the SAD; each fact lives in exactly one), *derived* files (the Build
card, the setup notes, the public summary; they point at the source by ID such as DL-40 instead of
re-explaining it) and *logs* (like this one; they only grow). A derived file may also be frozen on
purpose with a banner ("as of 12 Nov, see the SAD for changes"), which is better than a copy that is
quietly wrong. Also, a long reference document needs a one-page working copy. The Build card is
that copy, and agents should be pointed at it plus one named section, not the whole file.

**Personas that may not edit each other's files need a message board.** The product manager persona
cannot change the SAD, and the architect persona cannot invent requirements. That is a good
boundary, but it left the operator copy-pasting text between chats. The fix is one shared file,
`project-context/handoffs.md`: a persona asks for a change by writing a short entry (who it is for,
which IDs it touches, what should change, why), and the owner of the file makes the change and
records the outcome. A table of who owns which file keeps this working as more personas join.
Entries refer to IDs and never copy the text of a decision.

**Put decisions in files, not in the chat, especially if you switch models.** Switching the model
in the middle of a session keeps the conversation history, but a different model can read the same
vague instruction differently, and the first message after a switch is slower and costs more. A
decision that exists only in the chat is the one most likely to be misread or lost. Write it into
the file that owns it, and look at the diff after a model switch before accepting edits. This is
about the tool used to build the project, which is separate from the model the product itself will
call (DL-40).

**A story about a project goes stale when the project decides.** The case-study site was written
during Define. When the architecture was settled, about a dozen of its claims quietly became wrong:
it said an AI agent checks the quotes (code does, DL-14), showed a "not confirmed" weekend rule
(retired, DL-19 update) and had an Edit button (cut, DL-22). Nothing broke; the words just stopped
being true. The fix was a fact-check against the latest decision log, not against a summary, because
the summary was itself a snapshot from two days earlier. Lesson: anything that describes the project
from outside (a portfolio, a pitch, a README) needs a re-check whenever a phase closes. It's like a
case-study deck that still shows last quarter's screens.

**Two personas writing at once can take the same number.** The backend persona picked the next free
handoff number, H-063, and opened a pull request. While that request waited, the frontend persona
merged its own entry, also called H-063, at the same spot in `handoffs.md`. Neither had done anything
wrong: each checked the numbers on `main`, but the other's entry was still on a separate branch. The
clash showed up as a request that could no longer merge, and the fix was to renumber the late one
(H-064). Lesson: when several people or agents add to a shared numbered list, check the highest number
on every open branch right before committing, not when you start writing. It's like two designers
both naming a new frame "v3" in shared files: whoever saves second has to rename.

## 2. Designing AI agent systems

**Why I build this by directing a team of agents.** Two reasons. First, I want first-hand experience
of how AI-native product teams work, because that is the kind of design role I'm aiming for. Second,
the product is about people approving AI work, so I wanted the same discipline in how it is built:
every decision written down with its reason, owned by one agent, and checkable later by me or the next
agent. Prompting one long chat would have left the decisions in a conversation that ends.

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

**Decide who owns each step before deciding the shape of the system.** The architect's first move was
not "how many agents?" but a table: for every step a user sees, is the owner a model, plain code or a
person, and how bad and how reversible is a mistake there? Four facts about language models decide it.
They are probabilistic, so they may draft but never record. They have a knowledge cutoff, so they are
never asked what the law says from memory. They have limited working memory, so each call gets only
what that step needs. And they are steerable by their inputs, so nothing they say changes state. Once
the table existed, the "agent" wording in one requirement resolved itself: a word-for-word quote check
is a string comparison, so it belongs to code even though the requirement called the whole
verification step an agent. The verifier is still separate from the extractor; part of it is just not
a model. The note went to the operator as an open question, because an architect may reinterpret a
requirement's wording but must say so.

**Three named agents do not make an agent system.** The extractor, verifier and applicability judge
are three model roles, but the order they run in is written in code and a person sits between them.
That is a workflow. It would only become an "agent" if a model chose which role runs next. One pattern
was rejected for a reason worth remembering: evaluator-optimizer, where the checker's flags go straight
back to the maker, who revises until the checker is happy. It sounds efficient, but it would let a
model change a rule in response to a flag, and the whole point of the design is that only the
specialist does that. When a human is supposed to close a loop, don't automate the loop.

**"Try again" is only safe if the system knows what "again" means.** Re-running a failed step sounds
harmless until the second attempt adds six new rows next to the six from the first. The fix is a
label on every output, the idempotency key: run + step + which row + which version of the input. An
output with the same label replaces the old one instead of piling up. That is also why a retry limit
("three goes, then stop") was decided together with the key: without the key, a limit only caps how
many duplicates you get.

**A library's helpful defaults can quietly undo a design decision.** CrewAI can automatically re-ask
the model when its answer fails a check, and its house rules suggest at least two automatic retries.
Both sound safe. But the design had already decided that a bad answer is shown to the specialist
rather than retried, because silent retries hide systematic failures and spend budget. Following the
default would have rebuilt the "let the model fix itself" loop the design rejected. The fix was to
switch those defaults off and write down why, so the next person doesn't helpfully switch them back.

**The six CrewAI adapter deviations, and what each one protects** (SAD §2, decision log DL-21). The
project's CrewAI rule file gives sensible defaults for crews that *write documents*. This system's
crews return *data* that people check, so six rules needed a different answer:

| # | The rule said | We did instead | Because otherwise… |
|---|---|---|---|
| D1 | Retry a failed agent at least twice | Retry once, and only for network-type errors | …repeated failures would be hidden from the specialist and quietly cost money |
| D2 | Pass each task's output into the next task's prompt | Build every prompt from stored data | …the verifier would read the extractor's work and tend to agree with it, which is the very bias a separate checker exists to avoid |
| D3 | Describe the expected output as headings and a file path | Describe it as a typed data schema | …the rule fits documents, not data a program validates |
| D4 | Write each task's output to a file | Store it in the database; export traces after every evaluation run | …a file would be a second copy outside the rules that stop duplicates and edits. The export is required, and a test fails the run if it's missing, so the evidence trail isn't lost |
| D5 | (library default) Re-ask the model when its answer fails a check | Never re-ask; show the failure | …that is the "let the model fix itself" loop the design rejected. The cost is a lower first-try success rate, so the week-1 spike measures it |
| D6 | Put a human review step inside the task | The three gates in the backend are the review | …gate status would live inside the workflow engine, a second place that has to agree with the backend |

**How they were recorded matters too.** I first wrote the deviations straight into the architecture
document, then said there were two when there were really five plus one interpretation. The operator
stopped it: nothing gets recorded until each one is reviewed, with the rule quoted word for word, its
line number, the decisions it clashes with, the justification and the risk. Checking line by line is
what found the other four. A deviation is a decision, so it needs the same review as any other.

**A backstory is for reasons, not a résumé.** "You are a world-class expert with 20 years of
experience" gives the model nothing to act on. A useful backstory has four parts: who the agent
works for, which mistake costs that person most, the habits that follow from that, and the trap (a
case that looks like it fits but doesn't). Reasons matter because rules only cover the cases you
thought of. An agent that knows *why* it copies exactly ("a quote one word off costs the specialist
more than a gap") can handle a case no rule names. A quick test: if deleting a sentence wouldn't
change what the agent does, delete it. The same split keeps agent and task apart: values and reasons
go in the agent (role, goal, backstory), steps go in the task. Template: `docs/agent-card-template.md`.

**A time limit is only real if something enforces it, and it must leave room for its own retries.**
The plan said a stage had 180 seconds, yet one extraction call (90 s) plus its retry (90 s) and one
verification call (60 s) already needed 240. The library's own "max execution time" also turned out not
to stop a call already running. The fix is one rule everywhere: each call gets a timeout and one retry,
a stage's limit is the sum of its calls *with* their retries plus a margin, and the backend's own timer
ends the stage. Results that arrive after the stage has failed are thrown away but still paid for.
When a document gives the same limit in three places, add them up and check that they agree.

**A guardrail should block the mistake, not the topic.** The rule "refuse any date in an agent's
output" sounded safe, because a model must never work out a deadline. But a correct quote from a law
can contain "31 October", and a correct rule can name the "Law of 17 December 2010", so the strict
rule would have failed right answers. The fix was to say what the real risk is: refuse a date the
agent *wrote itself*, allow one *copied word for word* from the text it was given. Two small details
mattered too: month names only count when capitalised (so "rule 3 may apply" isn't read as "3 May"),
and the checker that only copies evidence needed no date check at all. A rule like this only shows
its flaw when real text runs through it, so the spec should be updated from what the build found
(H-052).

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

**Recount any number a document hands you before you write it into a test.** The architecture document
said the G1 coverage view would list five paragraphs that no row cites in the demo set. Writing the
acceptance criterion meant counting them: 13 paragraphs are loaded, the 6 rows cite 6 of them, so 7 are
uncited, not 5. The "five" probably came from a list of four named paragraphs plus a general remark about
the secondary source, which is three more. Nobody was careless. A number written in prose is a summary
of a calculation, and the calculation is what a test needs. If QA had copied "five", the first test run
would have failed on correct behaviour, and someone would have spent time suspecting the code. The habit:
when a story states an expected count, derive it from the data and show the sum (13 − 6 = 7), so the
next reader can check it without trusting you, and report any mismatch to the owner of the source
document instead of silently fixing it.

**Test data can carry its own answers.** The mock source files had helpful "Test note" lines ("the
correct verdict is unsure") and the fund profile had a "Decides" column. Useful for people, fatal if
they reach a prompt: the agent would be reading the answer key. The fix is a loader that takes only
the paragraph text and fact values, plus a test that renders every prompt and fails if any of that
content appears. Lesson: before an agent reads a file, ask what else is in the file besides the part
you meant it to read. It's like handing a usability-test participant a prototype with your
facilitator notes still on the artboard.

**Teach the principle, not the test case.** The judge needed a rule ("a fact counts only if it
asserts what the condition requires"), but a rule that echoes a demo case makes the evaluation look
better than the model is. The rule was written generally, then checked mechanically against the demo
material for shared wording. Lesson: when an instruction exists because of a known test case, word
it so it would make sense without that case, and check.

**Changing a rule moves the wrong answers too.** When the specialist's weekend choice for two filings
became "move to the preceding working day", the two right answers changed (Sun 28 Feb → Fri 26 Feb), as
expected. So did a wrong answer the key keeps on purpose: counting from the event date instead of the
awareness date used to give 20 Feb, which is a Saturday, so under the new rule it gives 19 Feb. A test
that looks for the old wrong value would quietly stop catching the mistake. Lesson: after a rule change,
recompute the deliberate mistakes as well as the correct results. Then prove a new test can fail: put
the old value back in a throwaway copy and watch the test go red. A test that has never failed hasn't
shown it can catch anything.

**A test that fails first can catch the code, not just the feature.** The stand-in pause had a test
that swapped Python's `sleep` for a fake one that only writes down what it was asked to wait. The test
failed: the fake was never called. The code was written `def unit_pause(settings, sleep=time.sleep)`,
and Python fixes a default value once, when the file loads, so swapping `time.sleep` later changed
nothing. The fix was `sleep=None`, looking up `time.sleep` at the moment of pausing. Lesson: a
default is a snapshot, not a live link. And a "real mode never pauses" test only means something if
the matching "stand-in does pause" test exists and can go red.

**A flaky test can be a flaky outside service.** The screenshot tests now and then reported every
page of one browser session as changed, with only tiny differences in body text. Waiting longer for
the fonts did not fix it. Asking Google Fonts the same question five times did: one answer in five
pointed to a different, built-on-the-fly copy of the Inter font, which renders slightly differently.
The fix was to give the tests a pinned copy of the usual answer, so every run uses the same font
files; the app itself is unchanged. Lesson: when a test fails "randomly", look for something outside
your code that can answer differently (a font server, a clock, a network), and pin it in the test.
It's like comparing two exports of a Figma frame where a shared library font quietly updated between
them: the design did not change, the font did.

**Run a failing visual test on the untouched code too.** A two-word data change made 10 screenshot
tests fail, and an older note in the handoffs said 18 already differed, so it was not clear which
failures were new. Setting the change aside and running the same test on plain `main` gave a clean pass,
which proved all 10 came from the change. Lesson: before you report what a change broke, get a baseline
from the code without it, and do not trust an old count. It's like comparing a new Figma version with
the last published one instead of with a screenshot someone remembers. A failing picture test after a
text change is expected; the job is to list the pictures, not to re-record them, so the person who owns
the approval can see exactly what moved.

**Clicking like a person finds what a shortcut test skips.** To film a walkthrough, a script clicked
through the app with a real cursor instead of sending form data straight to the server, as the
screenshot tests do. On the demo rule it pressed "Approve rule", and the server approved it, although
the page says that rule must not be approved. The screenshot tests never noticed, because they only
ever send "reject" for that rule. It was a known unbuilt block, not a bug, but nothing on screen said
so. Lesson: a test that takes the fast route checks the pages, not the choices a person could make on
them; walk the slow route by hand or by script before showing the work. It's like a prototype where
only the happy-path hotspots are wired: the review looks fine until someone taps the other button.

## 4. Data, privacy and public repositories

**A public repo is published forever.** Treat anything committed as public, even if deleted later.
Anonymisation isn't just swapping names: dates, row counts, version numbers and feature lists can also
identify an organisation.

**`.gitignore` only works once git is switched on.** It tells git what to skip, but has no effect until
`git init`. Always check `git status` before the first push.

**Keep the real-to-fake mapping out of the repo.** A list matching real names to mock names would itself
leak the real names. The private identifier list lives only in the git-ignored `reference/` folder.

**Disagreements between documents make good test data, but not from an employer.** Conflicting
deadlines across documents are both a strong illustration of the problem and test data for the verifier.
At first the MRD summarised real internal documents. A business review caught that this is confidential
material, even with every name removed, because specific figures and document details can still identify
the source. The evidence was rewritten as an illustrative scenario for a fictional firm, built from the
conflicts planted in the mock data. Lesson: the real-name scan catches names, not details. Anonymising
names is not enough; use evidence you made up or that is public.

**A safety check needs a recorded exception, not a switch-off.** The real-name scan blocked the first
commit of the case-study site because my own first name is on the private identifier list. The fix was
one named exception for that one entry, in that repo only, written into its `CLAUDE.md` with the date
and the reason. Every other identifier is still blocked, and the capstone's own scan stays strict.
Turning the check off "just this once" would have left the site with no check at all.

**Reference files can leak too.** The design-system files I worked from named the website the style was
extracted from. They stay out of the public repo; the tokens were rewritten into the site's own
stylesheet. A file you only *used* can still publish a name you didn't mean to.

**Moving a file can break its links.** The framework's README moved from the repo root to `docs/` to
make room for a project README. Its link `CHECKLIST.md` meant "the file next to me", so after the move
it pointed at `docs/CHECKLIST.md`, which doesn't exist. It needed `../CHECKLIST.md` ("go up one folder
first"). Lesson: after moving a file, search it for links that don't start with `http` and check each
one still lands. It's like moving a Figma component to another page and checking its instances still
resolve.

**A README is the front door, not a copy.** The project README summarises the PRD in a few lines per
section and links to the detailed documents. When something is still undecided (here, the agent
roster, which waits for the SAD), the README says "planned, not final" instead of guessing.

**A stash is a shelf, not a loss.** I switched branches in GitHub Desktop while a file had unsaved-to-git
changes. GitHub Desktop put those changes aside as a "stash" so the switch could happen, and the file
went back to its last committed state. It looked as if the work had vanished. It hadn't: a stash is
changes parked on a shelf, and restoring it puts them back. Lesson: commit before switching branches,
and if "stashed changes" appears, restore them before doing anything else. It's like Figma's version
history: the work is still there, just not on the canvas.

**A public site is safe when there is nothing to reach, not when it is hidden.** The hosted demo is
open to anyone, with a role picker instead of a login. That is only acceptable because the host holds
no model key (so no one can run up a bill), only mock data, and one low-value secret. The design makes
the safe state the only possible one: the app refuses to start if a key is present. Lesson: ask "what
could a stranger reach?" before asking "how do I lock it?". It's like publishing a Figma file with
only placeholder content: you don't need a password, you need to check there's nothing real in it.

**Resetting data must not fight the rules that protect it.** The audit log is append-only: the
database refuses edits and deletes. A "reset the demo" that deleted rows would have to defeat that
rule. The answer is to replace the whole database file with a fresh one and leave the rule alone.
Lesson: when a new feature seems to need an exception to a protection, look for a way to do it that
never touches the protection. Also, a reset means the hosted audit log is a demo record, not evidence.

**Check `git status` right before you delete, not at the start of the session.** Two files showed as
untracked (`??`) when a session began, so they looked like stray copies. Two hours and several merges
later they had been committed on purpose. Deleting them then showed as `D` (a tracked file deleted),
which is how it was caught, before anything was committed. Lesson: what git said earlier is a
snapshot, like a screenshot of a shared file. Look again immediately before deleting, and treat a
committed file as someone's decision, removed only by a pull request they asked for.

**When a diagram and a table describe the same thing, name which one is in charge.** The
architecture document listed its database tables in a table, and we added an entity-relationship
diagram (ERD) of the same tables. Two descriptions of one thing drift apart over time, like a design
file and the shipped screen. So the document now says: "The table list is the source for write rules.
If the two differ, stop and ask the architect." That turns drift into a question someone asks, not a
silent bug. Drawing the diagram also paid for itself: turning words into boxes and lines showed three
links the text never stated (for example, which rule a calendar entry came from), found before any
database existed rather than mid-build. How to read the lines: `||--o{` means "one to zero-or-many"
(one review drafts many rules); a foreign key (FK) is a column that points at another table's ID, and
each line in the diagram stands for one.

**A shortcut to a private folder is not covered by that folder's ignore rule.** To let the git hooks
run in a second checkout (a "worktree"), an agent made shortcuts (symlinks) to the private
`reference/` folder. The ignore line `reference/` ends in a slash, which means "only real folders",
and git sees a shortcut as a file, not a folder. A quick test showed the shortcut listed as a new file
ready to commit. Nothing leaked: the agent removed the shortcuts and the commit held only the three
intended files. Lesson: a protection is defined by its exact pattern, not by what it is meant to
protect. It's like a Figma share setting on a page: a link to that page from another file is a
separate thing with its own settings. Before relying on a rule, test the edge case.

**A check you run by hand is only as good as the tool it runs on.** All through the stubbed-UI
build, the agent ran the real-name scan by hand before each commit and it came back clean. Then the
commit hook blocked a commit: two lines in downloaded test-tool code (Playwright, git-ignored) matched
a word on the identifier list. The agent's scans had missed them because, in its environment, `grep`
was quietly swapped for a look-alike tool that decides where a "word" starts and ends differently.
The hook calls the system's own `grep`, so it was right, and every earlier commit had passed it.
Lesson: two copies of "the same" check can disagree; trust the one that guards the door (the hook),
and when a hand check matters, call the exact tool by its full path (`/usr/bin/grep`). It's like
checking colour contrast with a different plug-in from the one the design review uses: same
question, different answer.

## 5. Domain: fund compliance calendars

**Anchor + offset.** A deadline is stored as a rule ("year-end + 6 months"), not a date, so the same
rule works for funds with different year-ends.

**Business-day rolls depend on the authority.** CSSF and BCL deadlines that fall on a weekend roll to the
next business day; tax deadlines do not. Never apply one global rule.

**End-of-month convention.** For deadlines in months from a month end, the due date is the last day of
the target month (30 June + 2 months = 31 August).

## 6. Front-end and design in code

**In CSS, the later rule wins a tie.** When two rules are equally specific, the one further down the
file wins. A sticky contents menu stopped sticking because a later rule (added for an unrelated
annotation feature) reset its `position`. A panel stopped breaking out of the column because a later
`margin` shorthand reset its side margins. The fix both times: keep each property in one place, and
let add-on features (like annotations) live in their own layer instead of restyling the page.

**…but a more specific rule beats a later one.** Order only decides a tie. In the G1 mock-ups,
`.app p { margin: 0 }` (a class plus a tag) beat a later `.progress { margin-top: 24px }` (one class),
so the progress line was jammed under the summary cards. The fix is to match the specificity
(`.app .progress`), not to add `!important`.

**Check a design in the browser, not just in the code.** Screenshots at desktop and phone widths
caught colliding cards, clipped tables and wrong text sizes that looked fine when reading the code.
One catch: a headless browser's *window* cannot be made narrower than about 500px, so a "375px"
screenshot can quietly skip the phone rules. Set the *viewport* to 375px instead, and check that the
page is no wider than the screen (`scrollWidth` equals `innerWidth`).

**Design tokens: one source of truth.** Colours, type sizes, spacing and corners live in one file
(`@theme` in Tailwind v4). Each value becomes both a CSS variable and a class name, such as `text-brass`
or `bg-ivory`, so changing it once changes it everywhere. That is how a design system "lives in code"
instead of drifting away from a Figma library. A bonus: the spacing scale (8, 12, 16, 20, 36, 40, 60,
140px) is all multiples of 4px, which Tailwind already uses, so no custom spacing was needed.

**Self-host fonts.** Installing the fonts as packages (Fontsource) instead of loading them from Google
means visitors' browsers never contact a font service. Pages load faster and there is one less privacy
question to answer.

**Revealing is not blocking.** The spec says "no button is hidden to enforce a rule", yet the
answer-first form hides the Approve button until "Approve" is chosen. These don't clash: the form
hides a button only until you pick its answer, and every answer can always be picked, so nothing
is kept out of reach. Hiding *to stop someone* (for example, no Approve on the demo row) is what the
rule forbids; that case keeps the button and lets the server refuse with a reason. When a new
pattern seems to break a written rule, add one sentence saying why it doesn't, before a builder
reads the two as a contradiction (ux.md §1.2, H-028).

**Hidden is not absent.** An "answer first, then show its fields" form (CSS `:has()`) only *hides*
the other answer's fields; the browser still sends them when the form is submitted. So the server
must read the chosen answer and ignore everything that belongs to the other one, and two fields that
mean different things (an approve reason and a reject reason) need different names, or one quietly
overwrites the other. The rule for the app lives on the server, never in what the page shows (SAD
DL-48).

**A fix in one place can break another; check every page.** Real data made an ID break at its hyphen
("FACT-" / "STUB-1") on step 3. The first fix, "an ID never wraps" for every ID, fixed step 3 and
passed every test, but the visual check showed step 4 at 1024px had become 12px wider than the
screen: an ID in a narrow "Why" column could no longer wrap, so it pushed the table out. One style
rule reaches every page that uses the class, not only the one you were looking at. The fix was a
narrower rule (only IDs that head a table row), and the check that caught it was comparing every
page's width with the screen's, which a look at the fixed page alone would have missed
(ux-review H-015, `c84d181`).

---

## Audit

- 2026-11-06 · started during the Define phase; collects all learning notes from the session so far
- 2026-11-07 · added two notes from the approval-map session (skill discovery; Never vs Ask)
- 2026-11-07 · added two notes from the approval-decisions session (recovery paths need guards; new
  features can break old absolutes)
- 2026-11-07 · added one note from the consistency sweep (a new action belongs in every list of actions)
- 2026-11-08 · added theme 6 from the case-study microsite mockup session (CSS cascade; check in the
  browser)
- 2026-11-08 · added four notes from setting up the case-study site (recorded exceptions to safety
  checks; reference files can leak; design tokens; self-hosted fonts)
- 2026-11-08 · added one note from the extensibility session (extensible needs scenarios)
- 2026-11-09 · added two notes from the project README session (moved files break relative links; a
  README links rather than copies)
- 2026-11-11 · added three notes from the architect's work-ownership, pattern and controls sessions
  (decide owners before shape; three named agents are still a workflow; retry needs an idempotency
  key)
- 2026-11-11 · added one note from `*create-sad` pass (a) (library defaults can undo a design
  decision)
- 2026-11-11 · added the six CrewAI adapter deviations (D1–D6) with what each protects, and how
  they came to be reviewed before recording
- 2026-11-11 · added one note from the Define follow-up session (recount any number a document hands you before writing it into a test)
- 2026-11-12 · added two notes from the MVP rewrite of the architecture document (cut scope by removing text; a plan needs a capacity number)
- 2026-11-12 · added one note from the review of the MVP estimate (build last what you would cut first)
- 2026-11-12 · added one note from a branch switch during the architecture rewrite (a stash is a shelf, not a loss)
- 2026-11-12 · added one note from the model spend decision (a cap is not a budget)
- 2026-11-12 · added one note from the agent card template session (a backstory is for reasons, not a
  résumé)
- 2026-11-13 · added three notes from the documentation-sync session (three tiers of files; a message
  board between personas; decisions go in files, not chat)
- 2026-11-12 · added one note from the final SAD review (a time limit must cover its own retries)
- 2026-11-13 · added two notes from the G1 / GP mock-ups session (a more specific CSS rule beats a later one; set the viewport, not the window, for phone screenshots)
- 2026-11-14 · added one note from the design-exploration SAD update (a field hidden by CSS is still submitted)
- 2026-11-14 · added one note from the answer-key update for Q1 and Q2 (a rule change moves the wrong answers too; prove a test can fail)
- 2026-11-15 · added two notes from the case-study site sync session (a story about a project goes
  stale when the project decides; check `git status` right before deleting)
- 2026-11-16 · added why the project is built by directing a team of agents (operator's reasons:
  first-hand AI-native experience; control and checkable decisions)
- 2026-11-16 · added one note from the data model session (when a diagram and a table describe the
  same thing, name which one is in charge)
- 2026-11-16 · added one note from the B13 split session (a shortcut to a private folder is not
  covered by that folder's ignore rule)
- 2026-11-16 · added one note from the app-shell build (a default value is a snapshot; a test that
  fails first can catch the code)
- 2026-11-17 · added one note from the visual-regression setup (a hand-run check is only as good as
  the tool it runs on; the hook used the system grep and caught what the hand scan missed)
- 2026-11-17 · added one note from the visual-check flake (a flaky test can be a flaky outside service;
  pin it in the test)
- 2026-11-17 · added one note from the H-036 snapshot refresh (a fix in one place can break another;
  check every page's width, not only the page you fixed)
- 2026-11-17 · added one note from H-051 (run a failing visual test on the untouched code too, to know
  which failures are yours)
- 2026-11-18 · added one note from H-052 (a guardrail should block the mistake, not the topic; refuse
  a date the agent wrote, allow one it copied)
- 2026-11-19 · added one note from H-064 (two personas took the same handoff number; check every open
  branch right before committing)
