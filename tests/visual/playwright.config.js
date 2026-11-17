// Playwright Test config for the visual snapshots (visual-regression skill, frontend.md §8 D-6).
// Run from tests/visual/:  npm run test:visual
// It starts the real app itself, on its own port and a fresh database, with stand-in agents and
// no pause, so every run starts from the same nothing. No model is ever called.
import { defineConfig, devices } from "@playwright/test";

const PORT = 8777;

export default defineConfig({
  testDir: ".",
  testMatch: "visual.spec.js",
  fullyParallel: false,
  workers: 1, // the spec is one story told in order (sign in, start, decide, publish)
  retries: 0,
  // Proposal mode (npm run test:visual:candidates): write every picture into candidates/ (git-ignored)
  // instead of the baseline folder, so a refresh can be proposed with all images to look at and the
  // approved baselines are never overwritten by a run. Approved images are then copied over by hand.
  ...(process.env.VR_CANDIDATES ? { snapshotPathTemplate: "candidates/{arg}{ext}" } : {}),
  reporter: [["list"], ["html", { open: "never" }]],
  expect: {
    toHaveScreenshot: {
      // A one-pixel antialias difference must not fail; a real layout shift must.
      maxDiffPixels: 150,
      threshold: 0.2,
      animations: "disabled", // finite animations jump to their end state
      caret: "hide",
    },
  },
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    // Chromium only, recorded in ux-review.md. Snapshot files carry the platform name
    // (…-darwin.png), so a run on another OS makes its own and does not compare against these.
    ...devices["Desktop Chrome"],
    colorScheme: "light",
    locale: "en-GB",
  },
  projects: [{ name: "chromium" }],
  webServer: {
    // A fresh database every run: the folder is deleted, then the app creates it again.
    command:
      "rm -rf tests/visual/.tmp && mkdir -p tests/visual/.tmp && " +
      `.venv/bin/python -m uvicorn backend.main:create_app --factory --port ${PORT}`,
    cwd: "../..",
    url: `http://127.0.0.1:${PORT}/health`,
    reuseExistingServer: false,
    timeout: 30_000,
    env: {
      AGENTS_MODE: "stand_in",
      STAND_IN_UNIT_PAUSE_S: "0",
      SESSION_SECRET: "visual-regression-only",
      DATABASE_PATH: "tests/visual/.tmp/visual.db",
    },
  },
});
