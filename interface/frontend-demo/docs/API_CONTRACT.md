# Hash Cracker — Frontend/Backend API Contract

This document describes the integrated Flask API and the standalone frontend mock.

All requests are made from `static/js/api.js`. No other Frontend file talks to the network
directly.

Base URL: configurable. Defaults to `/api`. Can be overridden by setting
`window.HASH_CRACKER_API_BASE` before the page's scripts load (for example from a Jinja
template if the Backend is served from a different origin).

## 1. Submit a hash for cracking

```
POST /api/crack
Content-Type: application/json
```

### Request body

```json
{ "hash": "5f4dcc3b5aa765d61d8327deb882cf99" }
```

The frontend sends only the hash. The backend validates hexadecimal characters and selects
one supported algorithm by length: 32 for MD5, 40 for SHA-1, 64 for SHA-256, and 128 for
SHA-512. This is a best-effort assumption: other algorithms can share these lengths. The
returned `algorithm` is the one actually tested, not definitive identification. Unsupported
formats and lengths receive HTTP 400. The wordlist and attack method stay on the backend.

### Expected success response — `200 OK`

```json
{
  "hash": "5f4dcc3b5aa765d61d8327deb882cf99",
  "algorithm": "md5",
  "status": "found",
  "password": "password",
  "durationMs": 410
}
```

| Field | Type | Notes |
|---|---|---|
| `status` | string | One of `found`, `not_found`, `processing`, `error`. |
| `password` | string or null | `null` when not found. |
| `durationMs` | number or omitted | Processing time, if the Backend tracks it. The Frontend shows "Not reported by Backend" when absent. |

### Expected error response — `4xx` / `5xx`

```json
{
  "error": {
    "message": "A human-readable explanation of what went wrong."
  }
}
```

The Frontend shows `error.message` directly to the user, with no fabricated text of its own,
and treats any non-2xx response as a failure.

## 2. Fetch submission history

```
GET /api/history
```

### Expected response — `200 OK`

```json
{
  "records": [
    {
      "id": "h1",
      "hash": "5f4dcc3b5aa765d61d8327deb882cf99",
      "algorithm": "md5",
      "status": "found",
      "password": "password",
      "submittedAt": "2026-11-10T09:14:00Z"
    }
  ],
  "backendConnected": true
}
```

`backendConnected` tells the Frontend whether these records are backed by persistent storage.
When `false`, the History page shows a banner warning that records may not be durable. If the
Backend has no persistence layer yet, it is fine to always return `false` here.

## 3. Fetch reports

```
GET /api/reports
```

### Expected response — `200 OK`

```json
{
  "reports": [
    {
      "id": "r1",
      "title": "Weekly cracking summary",
      "generatedAt": "2026-11-09T00:00:00Z",
      "totalJobs": 2,
      "totalFound": 1
    }
  ],
  "backendConnected": true
}
```

## Integration notes

The integrated backend supports MD5, SHA-1, SHA-256 and SHA-512. It determines the algorithm
to test from the hexadecimal hash length. The API base defaults to `/api`, and the wordlist
remains configured on the backend. Live progress and cancellation are not currently provided.

## What the Frontend will not do

- It will not implement hash-cracking logic client-side.
- It will not expose Wordlist selection, upload, or configuration anywhere in the UI or API
  payloads.
- It will not offer a Brute Force option anywhere.

## Clear saved history (integrated local app)

`DELETE /api/history` deletes saved sessions, recovered values and associated candidate logs. Reports based on those sessions change as a result. It returns `{"deleted": 3}` on success or HTTP 409 if an attack is pending or running. The UI asks for confirmation before issuing this request. The JavaScript-only mock does not support deletion.

Real attacks stream the wordlist without recording individual candidates; old candidate logs are removed when their sessions are cleared. The integrated app handles attacks synchronously, so interrupted connections can leave a server task running.
