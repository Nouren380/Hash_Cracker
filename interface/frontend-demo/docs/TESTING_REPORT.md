# Testing Report

Testing was performed against a running instance of `dev_server.py` on
`http://127.0.0.1:5000`, using real HTTP requests (`curl`) and a real headless browser
(Playwright/Chromium driving the actual pages, not just reading the source). This is Frontend
and mock-data testing only — see "Not yet tested" below for what needs the real Backend.

## 1. Pages load correctly

All six routes and every static asset returned `200 OK`:

| Path | Result |
|---|---|
| `/` (Dashboard) | 200 |
| `/crack` | 200 |
| `/results` | 200 |
| `/history` | 200 |
| `/reports` | 200 |
| `/settings` | 200 |
| `/static/css/style.css` | 200 |
| `/static/js/*.js` (all 9 files) | 200 |

## 2. Navigation

Followed sidebar links across all six pages in the browser; each one loads the correct page
and highlights the correct sidebar item.

## 3. Responsive layout

Checked `/` at three viewport widths with Playwright and asserted no horizontal scroll:

| Viewport | Result |
|---|---|
| 1440×900 (desktop) | Pass — no overflow |
| 768×1024 (tablet) | Pass — no overflow |
| 390×844 (mobile) | Pass — no overflow, sidebar collapses to a horizontal tab bar |

## 4. Hash input accepts valid input

Submitted a well-formed 32-character MD5 hash with MD5 selected — accepted, request sent,
redirected to Results. Pass.

## 5. Empty hash is rejected

Submitted the form with the hash field empty. Blocked client-side with "Enter a hash value."
No request was sent. Pass.

## 6. Whitespace-only input is rejected

Submitted three spaces as the hash. Blocked client-side with "The hash cannot be whitespace
only." Pass.

## 7. Algorithm dropdown works

Selecting each of MD5 / SHA-1 / SHA-256 / SHA-512 changes the active format check (confirmed by
submitting a non-hex value and seeing the error message name the selected algorithm). Pass.

## 8. Only Dictionary Attack is available

The attack-method area of the Crack page is a locked, non-interactive label reading
"Dictionary Attack" — there is no dropdown and no other method can be selected. Pass.

## 9. No Brute Force functionality remains

Searched every template, stylesheet, script, and the dev server for the word "brute" —
zero matches anywhere in the project. Confirmed in the rendered `/crack` page's HTML and
in the algorithm/attack-method logic. Pass.

## 10/11. No Wordlist upload, selection, or exposed information

Searched the rendered HTML of every page for any Wordlist control (upload input, dropdown,
filename, path, or ID). None exist. The two sentences that mention "wordlist" in
`crack.html`/`dashboard.html` are explanatory text telling the user the wordlist is internal to
the Backend — not a control, and no wordlist identifier is ever sent in a request body. Pass.

## 12. Loading indicators work

On submit, the button gains a spinner and becomes disabled for the duration of the mock
network delay, then returns to normal. Verified both the "found" and "not found" paths. Pass.

## 13. Duplicate submissions are prevented

Clicked submit and confirmed the button was `disabled` before the request resolved, so a second
click cannot fire a second request while one is in flight. Pass.

## 14. API failures are handled correctly

Used Playwright request interception to force the `/api/crack` call to fail outright (simulated
network failure). Result: an error banner reading "Could not reach the server. Check that the
Backend is running." appeared, and the submit button was re-enabled afterwards rather than left
stuck. Pass.

## 15. Results are displayed correctly using controlled mock responses

- Known hash (`5f4dcc3b5aa765d61d8327deb882cf99`, MD5) → Results page shows state "Password
  found" and password `password`. Pass.
- Unknown hash (`ffffffff...`, MD5) → Results page shows state "Not found" and "Not recovered".
  Pass.
- Visiting `/results` directly with nothing submitted yet shows the "No result to show yet"
  empty state rather than a blank or broken page. Pass.

## 16. No JavaScript console errors

Captured browser console and page errors across the full test run (page loads, form
submissions, navigation, both "live" and `?mode=mock` paths). Zero console errors or page
errors. Pass.

## 17. No missing files or broken asset references

Every CSS and JS reference resolved to a real, served file (see section 1); no 404s were logged
for any asset during the full test run.

## 18. No unexpected errors navigating between pages

Navigated Dashboard → Crack → Results → History → Reports → Settings → Crack repeatedly,
including after a failed and a successful submission. No crashes, no uncaught exceptions.

## Also tested beyond the checklist

- End-to-end flow fully isolated from any server (`?mode=mock`, using only
  `static/js/mock-api.js`): submit → redirect → correct result shown. Pass.
- Settings page toggles persist their pressed state and write to `localStorage`. Pass.
- History and Reports pages render their mock data correctly and show the
  "Backend has not confirmed persistent storage" banner when `backendConnected` is `false`.
  Pass.

## Not yet tested — requires the real Backend

- Real Dictionary Attack timing and results against a real wordlist.
- Real persistence of History records across a server restart.
- The real, final algorithm list and any format quirks specific to algorithms the Backend
  actually supports.
- Behavior under the Backend's real error responses (this report only verifies the Frontend
  correctly displays whatever `error.message` it is given, and correctly handles a totally
  unreachable server).

No claim is made above that functionality depending on the real Backend works — only that the
Frontend behaves correctly against the documented contract and mock data.
