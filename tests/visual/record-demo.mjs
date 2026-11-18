// Records a walkthrough video of the app: the full stand-in happy path, clicked through the way a
// person would. Run from tests/visual/:  npm run record:demo
//
// What it does, in order:
//   1. starts its own copy of the app (own port, fresh throwaway database, stand-in agents)
//   2. opens a browser that films itself, and clicks through the story below
//   3. saves the film to docs/demo-video/ (git-ignored) and converts it to .mp4 with ffmpeg
//
// It is NOT a test and never changes the app or the visual snapshots. No model is called.
// To change the pacing, edit the numbers in PACE. To change the story, edit the steps at the bottom.
import { chromium } from "playwright";
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = resolve(fileURLToPath(new URL("../..", import.meta.url)));
const OUT_DIR = join(REPO, "docs", "demo-video"); // docs/* is git-ignored, so the film stays private
const PORT = 8779; // not 8000 (make run) and not 8777 (visual tests), so nothing collides
const BASE = `http://127.0.0.1:${PORT}`;
const SIZE = { width: 1440, height: 900 }; // the film's size in pixels

// How long to linger, in milliseconds. Bigger numbers = a slower, calmer film.
const PACE = {
  read: 1800, // after arriving on a new page
  glance: 900, // after a small change on the same page
  beforeClick: 350, // cursor rests on a button before pressing it
  key: 28, // between typed letters
};

const pause = (ms) => new Promise((done) => setTimeout(done, ms));

// ---------------------------------------------------------------------------------------------
// 1. The app
// ---------------------------------------------------------------------------------------------
async function startApp() {
  const dbDir = mkdtempSync(join(tmpdir(), "demo-video-"));
  const server = spawn(
    join(REPO, ".venv/bin/python"),
    ["-m", "uvicorn", "backend.main:create_app", "--factory", "--port", String(PORT)],
    {
      cwd: REPO,
      stdio: "ignore",
      env: {
        ...process.env,
        AGENTS_MODE: "stand_in", // project rule: stand-in only
        STAND_IN_UNIT_PAUSE_S: "0.7", // each "AI" unit takes 0.7s, so progress is visible on film
        SESSION_SECRET: "demo-video-only",
        DATABASE_PATH: join(dbDir, "demo.db"),
      },
    },
  );
  // Wait until the app answers.
  for (let i = 0; i < 60; i++) {
    try {
      if ((await fetch(`${BASE}/health`)).ok) return { server, dbDir };
    } catch { /* not up yet */ }
    await pause(500);
  }
  server.kill();
  throw new Error("The app did not start within 30 seconds.");
}

// ---------------------------------------------------------------------------------------------
// 2. A visible cursor
// ---------------------------------------------------------------------------------------------
// A filmed browser shows no mouse pointer, so this draws one. It lives only in the filming
// browser's copy of each page. It remembers its position between pages so it does not jump.
function drawCursor() {
  const start = () => {
    if (document.getElementById("demo-cursor")) return;
    const c = document.createElement("div");
    c.id = "demo-cursor";
    c.innerHTML =
      '<svg width="22" height="22" viewBox="0 0 24 24"><path d="M5 3l14 8-6.2 1.6L9.6 19z" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    c.style.cssText =
      "position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;margin:-3px 0 0 -5px;";
    const ring = document.createElement("div");
    ring.style.cssText =
      "position:fixed;left:0;top:0;z-index:2147483646;pointer-events:none;width:36px;height:36px;" +
      "margin:-18px 0 0 -18px;border-radius:50%;background:rgba(17,17,17,.18);opacity:0;" +
      "transition:opacity .25s, scale .25s;scale:.4;";
    document.documentElement.append(ring, c);
    const place = (x, y) => {
      c.style.translate = ring.style.translate = `${x}px ${y}px`;
      try { sessionStorage.setItem("demo-cursor", JSON.stringify([x, y])); } catch { /* fine */ }
    };
    let saved = null;
    try { saved = JSON.parse(sessionStorage.getItem("demo-cursor")); } catch { /* fine */ }
    place(...(saved || [innerWidth / 2, innerHeight / 2]));
    addEventListener("mousemove", (e) => place(e.clientX, e.clientY), true);
    // A soft grey ring flashes where a click lands.
    addEventListener("mousedown", () => { ring.style.opacity = "1"; ring.style.scale = "1"; }, true);
    addEventListener("mouseup", () => setTimeout(() => { ring.style.opacity = "0"; ring.style.scale = ".4"; }, 180), true);
  };
  if (document.body) start();
  else addEventListener("DOMContentLoaded", start);
}

// ---------------------------------------------------------------------------------------------
// 3. Human-like actions
// ---------------------------------------------------------------------------------------------
let mouse = { x: SIZE.width / 2, y: SIZE.height / 2 };

// Scroll smoothly until the element sits in the middle of the window.
async function look(target, ms = PACE.glance) {
  await target.first().evaluate((el) => el.scrollIntoView({ behavior: "smooth", block: "center" }));
  await pause(650 + ms);
}

// Glide the cursor to the element (ease in, ease out), rest, then click.
async function click(page, target) {
  const el = target.first();
  await el.waitFor({ state: "visible" });
  const outside = await el.evaluate((n) => {
    const r = n.getBoundingClientRect();
    return r.top < 90 || r.bottom > innerHeight - 90;
  });
  if (outside) await look(el, 100);
  const box = await el.boundingBox();
  const to = { x: box.x + Math.min(box.width / 2, 120), y: box.y + box.height / 2 };
  const steps = 28;
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const e = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2; // ease in and out
    await page.mouse.move(mouse.x + (to.x - mouse.x) * e, mouse.y + (to.y - mouse.y) * e);
    await pause(14);
  }
  mouse = to;
  await pause(PACE.beforeClick);
  await page.mouse.down();
  await pause(90);
  await page.mouse.up();
}

// Click a button that sends a form, and wait for the next page to arrive.
async function submit(page, target, ms = PACE.read) {
  await Promise.all([page.waitForNavigation(), click(page, target)]);
  await pause(ms);
}

// Click into a text box and type, one letter at a time.
async function type(page, target, text) {
  await click(page, target);
  await target.first().pressSequentially(text, { delay: PACE.key });
  await pause(500);
}

// One answer inside a decision form: the label wrapping the radio button or checkbox.
const option = (scope, inputSelector) => scope.locator(`label:has(${inputSelector})`);

// The review status page reloads itself while "AI" works. Wait there until the button for the
// next step appears, then press it.
async function waitThenContinue(page, step) {
  const next = page.locator(`a.btn[href$="/${step}"]`);
  await next.waitFor({ state: "visible", timeout: 60_000 });
  await pause(PACE.read);
  await submit(page, next);
}

// ---------------------------------------------------------------------------------------------
// 4. The story
// ---------------------------------------------------------------------------------------------
async function story(page) {
  // Sign in as the compliance specialist.
  await page.goto("/sign-in");
  await pause(3200); // let the opening animation play
  await submit(page, page.getByRole("button", { name: /compliance specialist/ }));

  // Start a review, with the demo rule switched on.
  await click(page, option(page, 'input[name="demo_planted_row"]'));
  await pause(PACE.glance);
  await submit(page, page.getByRole("button", { name: "Start a new review" }), 0);

  // Step 1: "AI" drafts the rules (stand-in). Then step 2: check the rules.
  await waitThenContinue(page, "g1");
  await look(page.locator("#index-h"), PACE.read);

  // Rules 1 to 3: approve. Rule 1's source does not say who files, so the specialist chooses.
  const approve = async (i, weekendRule, whoFiles) => {
    const card = page.locator(`#row-${i}`);
    await look(card.locator("h2"), PACE.read);
    await click(page, option(card, 'input[data-answer="approve"]'));
    await click(page, option(card, `input[name="business_day_rule"][value="${weekendRule}"]`));
    if (whoFiles) await click(page, option(card, `input[name="who_files"][value="${whoFiles}"]`));
    await pause(PACE.glance);
    await submit(page, card.getByRole("button", { name: "Approve rule" }), PACE.glance);
  };
  await approve(1, "roll_forward", "AIFM");
  await approve(2, "roll_forward");
  await approve(3, "no_roll");

  // Rule 4 is the demo rule: reject it with a reason.
  // TODO after block B7: the server will refuse to approve this rule. Film that first (choose
  // Approve, press "Approve rule", pause on the refusal), then reject. Today the server would
  // approve it (backend/services/decisions.py says the refusal is "not here yet"), so the film
  // must not press Approve here.
  const demo = page.locator("#row-4");
  await look(demo.locator("h2"), 2600);
  await click(page, option(demo, 'input[data-answer="reject"]'));
  await type(page, demo.locator('textarea[name="reject_reason"]'), "The quote doesn't support this rule.");
  await submit(page, demo.getByRole("button", { name: "Reject rule" }));

  // Finish step 2.
  await look(page.locator("#finish"), PACE.glance);
  await submit(page, page.getByRole("button", { name: "Finish checking" }), 0);

  // Step 3: confirm which rules apply to this fund.
  await waitThenContinue(page, "g2");
  const answers = await page.locator("article.rule-card").count();
  for (let i = 1; i <= answers; i++) {
    const card = page.locator(`#verdict-${i}`);
    await look(card.locator("h2"), PACE.read);
    if (await card.locator('input[data-answer="add"]').count()) {
      // "AI" could not tell: add it, marked "May not be required", and say why.
      await click(page, option(card, 'input[data-answer="add"]'));
      await type(page, card.locator('textarea[name="decide_reason"]'), "Not confirmed in the fund's records yet.");
      await submit(page, card.getByRole("button", { name: "Add to the calendar" }), PACE.glance);
    } else {
      await click(page, option(card, 'input[data-answer="confirm"]'));
      await pause(PACE.glance);
      await submit(page, card.getByRole("button", { name: /^Confirm/ }), PACE.glance);
    }
  }
  await look(page.locator("#finish"), PACE.glance);
  await submit(page, page.getByRole("button", { name: "Finish and calculate dates" }), 0);

  // Step 4: read the calendar and what was left out, acknowledge, publish.
  await waitThenContinue(page, "g3");
  await look(page.locator("#cal-h"), PACE.read);
  await look(page.locator("#left-out-h"), 2600);
  const publish = page.locator("form.decision");
  await look(publish, PACE.glance);
  await click(page, option(publish, 'input[data-answer="publish"]'));
  await pause(PACE.read);
  await click(page, option(publish, 'input[name="acknowledged"]'));
  await pause(PACE.glance);
  await submit(page, publish.getByRole("button", { name: "Publish calendar" }), 2600);

  // Sign out, then sign in as the General Partner: read-only calendar, three views.
  await submit(page, page.getByRole("button", { name: "Sign out" }));
  await submit(page, page.getByRole("button", { name: /General Partner/ }), 2600);
  await look(page.locator("#entries"), PACE.read);
  await click(page, page.locator("label:has(#v-list)"));
  await pause(2600);
  await click(page, page.locator("label:has(#v-year)"));
  await pause(3200);
}

// ---------------------------------------------------------------------------------------------
// 5. Film it
// ---------------------------------------------------------------------------------------------
mkdirSync(OUT_DIR, { recursive: true });
const { server, dbDir } = await startApp();
const browser = await chromium.launch();
let failed = null;
try {
  const context = await browser.newContext({
    baseURL: BASE,
    viewport: SIZE,
    recordVideo: { dir: OUT_DIR, size: SIZE }, // this line is what makes the browser film itself
    colorScheme: "light",
    locale: "en-GB",
  });
  await context.addInitScript(drawCursor);
  const page = await context.newPage();
  try {
    await story(page);
  } catch (error) {
    failed = error;
    await page.screenshot({ path: join(OUT_DIR, "where-it-stopped.png") });
  }
  await context.close(); // the film is written to disk when the browser session closes
  await page.video().saveAs(join(OUT_DIR, "demo-raw.webm"));
  await page.video().delete(); // remove the copy with a random name
} finally {
  await browser.close();
  server.kill();
  rmSync(dbDir, { recursive: true, force: true });
}

if (failed) {
  console.error(`\nThe story stopped early: ${failed.message}\nSee docs/demo-video/where-it-stopped.png`);
  process.exit(1);
}

// Convert to .mp4 (plays everywhere: Keynote, websites, QuickTime). Needs ffmpeg; skipped without it.
const mp4 = join(OUT_DIR, "demo.mp4");
const ff = spawnSync("ffmpeg", [
  "-y", "-loglevel", "error", "-i", join(OUT_DIR, "demo-raw.webm"),
  "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4,
]);
console.log(ff.status === 0 ? `\nSaved ${mp4}` : "\nSaved docs/demo-video/demo-raw.webm (ffmpeg not found, so no .mp4)");
