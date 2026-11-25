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
            response = self.client.post('/api/crack', json={'hash': digest, 'algorithm': alg})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['password'], '123456')
            self.assertEqual(response.json['algorithm'], alg)
        history = self.client.get('/api/history').json
        self.assertTrue(history['backendConnected'])
        self.assertEqual(len(history['records']), 4)
        self.assertEqual(set(record['algorithm'] for record in history['records']), {'md5','sha1','sha256','sha512'})
        self.assertTrue(self.client.get('/api/reports').json['reports'])

    def test_not_found_and_validation(self):
        response = self.client.post('/api/crack', json={'hash': 'f'*32, 'algorithm':'md5'})
        self.assertEqual(response.json['status'], 'not_found')
        self.assertIsNone(response.json['password'])
        for payload in ({'hash':'bad','algorithm':'md5'}, {'hash':'f'*32,'algorithm':'sha256'}, {'hash':123, 'algorithm':'md5'}, {}):
            self.assertEqual(self.client.post('/api/crack', json=payload).status_code, 400)
        self.assertEqual(len(self.client.get('/api/history').json['records']), 1)

    def test_missing_wordlist_and_pages(self):
        self.wordlist.unlink()
        self.assertEqual(self.client.post('/api/crack', json={'hash':'f'*32,'algorithm':'md5'}).status_code, 503)
        for path in ('/', '/crack', '/results', '/history', '/reports', '/settings', '/static/css/redesign.css'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            response.close()

if __name__ == '__main__':
    unittest.main()
