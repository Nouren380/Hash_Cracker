-- =============================================================================
-- Hash Cracker - Production SQLite Database Schema
-- Mariam Ashraf Adam
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 1. Supported Cryptographic Hash Algorithms
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hash_algorithms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    hash_length INTEGER NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Seed predefined supported algorithms
INSERT OR IGNORE INTO hash_algorithms (name, hash_length, description) VALUES
('MD5', 32, 'Message Digest 5 (128-bit)'),
('SHA-1', 40, 'Secure Hash Algorithm 1 (160-bit)'),
('SHA-256', 64, 'Secure Hash Algorithm 256-bit'),
('SHA-512', 128, 'Secure Hash Algorithm 512-bit');

-- -----------------------------------------------------------------------------
-- 2. Wordlists Metadata Registry
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wordlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    word_count INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    added_at TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------------------------
-- 3. Cracking Sessions Tracking
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cracking_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_hash TEXT NOT NULL,
    detected_algorithm_id INTEGER REFERENCES hash_algorithms(id) ON DELETE SET NULL,
    selected_algorithm_id INTEGER REFERENCES hash_algorithms(id) ON DELETE SET NULL,
    wordlist_id INTEGER REFERENCES wordlists(id) ON DELETE SET NULL,
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
    duration_ms REAL DEFAULT 0,
    attempts_count INTEGER DEFAULT 0,
    started_at TEXT DEFAULT (datetime('now')),
    finished_at TEXT
);

-- -----------------------------------------------------------------------------
-- 4. Dictionary Attack Candidate Log
-- -----------------------------------------------------------------------------
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

-- -----------------------------------------------------------------------------
-- 5. Performance Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_sessions_status ON cracking_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_target_hash ON cracking_sessions(target_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON cracking_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts_log(session_id);
CREATE INDEX IF NOT EXISTS idx_attempts_order ON attempts_log(session_id, attempt_order);

-- -----------------------------------------------------------------------------
-- 6. Analytical Summary Views for Dashboard & Reporting
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_session_summary AS
SELECT 
    cs.id,
    cs.target_hash,
    COALESCE(sa.name, da.name, 'UNKNOWN') AS algorithm,
    cs.status,
    cs.cracked_password,
    cs.duration_ms,
    cs.attempts_count,
    cs.started_at,
    cs.finished_at,
    w.name AS wordlist_name,
    w.file_path AS wordlist_path
FROM cracking_sessions cs
LEFT JOIN hash_algorithms sa ON cs.selected_algorithm_id = sa.id
LEFT JOIN hash_algorithms da ON cs.detected_algorithm_id = da.id
LEFT JOIN wordlists w ON cs.wordlist_id = w.id;
