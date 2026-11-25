# Hash Cracker — Frontend/Backend API Contract

Status: **draft, not yet confirmed by the Backend team.** The Frontend is built against this
contract. The endpoint paths, field names, and base URL below are proposals, isolated in
`static/js/api.js`, so the Backend team can change them with a one-file edit on the Frontend side.

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
{
  "hash": "5f4dcc3b5aa765d61d8327deb882cf99",
  "algorithm": "md5"
}
```

| Field | Type | Notes |
|---|---|---|
| `hash` | string | Trimmed, non-empty, no internal whitespace. |
| `algorithm` | string | One of the IDs in `static/js/algorithms.js` (`md5`, `sha1`, `sha256`, `sha512`). **Awaiting Backend confirmation of the real supported list.** |

The Frontend never sends a wordlist name, path, or ID, and never sends a Brute Force field —
Dictionary Attack against the Backend's own configured wordlist is the only attack method.

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

## What the Backend team needs to confirm or provide

1. The real, final list of supported hash algorithms and their IDs — `static/js/algorithms.js`
   is a centralized placeholder marked `confirmedByBackend: false` until this is confirmed.
2. The real base URL / path prefix for the API in production (currently assumed to be `/api`
   on the same origin as the Flask templates).
3. Whether `durationMs` and `backendConnected` will actually be populated, or should be removed
   from the contract.
4. The exact wording and structure of `error.message` for validation failures versus genuine
   server/engine errors, so the Frontend can tell them apart if that distinction matters later.
5. Confirmation that the Wordlist never needs to appear in any request — this contract assumes
   it stays entirely internal to the Backend.

## What the Frontend will not do

- It will not implement hash-cracking logic client-side.
- It will not expose Wordlist selection, upload, or configuration anywhere in the UI or API
  payloads.
- It will not offer a Brute Force option anywhere.

## Clear saved history (integrated local app)

`DELETE /api/history` deletes saved sessions, recovered values and associated candidate logs. Reports based on those sessions change as a result. It returns `{"deleted": 3}` on success or HTTP 409 if an attack is pending or running. The UI asks for confirmation before issuing this request. The JavaScript-only mock does not support deletion.

Real attacks stream the wordlist without recording individual candidates; old candidate logs are removed when their sessions are cleared. The integrated app handles attacks synchronously, so interrupted connections can leave a server task running.
