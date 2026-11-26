> This directory also contains a standalone mock server. For the integrated app, run `python interface/app.py` from the repository root; see the root README.

# Hash Cracker — Frontend

This is the Frontend only. It is built with Flask/Jinja2 templates, vanilla CSS, and vanilla
JavaScript, and is meant to be dropped into the team's Flask project (the real `app.py`,
hash-cracking engine, wordlist, and database are owned by other teammates and are not part of
this delivery).

Dictionary Attack is the only attack method anywhere in this project. Brute Force has been
fully removed, and the Wordlist is never exposed to the Frontend — see `API_CONTRACT.md` for
exactly what the Frontend sends and expects back.

## Folder structure

```
hash-cracker-frontend/
  templates/        Jinja2 page templates
  static/css/        One shared stylesheet
  static/js/          UI logic, split by page, plus a centralized API module
  docs/                This documentation set
  dev_server.py       A small Flask app for running and testing the Frontend locally
```

`dev_server.py` is **not** the team's real Backend. It is a temporary, Frontend-only test
harness: it renders the templates and serves a few mock `/api/...` endpoints backed by an
in-memory dictionary, so the pages and the API module can be exercised end to end before the
real Backend exists. When the real `app.py` is ready, its routes should render the same
templates in `templates/` with the same variables (see "What each route must provide" below),
and the Backend's real endpoints should replace the mock ones at the paths in
`API_CONTRACT.md`. Nothing in `templates/`, `static/css/`, or `static/js/` needs to change for
that swap.

## Running it locally

Requirements: Python 3.9+ and Flask (`pip install flask`).

```bash
cd hash-cracker-frontend
python3 dev_server.py
```

Then open `http://127.0.0.1:5000/` in a browser.

- By default every page talks to the mock `/api/...` endpoints built into `dev_server.py`
  (status: `live` mode, pointed at a stand-in Backend).
- Appending `?mode=mock` to any page URL (for example `http://127.0.0.1:5000/crack?mode=mock`)
  switches the page to the JavaScript-only mock in `static/js/mock-api.js`, with no network
  calls at all. This is for testing the Frontend in complete isolation from any server-side
  code.

Two known test hashes are wired into both mock paths for convenience:

| Hash (MD5) | Password |
|---|---|
| `5f4dcc3b5aa765d61d8327deb882cf99` | `password` |
| `e10adc3949ba59abbe56e057f20f883e` | `123456` |

Any other well-formed MD5 hash will correctly come back as not found.

## What each route must provide (for the real `app.py`)

| Route | Template | Template variables used |
|---|---|---|
| `/` | `dashboard.html` | `algorithms`, `stats` (pass `None` until real statistics exist) |
| `/crack` | `crack.html` | `algorithms` |
| `/results` | `results.html` | `algorithms` |
| `/history` | `history.html` | `algorithms` |
| `/reports` | `reports.html` | `algorithms` |
| `/settings` | `settings.html` | `algorithms` |

`algorithms` is a list of `{"id": ..., "label": ...}` dicts, matching
`static/js/algorithms.js`. Every route should also pass `active_page` (one of `dashboard`,
`crack`, `results`, `history`, `reports`, `settings`) so the sidebar highlights correctly — see
how `dev_server.py` does this.

## Backend-dependent features

These are built and testable with mock data, but cannot be fully verified until the real
Backend and API are connected:

- Real Dictionary Attack results (only a two-entry in-memory dictionary is simulated here).
- Persistent History (the mock endpoint always reports `backendConnected: false`).
- Real Reports content and numbers.
- Algorithm detection is simulated in the mock server.

See `TESTING_REPORT.md` for exactly what was tested and how.

## Redesigned interface

The primary navigation focuses on Dashboard, Crack a hash, and Results. History and Reports are available when the integrated backend is used. Settings remains outside the main navigation.
The development server and JavaScript-only mock show a demo notice; neither connects to the real
cracking engine. The backend selects one supported algorithm using the hash length. Other algorithms can share a length, so the result is a best-effort assumption.
The copy button uses the browser clipboard where available. Processing feedback is indeterminate:
the draft backend contract does not supply live progress or a cancellation endpoint.
