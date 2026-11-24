// Helpers shared by the visual specs (visual.spec.js and evaluation.spec.js).
// Moved here unchanged from visual.spec.js so the two specs normalise and photograph pages the same way.
import { expect } from "@playwright/test";
import { fileURLToPath } from "node:url";

// Every browser session in this test gets the same font stylesheet (fonts.css, a pinned copy of
// Google's usual answer), because Google sometimes serves on-the-fly font builds that render text
// slightly differently and made the screenshots flaky (ux-review M-012). The app is unchanged.
const PINNED_FONTS_CSS = fileURLToPath(new URL("./fonts.css", import.meta.url));
export async function newSession(browser) {
  const context = await browser.newContext();
  await context.route(/fonts\.googleapis\.com\/css2/, (route) =>
    route.fulfill({ path: PINNED_FONTS_CSS, contentType: "text/css" }));
  return context;
}

// Values that change every run (run IDs carry today's date; start, publish and "Last updated"
// times) are replaced with fixed placeholders in the page, just before the picture. Nothing in
// the app changes; this only touches the copy of the page in the test browser.
export async function normalise(page) {
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

export async function snap(page, name, widths) {
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await expect.soft(page).toHaveScreenshot(`${name}-${width}.png`, { fullPage: true });
  }
}

// Open a page, wait until it shows what we expect (the stand-in stages finish in the background),
// then normalise it.
export async function open(page, path, ready) {
  await expect(async () => {
    await page.goto(path);
    await expect(page.locator(ready).first()).toBeVisible({ timeout: 1000 });
  }).toPass({ timeout: 20_000 });
  await normalise(page);
}

export const form = (page, path, data) => page.request.post(path, { form: data });
