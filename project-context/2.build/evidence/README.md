# UI evidence: screenshots of the stubbed UI

Screenshots for `project-context/2.build/ux-review.md`. Taken on **17 Nov 2026** by
`@frontend.eng` from the real app on branch `frontend-spec` (stand-in agents, no model call, mock
data only: the fund and the firm are fictional). Rendered with headless Chrome 157.

The pages were saved as the server rendered them and shown with the app's own stylesheet. Two
things look different from a browser session: a review is named by its run ID ("Review
RUN-20261117-1") until H-036 sends the review number, and some fields are empty until H-036 and
B2 land (`frontend.md` §11).

Real-name scan run on this folder and on the HTML the images were taken from: nothing found.

| File | Page (ux.md) | State | Width |
|---|---|---|---|
| `01-sign-in-1280.png` | 1 · Sign-in | Two panels: the portfolio panel (H-037) and the sign-in box | 1280 px |
| `01-sign-in-narrow-800.png` | 1 · Sign-in | Narrow screen: the panels stacked, the charts hidden | 800 px (inside a frame) |
| `17-filing-rules-populated-1280.png` | 2 · Filing rules | Three reviews (published, failed, abandoned); start form | 1280 px |
| `04b-running-still-1280.png` | 3 · Review status | AI drafting, units filling in one by one, "Last updated at …" | 1280 px |
| `07-review-status-your-turn-1024.png` | 3 · Review status | Your turn: check the rules; sidebar beside the content at 1024 px | 1024 px |
| `08-check-rules-1280.png` | 4 · Check the rules | At step 2: summary cards, rule index, answer-first form | 1280 px |
| `10-confirm-applies-1280.png` | 5 · Confirm what applies | At step 3: "can't tell" first in the index, answer cards | 1280 px |
| `11-publish-1280.png` | 6 · Check the calendar and publish | At step 4: calendar, marks, the publish form | 1280 px |
| `12-review-status-published-1280.png` | 3 · Review status | Published | 1280 px |
| `13-gp-calendar-1280.png` | 7 · Calendar | Published, as the General Partner | 1280 px |
| `13-gp-calendar-phone-600.png` | 7 · Calendar | Published, as the General Partner, at phone width: the page is the 360 px frame on the left; the grey strip is outside it | 360 px (inside a 600 px image) |
| `16-review-status-failed-1280.png` | 3 · Review status | Failed (failure demo), the "Without Retry" page | 1280 px |
| `15-403-1280.png` | §1.7 · No access | The General Partner on a specialist page | 1280 px |

`04b-running-still` is the running page with its 3-second reload removed, so the browser could take
a still picture; nothing else differs.

## Keyboard pass recording

| File | What it shows | Size |
|---|---|---|
| `keyboard-pass-2026-11-17.gif` | The keyboard pass in the operator's own Chrome (Claude in Chrome, 17 Nov 2026), keyboard only: sign in, skip link, start a review with the demo rule, "Stop automatic refresh" as the first Tab stop while AI works, approve rule 1 (weekend option and who files), switch rule 2 to Reject with the right arrow, type a reason, "Reject rule". 41 frames, 960 px wide, shrunk from 5.5 MB | 1.2 MB |

The black labels name each key press. One step shows "Pressed key: ArrowRight" with no change on
screen: the browser tool expected the name "Right", so that key press never reached the page. The
next attempt, with "Right", switches the answer to Reject as it should (`ux-review.md`, M-001).
