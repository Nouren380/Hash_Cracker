# Hash Cracker

A local security-training tool for recovering a hash using a dictionary attack.
Only use it in authorized labs. It supports hexadecimal MD5, SHA-1, SHA-256 and SHA-512.

## Run

Python 3.10+ is required. From the repository root:

```sh
python -m pip install -r requirements.txt
python interface/app.py
```

Open http://127.0.0.1:5000. The real Flask application uses `Core/password_list.txt` and stores sessions in `Database/hash_cracker.db` (created automatically and ignored by Git). Set `HASH_CRACKER_WORDLIST` or `HASH_CRACKER_DB` to use alternative local paths. Recovered passwords and session details are stored in SQLite; keep the database private. New attacks do not record individual candidates. Older databases may still contain candidate logs. History can be cleared from the History page, deleting sessions, recovered values, associated old candidate logs and report totals; the action is blocked while an attack is active.

Try MD5 `e10adc3949ba59abbe56e057f20f883e` using the supplied list. The supplied wordlist contains 50,000 distinct entries, including generated case and suffix variations of existing entries. A dictionary attack only finds values present in its wordlist; a missing match does not prove the original value is strong.

The separate `interface/frontend-demo/dev_server.py` and `?mode=mock` are for mock frontend testing; they do not use the real engine. The real app handles attacks synchronously, streams the wordlist and does not provide real-time progress or cancellation. The frontend does not impose a fixed timeout on an attack; if the connection breaks, the server task may still continue. Check History before retrying. The Flask development server binds to localhost and is intended for local training, not public deployment.

## Tests

```sh
python -m unittest Database.test_db_manager Database.test_integration -v
```
