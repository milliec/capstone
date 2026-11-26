// Visual snapshots of an EVALUATION review waiting at a step (H-106, DL-61, UX-026).
//
// Four pages, each at 1280 px and 360 px (page 4 also has a top-of-page picture at 360 px). Each step has its own app and database, because only
// one review can be active at a time (playwright.config.js, seed_evaluation.py "at a step"):
//   page 2 at G1   the review list: the notice "Evaluation review 1: …" with one link, no "Your turn" tag
//   page 3 at G1   held until H-108 is answered (see STEPS below)
//   page 4 at G1   the one line and the rules, read-only, no form
//   page 5 at G2   the one line and the answers, read-only, no form
//   page 6 at G3   the one line and the calendar, no publish form
// No real call: the databases are made against a fake model on this machine.
//
// Same rule as visual.spec.js: a matching snapshot means "nothing changed since the approved
// baseline". It does not mean the design is good.
import { test, expect } from "@playwright/test";
import { newSession, snap, open, form } from "./helpers.js";

const STEPS = [
  // Page 3 (suffix "") is held: its status box still prints "Your turn: check the rules" until
  // `@ux.designer` answers H-108. Add ["", "03-review-status-at-step-evaluation", "text=Nothing for you to do yet"]
  // here, in a follow-up, once the words are settled.
  { step: "g1", port: 8779, pages: [[null, "02-filing-rules-at-step-evaluation", "text=Evaluation review 1:"],
                                     ["/g1", "04-check-rules-at-step-evaluation", "text=This is an evaluation review", { top360: true }]] },
  { step: "g2", port: 8780, pages: [["/g2", "05-confirm-applies-at-step-evaluation", "text=This is an evaluation review"]] },
  { step: "g3", port: 8781, pages: [["/g3", "06-publish-at-step-evaluation", "text=This is an evaluation review"]] },
];

for (const { step, port, pages } of STEPS) {
  test(`an evaluation review waiting at ${step}`, async ({ browser }) => {
    const context = await newSession(browser);
    const sp = await context.newPage();
    const base = `http://127.0.0.1:${port}`;
    await form(sp, `${base}/sign-in`, { identity_id: "specialist-1" });

    // Find the one review by its tag, never by position.
    await open(sp, `${base}/specialist/runs`, "text=Evaluation review");
    const link = sp.locator("tr", { hasText: "Evaluation review" }).locator("a").first();
    await expect(link).toHaveCount(1);
    const review = await link.getAttribute("href");

    for (const [suffix, name, ready, extra] of pages) {
      // suffix null = the review list (page 2); "" = page 3; "/g1" … = pages 4 to 6
      await open(sp, suffix === null ? `${base}/specialist/runs` : `${base}${review}${suffix}`, ready);
      // Pages 4 to 6 are the proof there is no control: not one form field in the page body.
      // (Pages 2 and 3 keep a form: "Start a review" and "Abandon this review".)
      if (suffix && suffix !== "") await expect(sp.locator("main input, main textarea, main select")).toHaveCount(0);
      await snap(sp, name, [1280, 360]);
      // Page 4 is 11,000 px tall at 360 px, too long to judge by eye: add a picture of the top screen only.
      if (extra && extra.top360) {
        await sp.setViewportSize({ width: 360, height: 900 });
        await expect.soft(sp).toHaveScreenshot(`${name}-top-360.png`, { fullPage: false });
      }
    }
    await context.close();
  });
}
