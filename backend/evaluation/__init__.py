"""The evaluation runner (B8, W-20, US-013). Grading only: nothing under backend/ except this
package may import it or read its files (T-MAP-1 d), and no agent, prompt or page ever sees the
answer key it reads.

First slice (operator decision, 2026-11-21): the Stage A grader. It grades a FINISHED stage A run
read from the database; it starts no run and calls no model. The run starter (evaluation-run type,
scripted gates, EC-R7 refusal), the trace export (D4) and the copy cases that need a model (`I-1`,
the injection case) are the rest of B8.
"""
