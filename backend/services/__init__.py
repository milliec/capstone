"""Services: every check and rule lives here, never in a page handler or template (SAD §4).

In the app shell most functions are STUBS. Each stub already has the name and place B2 gives it,
so B2 fills it in and nothing is renamed or moved (Build card, "Build approach").
"""

FUND_ID = "FND-DEMO-01"  # The MVP has one fund. Set by the backend, never taken from a form.
