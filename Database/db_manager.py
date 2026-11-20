import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "hash_cracker.db")


class DBManager:

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    # Initialize Database Tables
    def _init_schema(self):

        self.conn.executescript("""

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

        """)

        self.conn.commit()


    # Get Algorithm By Hash Length
    def get_algorithm_by_length(self, length: int):
        return self.conn.execute(
            "SELECT * FROM hash_algorithms WHERE hash_length = ?",
            (length,)
        ).fetchone()


    # Get Algorithm By Name
    def get_algorithm_by_name(self, name: str):
        return self.conn.execute(
            "SELECT * FROM hash_algorithms WHERE name = ?",
            (name,)
        ).fetchone()


    # Get All Algorithms
    def get_all_algorithms(self):
        return self.conn.execute(
            "SELECT * FROM hash_algorithms"
        ).fetchall()


    # Add Wordlist
    def add_wordlist(self, name: str, file_path: str,
                     word_count: int = 0) -> int:

        cur = self.conn.execute(
            """INSERT OR IGNORE INTO wordlists
               (name, file_path, word_count)
               VALUES (?, ?, ?)""",
            (name, file_path, word_count)
        )

        self.conn.commit()

        if cur.lastrowid:
            return cur.lastrowid

        row = self.conn.execute(
            "SELECT id FROM wordlists WHERE file_path = ?",
            (file_path,)
        ).fetchone()

        return row["id"]


    # Create Cracking Session
    def create_session(self, target_hash: str) -> int:

        cur = self.conn.execute(
            """INSERT INTO cracking_sessions
               (target_hash, status)
               VALUES (?, 'pending')""",
            (target_hash,)
        )

        self.conn.commit()

        return cur.lastrowid


    # Mark Invalid Hash
    def mark_invalid_hash(self, session_id: int):
        self._set_status(session_id, "invalid_hash", finished=True)


    # Mark Unsupported Algorithm
    def mark_unsupported_algorithm(self, session_id: int):
        self._set_status(
            session_id,
            "unsupported_algorithm",
            finished=True
        )


    # Mark Wordlist Not Found
    def mark_wordlist_not_found(self, session_id: int):
        self._set_status(
            session_id,
            "wordlist_not_found",
            finished=True
        )


    # Set Hash Algorithm
    def set_algorithm(self, session_id: int,
                      detected_algorithm_id: int,
                      selected_algorithm_id: int = None):

        selected = selected_algorithm_id or detected_algorithm_id

        self.conn.execute(
            """UPDATE cracking_sessions
               SET detected_algorithm_id = ?,
                   selected_algorithm_id = ?
               WHERE id = ?""",
            (detected_algorithm_id, selected, session_id)
        )

        self.conn.commit()


    # Start Cracking Session
    def start_running(self, session_id: int, wordlist_id: int):

        self.conn.execute(
            """UPDATE cracking_sessions
               SET wordlist_id = ?, status = 'running'
               WHERE id = ?""",
            (wordlist_id, session_id)
        )

        self.conn.commit()


    # Mark Password Found
    def mark_found(self, session_id: int,
                   password: str, attempts_count: int):

        self.conn.execute(
            """UPDATE cracking_sessions
               SET status = 'found',
                   cracked_password = ?,
                   attempts_count = ?,
                   finished_at = ?
               WHERE id = ?""",
            (
                password,
                attempts_count,
                datetime.now().isoformat(),
                session_id
            )
        )

        self.conn.commit()


    # Mark Password Not Found
    def mark_not_found(self, session_id: int,
                       attempts_count: int):

        self._set_status(
            session_id,
            "not_found",
            finished=True,
            attempts_count=attempts_count
        )


    # Update Session Status
    def _set_status(self, session_id: int,
                    status: str,
                    finished: bool = False,
                    attempts_count: int = None):

        if finished:

            self.conn.execute(
                """UPDATE cracking_sessions
                   SET status = ?,
                       finished_at = ?,
                       attempts_count = COALESCE(?, attempts_count)
                   WHERE id = ?""",
                (
                    status,
                    datetime.now().isoformat(),
                    attempts_count,
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


    # Get Session
    def get_session(self, session_id: int):

        return self.conn.execute(
            "SELECT * FROM cracking_sessions WHERE id = ?",
            (session_id,)
        ).fetchone()


    # Get All Sessions
    def get_all_sessions(self):

        return self.conn.execute(
            """SELECT * FROM cracking_sessions
               ORDER BY started_at DESC"""
        ).fetchall()


    # Log Attempt
    def log_attempt(self, session_id: int,
                    candidate_word: str,
                    generated_hash: str,
                    is_match: bool,
                    attempt_order: int):

        self.conn.execute(
            """INSERT INTO attempts_log
               (session_id, candidate_word, generated_hash,
                is_match, attempt_order)
               VALUES (?, ?, ?, ?, ?)""",
            (
                session_id,
                candidate_word,
                generated_hash,
                int(is_match),
                attempt_order
            )
        )

        self.conn.commit()


    # Get Attempts For Session
    def get_attempts_for_session(self, session_id: int):

        return self.conn.execute(
            """SELECT * FROM attempts_log
               WHERE session_id = ?
               ORDER BY attempt_order""",
            (session_id,)
        ).fetchall()


    # Close Database Connection
    def close(self):
        self.conn.close()


# Main
if __name__ == "__main__":

    db = DBManager()

    print("Database initialized successfully!")

    print("Available Hash Algorithms:")

    for algorithm in db.get_all_algorithms():
        print(
            algorithm["name"],
            "-",
            algorithm["hash_length"]
        )

    db.close()
