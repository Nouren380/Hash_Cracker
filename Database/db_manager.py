"""
Hash Cracker - Database Management Subsystem
Module: Database/db_manager.py
Author: Rashad Sameh

Provides high-performance SQLite operations, session tracking,
attempt logging, and analytical query helpers for the Hash Cracker application.
"""

import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "hash_cracker.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


class DBManager:
    """
    Manages SQLite database connections, schemas, sessions,
    and attack logging for the Hash Cracker project.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        # check_same_thread=False allows safe sharing across Flask worker threads
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # -------------------------------------------------------------------------
    # Schema Initialization
    # -------------------------------------------------------------------------
    def _init_schema(self) -> None:
        """
        Initializes the database schema from schema.sql if available,
        falling back to embedded DDL script.
        """
        if os.path.exists(SCHEMA_PATH):
            try:
                with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
                    schema_sql = schema_file.read()
                self.conn.executescript(schema_sql)
                self.conn.commit()
                return
            except Exception:
                # Fallback to embedded script if file reading encounters issues
                pass

        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS hash_algorithms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                hash_length INTEGER NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            INSERT OR IGNORE INTO hash_algorithms (name, hash_length, description) VALUES
            ('MD5', 32, 'Message Digest 5 (128-bit)'),
            ('SHA-1', 40, 'Secure Hash Algorithm 1 (160-bit)'),
            ('SHA-256', 64, 'Secure Hash Algorithm 256-bit'),
            ('SHA-512', 128, 'Secure Hash Algorithm 512-bit');

            CREATE TABLE IF NOT EXISTS wordlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                word_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                added_at TEXT DEFAULT (datetime('now'))
            );

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

            CREATE INDEX IF NOT EXISTS idx_sessions_status ON cracking_sessions(status);
            CREATE INDEX IF NOT EXISTS idx_sessions_target_hash ON cracking_sessions(target_hash);
            CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON cracking_sessions(started_at);
            CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts_log(session_id);
            CREATE INDEX IF NOT EXISTS idx_attempts_order ON attempts_log(session_id, attempt_order);

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
        """)
        self.conn.commit()

    # -------------------------------------------------------------------------
    # Algorithm Management
    # -------------------------------------------------------------------------
    def get_algorithm_by_length(self, length: int) -> Optional[sqlite3.Row]:
        """Fetch algorithm by standard hexadecimal digest character length."""
        return self.conn.execute(
            "SELECT * FROM hash_algorithms WHERE hash_length = ?",
            (length,)
        ).fetchone()

    def get_algorithm_by_name(self, name: str) -> Optional[sqlite3.Row]:
        """Fetch algorithm record by name (case-insensitive)."""
        return self.conn.execute(
            "SELECT * FROM hash_algorithms WHERE UPPER(name) = UPPER(?)",
            (name.strip(),)
        ).fetchone()

    def get_all_algorithms(self) -> List[sqlite3.Row]:
        """Retrieve all supported hash algorithms."""
        return self.conn.execute(
            "SELECT * FROM hash_algorithms ORDER BY hash_length ASC"
        ).fetchall()

    # -------------------------------------------------------------------------
    # Wordlist Management
    # -------------------------------------------------------------------------
    def add_wordlist(self, name: str, file_path: str, word_count: int = 0) -> int:
        """
        Register or update a wordlist file in the database.
        If file_path already exists, updates its name and word_count.
        """
        self.conn.execute(
            """INSERT INTO wordlists (name, file_path, word_count)
               VALUES (?, ?, ?)
               ON CONFLICT(file_path) DO UPDATE SET
                   name = excluded.name,
                   word_count = CASE WHEN excluded.word_count > 0 THEN excluded.word_count ELSE wordlists.word_count END""",
            (name, file_path, word_count)
        )
        self.conn.commit()

        row = self.conn.execute(
            "SELECT id FROM wordlists WHERE file_path = ?",
            (file_path,)
        ).fetchone()

        return row["id"] if row else 0

    def get_wordlist_by_id(self, wordlist_id: int) -> Optional[sqlite3.Row]:
        """Retrieve wordlist metadata by ID."""
        return self.conn.execute(
            "SELECT * FROM wordlists WHERE id = ?",
            (wordlist_id,)
        ).fetchone()

    def get_all_wordlists(self) -> List[sqlite3.Row]:
        """Retrieve all registered wordlists."""
        return self.conn.execute(
            "SELECT * FROM wordlists ORDER BY added_at DESC"
        ).fetchall()

    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------
    def create_session(self, target_hash: str) -> int:
        """Create a new cracking session with initial pending status."""
        cur = self.conn.execute(
            """INSERT INTO cracking_sessions
               (target_hash, status)
               VALUES (?, 'pending')""",
            (target_hash.strip(),)
        )
        self.conn.commit()
        return cur.lastrowid

    def mark_invalid_hash(self, session_id: int) -> None:
        """Mark session failed due to invalid hash syntax or length."""
        self._set_status(session_id, "invalid_hash", finished=True)

    def mark_unsupported_algorithm(self, session_id: int) -> None:
        """Mark session failed because the detected algorithm is not supported."""
        self._set_status(session_id, "unsupported_algorithm", finished=True)

    def mark_wordlist_not_found(self, session_id: int) -> None:
        """Mark session failed because the target wordlist file does not exist."""
        self._set_status(session_id, "wordlist_not_found", finished=True)

    def set_algorithm(self, session_id: int,
                      detected_algorithm_id: int,
                      selected_algorithm_id: Optional[int] = None) -> None:
        """Assign detected and selected algorithm IDs to a session."""
        selected = selected_algorithm_id or detected_algorithm_id
        self.conn.execute(
            """UPDATE cracking_sessions
               SET detected_algorithm_id = ?,
                   selected_algorithm_id = ?
               WHERE id = ?""",
            (detected_algorithm_id, selected, session_id)
        )
        self.conn.commit()

    def start_running(self, session_id: int,
                      wordlist_id: Optional[int] = None) -> None:
        """Transition session to running state, optionally with associated wordlist."""
        if wordlist_id is not None:
            self.conn.execute(
                """UPDATE cracking_sessions
                   SET wordlist_id = ?, status = 'running'
                   WHERE id = ?""",
                (wordlist_id, session_id)
            )
        else:
            self.conn.execute(
                """UPDATE cracking_sessions
                   SET status = 'running'
                   WHERE id = ?""",
                (session_id,)
            )
        self.conn.commit()

    def mark_found(self, session_id: int,
                   password: str,
                   attempts_count: int = 0,
                   duration_ms: float = 0.0) -> None:
        """Mark session successful with cracked password, attempts, and duration."""
        self.conn.execute(
            """UPDATE cracking_sessions
               SET status = 'found',
                   cracked_password = ?,
                   attempts_count = ?,
                   duration_ms = ?,
                   finished_at = ?
               WHERE id = ?""",
            (
                password,
                attempts_count,
                duration_ms,
                datetime.now().isoformat(),
                session_id
            )
        )
        self.conn.commit()

    def mark_not_found(self, session_id: int,
                       attempts_count: int = 0,
                       duration_ms: float = 0.0) -> None:
        """Mark session completed without finding matching password."""
        self._set_status(
            session_id,
            "not_found",
            finished=True,
            attempts_count=attempts_count,
            duration_ms=duration_ms
        )

    def _set_status(self, session_id: int,
                    status: str,
                    finished: bool = False,
                    attempts_count: Optional[int] = None,
                    duration_ms: Optional[float] = None) -> None:
        """Internal helper to update session status and metrics."""
        if finished:
            self.conn.execute(
                """UPDATE cracking_sessions
                   SET status = ?,
                       finished_at = ?,
                       attempts_count = COALESCE(?, attempts_count),
                       duration_ms = COALESCE(?, duration_ms)
                   WHERE id = ?""",
                (
                    status,
                    datetime.now().isoformat(),
                    attempts_count,
                    duration_ms,
                    session_id
                )
            )
        else:
            self.conn.execute(
                """UPDATE cracking_sessions
                   SET status = ?
                   WHERE id = ?""",
                (status, session_id)
            )
        self.conn.commit()

    def get_session(self, session_id: int) -> Optional[sqlite3.Row]:
        """Fetch session details by session ID."""
        return self.conn.execute(
            "SELECT * FROM cracking_sessions WHERE id = ?",
            (session_id,)
        ).fetchone()

    def get_all_sessions(self) -> List[sqlite3.Row]:
        """Fetch all sessions ordered by start time descending."""
        return self.conn.execute(
            "SELECT * FROM cracking_sessions ORDER BY started_at DESC"
        ).fetchall()

    # -------------------------------------------------------------------------
    # Attack Logging (Single & High-Throughput Batch)
    # -------------------------------------------------------------------------
    def log_attempt(self, session_id: int,
                    candidate_word: str,
                    generated_hash: str,
                    is_match: bool,
                    attempt_order: int) -> None:
        """Record an individual password cracking attempt."""
        self.conn.execute(
            """INSERT INTO attempts_log
               (session_id, candidate_word, generated_hash, is_match, attempt_order)
               VALUES (?, ?, ?, ?, ?)""",
            (
                session_id,
                candidate_word,
                generated_hash,
                int(is_match),
                attempt_order
            )
        )
        self.conn.execute(
            """UPDATE cracking_sessions
               SET attempts_count = attempts_count + 1
               WHERE id = ?""",
            (session_id,)
        )
        self.conn.commit()

    def log_attempts_batch(self, session_id: int,
                           attempts: List[tuple]) -> int:
        """
        Record multiple candidate attempts in a single high-performance transaction.
        Each attempt item tuple format: (candidate_word, generated_hash, is_match, attempt_order)
        """
        if not attempts:
            return 0

        prepared_data = [
            (session_id, word, h, int(match), order)
            for (word, h, match, order) in attempts
        ]

        self.conn.executemany(
            """INSERT INTO attempts_log
               (session_id, candidate_word, generated_hash, is_match, attempt_order)
               VALUES (?, ?, ?, ?, ?)""",
            prepared_data
        )
        self.conn.execute(
            """UPDATE cracking_sessions
               SET attempts_count = attempts_count + ?
               WHERE id = ?""",
            (len(prepared_data), session_id)
        )
        self.conn.commit()
        return len(prepared_data)

    def get_attempts_for_session(self, session_id: int) -> List[sqlite3.Row]:
        """Retrieve ordered attempt history for a specific session."""
        return self.conn.execute(
            """SELECT * FROM attempts_log
               WHERE session_id = ?
               ORDER BY attempt_order ASC""",
            (session_id,)
        ).fetchall()

    # -------------------------------------------------------------------------
    # Frontend Integration & Analytics API Helpers
    # Matches interface/frontend-demo/docs/API_CONTRACT.md
    # -------------------------------------------------------------------------
    def get_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Returns cracking history formatted exactly as expected by:
        GET /api/history
        """
        rows = self.conn.execute(
            """SELECT 
                   id,
                   target_hash,
                   algorithm,
                   status,
                   cracked_password,
                   duration_ms,
                   started_at
               FROM v_session_summary
               ORDER BY started_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset)
        ).fetchall()

        history_records = []
        for row in rows:
            history_records.append({
                "id": f"h{row['id']}",
                "hash": row["target_hash"],
                "algorithm": (row["algorithm"] or "").lower(),
                "status": row["status"],
                "password": row["cracked_password"],
                "submittedAt": row["started_at"],
                "durationMs": row["duration_ms"]
            })
        return history_records

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Computes statistics for interface/templates/dashboard.html:
        total_jobs, total_found, and success_rate percentage.
        """
        row = self.conn.execute("""
            SELECT 
                COUNT(*) AS total_jobs,
                SUM(CASE WHEN status = 'found' THEN 1 ELSE 0 END) AS total_found
            FROM cracking_sessions
        """).fetchone()

        total_jobs = row["total_jobs"] if row and row["total_jobs"] else 0
        total_found = row["total_found"] if row and row["total_found"] else 0
        success_rate = round((total_found / total_jobs * 100), 1) if total_jobs > 0 else 0.0

        return {
            "total_jobs": total_jobs,
            "total_found": total_found,
            "success_rate": success_rate
        }

    def get_reports(self) -> List[Dict[str, Any]]:
        """
        Generates aggregate cracking summaries for:
        GET /api/reports
        """
        rows = self.conn.execute("""
            SELECT 
                strftime('%Y-%W', started_at) AS week_period,
                MIN(started_at) AS period_start,
                COUNT(*) AS total_jobs,
                SUM(CASE WHEN status = 'found' THEN 1 ELSE 0 END) AS total_found
            FROM cracking_sessions
            GROUP BY strftime('%Y-%W', started_at)
            ORDER BY period_start DESC
        """).fetchall()

        reports = []
        for idx, row in enumerate(rows, start=1):
            reports.append({
                "id": f"r{idx}",
                "title": f"Cracking Summary (Week {row['week_period'] or 'Current'})",
                "generatedAt": row["period_start"] or datetime.now().isoformat(),
                "totalJobs": row["total_jobs"],
                "totalFound": row["total_found"] or 0
            })

        if not reports:
            # Fallback overall summary report if no weekly data partitioned
            stats = self.get_dashboard_stats()
            reports.append({
                "id": "r1",
                "title": "Overall Cracking Summary",
                "generatedAt": datetime.now().isoformat(),
                "totalJobs": stats["total_jobs"],
                "totalFound": stats["total_found"]
            })

        return reports

    # -------------------------------------------------------------------------
    # Connection Lifecycle
    # -------------------------------------------------------------------------
    def close(self) -> None:
        """Safely commit transactions and close SQLite connection."""
        try:
            self.conn.commit()
            self.conn.close()
        except Exception:
            pass


# -----------------------------------------------------------------------------
# CLI Verification
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    with DBManager() as db:
        print("[+] Hash Cracker Database Engine initialized successfully!")
        print("[+] Supported Cryptographic Algorithms:")
        for algo in db.get_all_algorithms():
            print(f"    - {algo['name']:<10} | Digest Length: {algo['hash_length']} chars | {algo['description']}")

        stats = db.get_dashboard_stats()
        print(f"[+] Initial Dashboard Stats: {stats}")
