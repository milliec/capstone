// Visual snapshots of the stubbed UI (visual-regression skill; frontend.md §8 D-6; ux-review.md).
//
// One story, told in order, against the real app with stand-in data: sign in, start a review with
// the demo rule, decide, finish each step, publish; then the failure demo, 403 and 404.
// One snapshot per page × state × width. Widths from ux.md §7: specialist pages 1280 and 1024 px;
// sign-in and the General Partner's calendar 1280 and 360 px.
//
// A matching snapshot means "nothing changed since the approved baseline". It does not mean the
// design is good: that is the Human judgment in ux-review.md.
import { test, expect } from "@playwright/test";
import { fileURLToPath } from "node:url";

// Every browser session in this test gets the same font stylesheet (fonts.css, a pinned copy of
// Google's usual answer), because Google sometimes serves on-the-fly font builds that render text
// slightly differently and made the screenshots flaky (ux-review M-012). The app is unchanged.
const PINNED_FONTS_CSS = fileURLToPath(new URL("./fonts.css", import.meta.url));
async function newSession(browser) {
  const context = await browser.newContext();
  await context.route(/fonts\.googleapis\.com\/css2/, (route) =>
    route.fulfill({ path: PINNED_FONTS_CSS, contentType: "text/css" }));
  return context;
}

const SPECIALIST = [1280, 1024];
const WIDE_AND_PHONE = [1280, 360];

// Values that change every run (run IDs carry today's date; start, publish and "Last updated"
// times) are replaced with fixed placeholders in the page, just before the picture. Nothing in
// the app changes; this only touches the copy of the page in the test browser.
async function normalise(page) {
  await page.evaluate(() => {
    const d = new Date();
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const today = `${days[d.getDay()]} ${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      n.nodeValue = n.nodeValue
        .replace(/RUN-\d{8}-\d+/g, "RUN-YYYYMMDD-N")
        .split(today).join("Mon 1 Jan 2026")
        .replace(/\b\d{2}:\d{2}:\d{2}\b/g, "12:00:00")
        .replace(/\b\d{2}:\d{2}\b/g, "12:00");
    }
  });
  // Fonts (ux-review M-012): a fresh browser session sometimes took the picture before a font face
  // had finished loading, so body text rendered slightly differently. Ask for every face the page
  // declares, wait until all are loaded, then wait two frames so the text is painted with them.
  await page.evaluate(async () => {
    await Promise.all([...document.fonts].map((face) => face.load().catch(() => null)));
    await document.fonts.ready;
    await new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
  });
}

async function snap(page, name, widths) {
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await expect.soft(page).toHaveScreenshot(`${name}-${width}.png`, { fullPage: true });
  }
}

// Open a page, wait until it shows what we expect (the stand-in stages finish in the background),
// then normalise it.
async function open(page, path, ready) {
  await expect(async () => {
    await page.goto(path);
    await expect(page.locator(ready).first()).toBeVisible({ timeout: 1000 });
  }).toPass({ timeout: 20_000 });
  await normalise(page);
}

const form = (page, path, data) => page.request.post(path, { form: data });

test("the stubbed UI, page by page", async ({ browser }) => {
  const specialistContext = await newSession(browser);
  const gpContext = await newSession(browser);
  const anonContext = await newSession(browser);
  const anon = await anonContext.newPage();
  const sp = await specialistContext.newPage();
  const gp = await gpContext.newPage();

  await test.step("Sign-in", async () => {
    await open(anon, "/sign-in", "text=Sign in to the demo");
    await snap(anon, "01-sign-in", WIDE_AND_PHONE);
  });

  await form(sp, "/sign-in", { identity_id: "specialist-1" });
  await form(gp, "/sign-in", { identity_id: "gp-1" });

  await test.step("Before anything is published", async () => {
    await open(sp, "/specialist/runs", "text=No reviews yet");
    await snap(sp, "02-filing-rules-empty", SPECIALIST);
    await open(gp, "/calendar", "text=being prepared and checked");
    await snap(gp, "07-calendar-gp-empty", WIDE_AND_PHONE);
    await open(gp, "/specialist/runs", "text=You don't have access to this");
    await snap(gp, "08-no-access-403", [1280]);
    await open(sp, "/specialist/runs/RUN-20000101-99", "text=We can't find that page");
    await snap(sp, "08-not-found-404", [1280]);
  });

  const started = await form(sp, "/specialist/runs", { demo_planted_row: "true" });
  const rid = started.url().match(/RUN-\d{8}-\d+/)[0];
  const review = `/specialist/runs/${rid}`;

  await test.step("Step 2: check the rules", async () => {
    await open(sp, review, `a.btn[href$="/g1"]`);
    await snap(sp, "03-review-status-your-turn", SPECIALIST);
    await open(sp, `${review}/g1`, "text=What's your decision on this rule?");
    await snap(sp, "04-check-rules-at-step", SPECIALIST);
    // B3 step 5: stand-in stage A drafts 6 rules; the demo rule is rule 7. Rule 3 carries the one
    // checker flag, so approving it needs a reason (B2). Rules 2, 3, 5 and 6 need "who files".
    await form(sp, `/specialist/rows/ROW-${rid}-1/decision`,
      { version: "1", decision: "approve", business_day_rule: "roll_forward", who_files: "AIFM" });
    await form(sp, `/specialist/rows/ROW-${rid}-7/decision`,
      { version: "1", decision: "reject", reject_reason: "Quote doesn't support the rule" });
    await open(sp, `${review}/g1`, "text=Rejected");
    await snap(sp, "04-check-rules-two-decided", [1280]);
    // B2: the server refuses to finish checking while a rule is undecided, so decide the others.
    // B4: with the demo's G1 choices (answer key §5), so the calendar is the demo calendar.
    const demoChoices = {
      2: { business_day_rule: "no_roll", who_files: "Fund administrator" },
      3: { business_day_rule: "roll_forward", who_files: "Fund administrator",
           approve_reason: "Checked: the law itself sets the deadline" },
      4: { business_day_rule: "roll_backward" },
      5: { business_day_rule: "roll_backward", who_files: "AIFM" },
      6: { business_day_rule: "no_roll", who_files: "Tax advisor" },
    };
    for (const n of [2, 3, 4, 5, 6]) {
      await form(sp, `/specialist/rows/ROW-${rid}-${n}/decision`,
        { version: "1", decision: "approve", ...demoChoices[n] });
    }
    await form(sp, `${review}/g1/complete`, { run_version: "1" });
  });

  await test.step("Step 3: confirm what applies", async () => {
    await open(sp, review, `a.btn[href$="/g2"]`);
    await open(sp, `${review}/g2`, "text=What's your answer on this rule?");
    await snap(sp, "05-confirm-applies-at-step", SPECIALIST);
    // B3 step 5: answer 4 is the stand-in "AI can't tell", answer 6 "doesn't apply", the rest "applies".
    await form(sp, `/specialist/verdicts/VER-${rid}-4/decision`,
      { version: "1", decision: "decide", value: "applies", decide_reason: "Not confirmed in fund records yet" });
    // B2: every answer must be decided before finishing.
    for (const n of [1, 2, 3, 5]) {
      await form(sp, `/specialist/verdicts/VER-${rid}-${n}/decision`,
        { version: "1", decision: "confirm", value: "applies" });
    }
    await form(sp, `/specialist/verdicts/VER-${rid}-6/decision`,
      { version: "1", decision: "confirm", value: "does_not_apply" });
    await form(sp, `${review}/g2/complete`, { run_version: "2" });
  });

  await test.step("Step 4: publish", async () => {
    await open(sp, review, `a.btn[href$="/g3"]`);
    await open(sp, `${review}/g3`, "text=Is this calendar ready for the General Partner?");
    await snap(sp, "06-publish-at-step", SPECIALIST);
    // B2: the server compares the acknowledged lists with its own, so post them as the page does:
    // read from the page's own hidden fields (B3 step 5), so the script never repeats the data.
    const listed = (name) => sp.locator(`input[name="${name}"]`).evaluateAll((els) => els.map((e) => e.value));
    const ackLists = [
      ...(await listed("rejected_row_ids")).map((v) => `&rejected_row_ids=${encodeURIComponent(v)}`),
      ...(await listed("uncited_paragraph_ids")).map((v) => `&uncited_paragraph_ids=${encodeURIComponent(v)}`),
    ].join("");
    await sp.request.post(`/specialist/calendars/CAL-${rid}/publish`, {
      headers: { "content-type": "application/x-www-form-urlencoded" },
      data: `run_version=3&decision=publish&acknowledged=true${ackLists}`,
    });
    await open(sp, review, "text=See the calendar as the General Partner sees it");
    await snap(sp, "03-review-status-published", [1280]);
    await open(gp, "/calendar", "text=All entries");
    await snap(gp, "07-calendar-gp-published", WIDE_AND_PHONE);
    // B12 views (DL-49, H-040): wide only; below 960px the list alone shows, so set the width first.
    await gp.setViewportSize({ width: 1280, height: 900 });
    // The default view is Month (operator, 2026-11-17), so the List view gets its own picture.
    // The name also appears in a hidden view's table, so wait for the visible copy.
    await open(gp, "/calendar?view=list", "text=Subscription tax return and payment >> visible=true");
    await snap(gp, "07-calendar-gp-list-view", [1280]);
    await open(gp, "/calendar?view=year", "table.year-table");
    await snap(gp, "07-calendar-gp-year-view", [1280]);
    await open(sp, "/calendar", "text=All entries");
    await snap(sp, "07-calendar-specialist-published", [1280]);
  });

  await test.step("Failure demo", async () => {
    const failed = await form(sp, "/specialist/runs", { demo_fail_step1: "true" });
    const fid = failed.url().match(/RUN-\d{8}-\d+/)[0];
    await open(sp, `/specialist/runs/${fid}`, "text=This review failed");
    await snap(sp, "03-review-status-failed", [1280]);
    await open(sp, "/specialist/runs", "text=Failed");
    await snap(sp, "02-filing-rules-populated", SPECIALIST);
  });

  await specialistContext.close();
  await gpContext.close();
  await anonContext.close();
});
