"""
Unit Tests for Dictionary Attack Engine & Database Integration
Module: Core/test_dictionary_attack.py
"""

import os
import tempfile
import unittest

from Core.dictionary_attack import dictionary_attack
from Database.db_manager import DBManager


class TestDictionaryAttackIntegration(unittest.TestCase):

    def setUp(self):
        """Create a temporary wordlist and in-memory DB for each test."""
        self.temp_wordlist = tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8")
        self.temp_wordlist.write("admin\nsecret\n123456\npassword\n")
        self.temp_wordlist.flush()
        self.wordlist_path = self.temp_wordlist.name

        self.db = DBManager(db_path=":memory:")

    def tearDown(self):
        """Clean up temporary files and close DB."""
        self.db.close()
        if os.path.exists(self.wordlist_path):
            os.remove(self.wordlist_path)

    def test_crack_md5_success(self):
        """Test successful cracking of MD5 hash for '123456'."""
        md5_hash = "e10adc3949ba59abbe56e057f20f883e"
        found = dictionary_attack(md5_hash, wordlist_path=self.wordlist_path, db=self.db)
        self.assertEqual(found, "123456")

        # Verify DB session state
        sessions = self.db.get_all_sessions()
        self.assertEqual(len(sessions), 1)
        session = sessions[0]
        self.assertEqual(session["status"], "found")
        self.assertEqual(session["cracked_password"], "123456")
        self.assertGreater(session["attempts_count"], 0)
        self.assertGreater(session["duration_ms"], 0)

        # Verify attempts log in DB
        attempts = self.db.get_attempts_for_session(session["id"])
        self.assertGreaterEqual(len(attempts), 1)
        matched_attempt = [a for a in attempts if a["is_match"] == 1]
        self.assertEqual(len(matched_attempt), 1)
        self.assertEqual(matched_attempt[0]["candidate_word"], "123456")

    def test_crack_sha256_success(self):
        """Test successful cracking of SHA-256 hash for 'secret'."""
        # SHA-256 for 'secret': 2bb80e5e...
        import hashlib
        sha256_hash = hashlib.sha256("secret".encode()).hexdigest()
        found = dictionary_attack(sha256_hash, wordlist_path=self.wordlist_path, db=self.db)
        self.assertEqual(found, "secret")

        sessions = self.db.get_all_sessions()
        self.assertEqual(sessions[0]["status"], "found")
        self.assertEqual(sessions[0]["cracked_password"], "secret")

    def test_invalid_hash_input(self):
        """Test handling of invalid hash format."""
        found = dictionary_attack("invalid hash with spaces", wordlist_path=self.wordlist_path, db=self.db)
        self.assertIsNone(found)

        sessions = self.db.get_all_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["status"], "invalid_hash")

    def test_wordlist_not_found(self):
        """Test handling of non-existent wordlist file."""
        md5_hash = "e10adc3949ba59abbe56e057f20f883e"
        found = dictionary_attack(md5_hash, wordlist_path="/path/does/not/exist.txt", db=self.db)
        self.assertIsNone(found)

        sessions = self.db.get_all_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["status"], "wordlist_not_found")

    def test_password_not_found_wordlist_exhausted(self):
        """Test hash that is not in the wordlist."""
        # MD5 of 'not_in_list'
        md5_hash = "73d758c56fa769eb07024ea9356ef5a8"
        found = dictionary_attack(md5_hash, wordlist_path=self.wordlist_path, db=self.db)
        self.assertIsNone(found)

        sessions = self.db.get_all_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["status"], "not_found")
        self.assertIsNone(sessions[0]["cracked_password"])
        self.assertEqual(sessions[0]["attempts_count"], 4)  # 4 words in temp wordlist


if __name__ == "__main__":
    unittest.main()
