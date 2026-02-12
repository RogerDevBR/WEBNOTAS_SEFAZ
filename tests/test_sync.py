import json
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

import app


class SyncFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        app.DB_PATH = base / "webnotas_test.db"
        app.DOWNLOADS_DIR = base / "downloads"
        app.init_db()

        cls.port = 8011
        cls.server = app.ThreadingHTTPServer(("127.0.0.1", cls.port), app.AppHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def _request(self, method, path, payload=None):
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            method=method,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_create_company_and_sync_documents(self):
        status, data = self._request(
            "POST",
            "/api/companies",
            {
                "name": "Cliente Teste",
                "cnpj": "12.345.678/0001-99",
                "strategy": "api",
            },
        )
        self.assertEqual(status, 201)
        company_id = data["id"]

        status, data = self._request("POST", f"/api/sync/{company_id}", {})
        self.assertEqual(status, 202)

        for _ in range(20):
            time.sleep(0.3)
            _, jobs = self._request("GET", "/api/jobs")
            if jobs and jobs[0]["status"] == "done":
                break
        self.assertTrue(jobs)
        self.assertEqual(jobs[0]["status"], "done")
        self.assertGreater(jobs[0]["total_documents"], 0)

        _, docs = self._request("GET", f"/api/documents?company_id={company_id}")
        self.assertGreater(len(docs), 0)


if __name__ == "__main__":
    unittest.main()
