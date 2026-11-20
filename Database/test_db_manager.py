"""
Unit Test Suite for Hash Cracker Database Subsystem
Module: Database/test_db_manager.py
Author: Rashad Sameh
"""

import os
import unittest
from Database.db_manager import DBManager


class TestDBManager(unittest.TestCase):

    def setUp(self):
        """Create an isolated, in-memory SQLite database instance for each test."""
        self.db = DBManager(db_path=":memory:")

    def tearDown(self):
        """Clean up connection."""
        self.db.close()

    def test_algorithms_prepopulated(self):
        """Verify that MD5, SHA-1, SHA-256, and SHA-512 are pre-populated."""
        algos = self.db.get_all_algorithms()
        names = [a["name"] for a in algos]
        self.assertIn("MD5", names)
        self.assertIn("SHA-1", names)
        self.assertIn("SHA-256", names)
        self.assertIn("SHA-512", names)

    def test_get_algorithm_by_length_and_name(self):
        """Test fetching algorithms by digest length and name."""
        md5 = self.db.get_algorithm_by_length(32)
        self.assertIsNotNone(md5)
        self.assertEqual(md5["name"], "MD5")

        sha256 = self.db.get_algorithm_by_name("sha-256")
        self.assertIsNotNone(sha256)
        self.assertEqual(sha256["hash_length"], 64)

        unknown = self.db.get_algorithm_by_length(999)
        self.assertIsNone(unknown)

    def test_wordlist_registration(self):
        """Test adding and retrieving wordlists."""
        w_id = self.db.add_wordlist("rockyou_sample", "/path/to/passwords.txt", 1000)
        self.assertGreater(w_id, 0)

        # Duplicate insert should return existing ID (idempotent)
        dup_id = self.db.add_wordlist("rockyou_sample", "/path/to/passwords.txt", 1000)
        self.assertEqual(w_id, dup_id)

        w_record = self.db.get_wordlist_by_id(w_id)
        self.assertIsNotNone(w_record)
        self.assertEqual(w_record["name"], "rockyou_sample")

    def test_session_lifecycle_success(self):
        """Test session lifecycle from pending to found."""
        target_hash = "e10adc3949ba59abbe56e057f20f883e"
        session_id = self.db.create_session(target_hash)
        self.assertGreater(session_id, 0)

        session = self.db.get_session(session_id)
        self.assertEqual(session["status"], "pending")

        # Set algorithm and wordlist
        algo = self.db.get_algorithm_by_name("MD5")
        w_id = self.db.add_wordlist("passwords", "/passwords.txt", 50)
        self.db.set_algorithm(session_id, detected_algorithm_id=algo["id"])
        self.db.start_running(session_id, wordlist_id=w_id)

        running_session = self.db.get_session(session_id)
        self.assertEqual(running_session["status"], "running")

        # Mark found
        self.db.mark_found(session_id, password="password", attempts_count=3, duration_ms=125.5)

        found_session = self.db.get_session(session_id)
        self.assertEqual(found_session["status"], "found")
        self.assertEqual(found_session["cracked_password"], "password")
        self.assertEqual(found_session["attempts_count"], 3)
        self.assertAlmostEqual(found_session["duration_ms"], 125.5)
        self.assertIsNotNone(found_session["finished_at"])

    def test_session_lifecycle_not_found_and_errors(self):
        """Test session transitions for not_found and error statuses."""
        # 1. Invalid Hash
        s1 = self.db.create_session("invalid!!")
        self.db.mark_invalid_hash(s1)
        self.assertEqual(self.db.get_session(s1)["status"], "invalid_hash")

        # 2. Unsupported Algorithm
        s2 = self.db.create_session("abcdef")
        self.db.mark_unsupported_algorithm(s2)
        self.assertEqual(self.db.get_session(s2)["status"], "unsupported_algorithm")

        # 3. Wordlist Not Found
        s3 = self.db.create_session("5f4dcc3b5aa765d61d8327deb882cf99")
        self.db.mark_wordlist_not_found(s3)
        self.assertEqual(self.db.get_session(s3)["status"], "wordlist_not_found")

        # 4. Not Found (Wordlist exhausted)
        s4 = self.db.create_session("5f4dcc3b5aa765d61d8327deb882cf99")
        self.db.mark_not_found(s4, attempts_count=500, duration_ms=450.0)
        self.assertEqual(self.db.get_session(s4)["status"], "not_found")
        self.assertEqual(self.db.get_session(s4)["attempts_count"], 500)

    def test_attempt_logging_single_and_batch(self):
        """Test single and batch attempt logging."""
        session_id = self.db.create_session("5f4dcc3b5aa765d61d8327deb882cf99")

        # Single log
        self.db.log_attempt(session_id, "admin", "21232f297a57a5a743894a0e4a801fc3", False, 1)

        # Batch log
        batch = [
            ("123456", "e10adc3949ba59abbe56e057f20f883e", False, 2),
            ("password", "5f4dcc3b5aa765d61d8327deb882cf99", True, 3),
        ]
        inserted = self.db.log_attempts_batch(session_id, batch)
        self.assertEqual(inserted, 2)

        attempts = self.db.get_attempts_for_session(session_id)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(attempts[0]["candidate_word"], "admin")
        self.assertEqual(attempts[2]["is_match"], 1)

    def test_frontend_contract_helpers(self):
        """Test history and dashboard stats formatting for API and templates."""
        # Create a few sessions
        s1 = self.db.create_session("5f4dcc3b5aa765d61d8327deb882cf99")
        algo = self.db.get_algorithm_by_name("MD5")
        self.db.set_algorithm(s1, detected_algorithm_id=algo["id"])
        self.db.mark_found(s1, password="password", attempts_count=10, duration_ms=100.0)

        s2 = self.db.create_session("e10adc3949ba59abbe56e057f20f883e")
        self.db.set_algorithm(s2, detected_algorithm_id=algo["id"])
        self.db.mark_not_found(s2, attempts_count=100, duration_ms=250.0)

        # 1. History
        history = self.db.get_history()
        self.assertEqual(len(history), 2)
        self.assertTrue(history[0]["id"].startswith("h"))
        self.assertIn("hash", history[0])
        self.assertIn("algorithm", history[0])
        self.assertIn("status", history[0])
        self.assertIn("submittedAt", history[0])

        # 2. Dashboard Stats
        stats = self.db.get_dashboard_stats()
        self.assertEqual(stats["total_jobs"], 2)
        self.assertEqual(stats["total_found"], 1)
        self.assertEqual(stats["success_rate"], 50.0)

        # 3. Reports
        reports = self.db.get_reports()
        self.assertGreaterEqual(len(reports), 1)
        self.assertIn("totalJobs", reports[0])
        self.assertIn("totalFound", reports[0])

    def test_run_tracked_attack_integration(self):
        """Test the integrated attack runner bridge in DBManager."""
        import tempfile
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tf:
            tf.write("pass\n123456\nadmin\n")
            wl_path = tf.name

        try:
            # MD5 for "123456"
            md5_hash = "e10adc3949ba59abbe56e057f20f883e"
            found = self.db.run_tracked_attack(md5_hash, wordlist_path=wl_path)
            self.assertEqual(found, "123456")

            session = self.db.get_all_sessions()[0]
            self.assertEqual(session["status"], "found")
            self.assertEqual(session["cracked_password"], "123456")
            self.assertGreater(session["attempts_count"], 0)
        finally:
            if os.path.exists(wl_path):
                os.remove(wl_path)

    def test_context_manager(self):
        """Test DBManager with 'with' statement."""
        with DBManager(db_path=":memory:") as manager:
            self.assertIsNotNone(manager.get_algorithm_by_name("MD5"))


if __name__ == "__main__":
    unittest.main()
