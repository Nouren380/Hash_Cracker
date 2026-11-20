-- Hash Cracker Database Schema

CREATE TABLE IF NOT EXISTS hash_algorithms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    hash_length INTEGER NOT NULL UNIQUE,
    description TEXT
);

INSERT OR IGNORE INTO hash_algorithms
(name, hash_length, description) VALUES
('MD5', 32, 'Message Digest 5'),
('SHA-1', 40, 'Secure Hash Algorithm 1'),
('SHA-256', 64, 'Secure Hash Algorithm 256-bit'),
('SHA-512', 128, 'Secure Hash Algorithm 512-bit');


CREATE TABLE IF NOT EXISTS wordlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    word_count INTEGER DEFAULT 0,
    added_at TEXT DEFAULT (datetime('now'))
);


CREATE TABLE IF NOT EXISTS cracking_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_hash TEXT NOT NULL,
    detected_algorithm_id INTEGER REFERENCES hash_algorithms(id),
    selected_algorithm_id INTEGER REFERENCES hash_algorithms(id),
    wordlist_id INTEGER REFERENCES wordlists(id),

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending',
            'invalid_hash',
            'unsupported_algorithm',
            'wordlist_not_found',
            'running',
            'found',
            'not_found'
        )),

    cracked_password TEXT,
    started_at TEXT DEFAULT (datetime('now')),
    finished_at TEXT,
    attempts_count INTEGER DEFAULT 0
);


CREATE TABLE IF NOT EXISTS attempts_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL
        REFERENCES cracking_sessions(id) ON DELETE CASCADE,
    candidate_word TEXT NOT NULL,
    generated_hash TEXT NOT NULL,
    is_match INTEGER NOT NULL DEFAULT 0,
    attempt_order INTEGER NOT NULL,
    tried_at TEXT DEFAULT (datetime('now'))
);


CREATE INDEX IF NOT EXISTS idx_sessions_status
ON cracking_sessions(status);

CREATE INDEX IF NOT EXISTS idx_attempts_session
ON attempts_log(session_id);
