// Visual snapshots of an EVALUATION review on the run pages (H-101, DL-60, UX-025).
//
// Three pictures, each from a database seeded by seed_evaluation.py (an ordinary review and an
// evaluation review, both published, made against a fake model on this machine; no real call):
//   page 2 populated         the review list: the "Evaluation review" tag on one row, not the other
//   page 3 published         the status page of the published evaluation review
//   page 6 after G3          the publish page of the same review, after the decision
// 1280 px wide only, one picture each. The app here runs in stand-in mode and only reads the database.
//
// Same rule as visual.spec.js: a matching snapshot means "nothing changed since the approved
// baseline". It does not mean the design is good.
import { test, expect } from "@playwright/test";
import { newSession, snap, open, form } from "./helpers.js";

// The evaluation database is served by its own app, on its own port (playwright.config.js).
test.use({ baseURL: "http://127.0.0.1:8778" });

test("an evaluation review on the run pages", async ({ browser }) => {
  const context = await newSession(browser);
  const sp = await context.newPage();
  await form(sp, "/sign-in", { identity_id: "specialist-1" });

  // Find the evaluation review by its tag, never by position, so the test cannot photograph
  // the ordinary review by mistake.
  await open(sp, "/specialist/runs", "text=Evaluation review");
  const row = sp.locator("tr", { hasText: "Evaluation review" });
  await expect(row).toHaveCount(1);
  const review = await row.locator("a").first().getAttribute("href");

  await snap(sp, "02-filing-rules-populated-evaluation", [1280]);

  await open(sp, review, "text=for the evaluation only");
  await snap(sp, "03-review-status-published-evaluation", [1280]);

  await open(sp, `${review}/g3`, "text=for the evaluation only");
  await snap(sp, "06-publish-after-g3-evaluation", [1280]);

  await context.close();
});
