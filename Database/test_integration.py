import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hash_cracker_app", ROOT / "interface" / "app.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.wordlist = Path(self.temp.name) / "words.txt"
        self.wordlist.write_text("first\n123456\nlast\n", encoding="utf-8")
        module.app.config.update(TESTING=True, DATABASE_PATH=str(Path(self.temp.name) / "test.db"), WORDLIST_PATH=str(self.wordlist))
        self.client = module.app.test_client()

    def test_real_attack_persists_across_requests(self):
        for alg in ("md5", "sha1", "sha256", "sha512"):
            digest = hashlib.new(alg, b"123456").hexdigest()
            response = self.client.post('/api/crack', json={'hash': digest})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['password'], '123456')
            self.assertEqual(response.json['algorithm'], alg)
        history = self.client.get('/api/history').json
        self.assertTrue(history['backendConnected'])
        self.assertEqual(len(history['records']), 4)
        self.assertEqual(set(record['algorithm'] for record in history['records']), {'md5','sha1','sha256','sha512'})
        self.assertTrue(self.client.get('/api/reports').json['reports'])

    def test_not_found_and_validation(self):
        response = self.client.post('/api/crack', json={'hash': 'f'*32})
        self.assertEqual(response.json['status'], 'not_found')
        self.assertIsNone(response.json['password'])
        for payload in ({'hash':'bad'}, {'hash':'g'*32}, {'hash':'f'*31}, {'hash':123}, {}):
            self.assertEqual(self.client.post('/api/crack', json=payload).status_code, 400)
        self.assertEqual(len(self.client.get('/api/history').json['records']), 1)

    def test_inferred_algorithm_and_ambiguous_hash_length(self):
        # SHA3-256 has the same length as SHA-256; the result describes only
        # the algorithm actually tested, not a definitive identification.
        digest = hashlib.sha3_256(b"123456").hexdigest()
        response = self.client.post('/api/crack', json={'hash': digest})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['algorithm'], 'sha256')
        self.assertEqual(response.json['status'], 'not_found')
        upper = hashlib.md5(b"123456").hexdigest().upper()
        response = self.client.post('/api/crack', json={'hash': upper})
        self.assertEqual(response.json['password'], '123456')

    def test_history_clear_and_no_candidate_logging(self):
        digest = hashlib.md5(b"123456").hexdigest()
        self.assertEqual(self.client.post('/api/crack', json={'hash': digest}).status_code, 200)
        with module.database() as db:
            session = db.get_all_sessions()[0]
            self.assertEqual(session['attempts_count'], 2)
            self.assertEqual(db.get_attempts_for_session(session['id']), [])
            db.log_attempt(session['id'], 'legacy', 'abcd', False, 1)
        response = self.client.delete('/api/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['deleted'], 1)
        self.assertEqual(self.client.get('/api/history').json['records'], [])
        with module.database() as db:
            self.assertEqual(db.conn.execute('SELECT COUNT(*) FROM attempts_log').fetchone()[0], 0)

    def test_clear_refuses_active_session(self):
        with module.database() as db:
            sid = db.create_session('f' * 32)
            db.start_running(sid)
        response = self.client.delete('/api/history')
        self.assertEqual(response.status_code, 409)
        with module.database() as db:
            self.assertIsNotNone(db.get_session(sid))

    def test_invalid_wordlist_encoding_is_error(self):
        self.wordlist.write_bytes(b'valid\n\xff')
        response = self.client.post('/api/crack', json={'hash': 'f' * 32})
        self.assertEqual(response.status_code, 503)

    def test_missing_wordlist_and_pages(self):
        self.wordlist.unlink()
        self.assertEqual(self.client.post('/api/crack', json={'hash':'f'*32}).status_code, 503)
        for path in ('/', '/crack', '/results', '/history', '/reports', '/settings', '/static/css/redesign.css'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            response.close()

if __name__ == '__main__':
    unittest.main()
