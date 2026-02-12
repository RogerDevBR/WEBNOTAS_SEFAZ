import json
import os
import random
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "webnotas.db"
DOWNLOADS_DIR = BASE_DIR / "data" / "downloads"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cnpj TEXT NOT NULL UNIQUE,
                state TEXT NOT NULL DEFAULT 'GO',
                strategy TEXT NOT NULL DEFAULT 'api',
                cert_alias TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                message TEXT,
                total_documents INTEGER DEFAULT 0,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                direction TEXT NOT NULL,
                chave TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                amount REAL NOT NULL,
                xml_path TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
            """
        )
        conn.commit()


def db_conn():
    return sqlite3.connect(DB_PATH)


def row_to_dict(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def json_response(handler, status, payload):
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def file_response(handler, path, content_type):
    data = Path(path).read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def run_mock_sync(job_id, company_id):
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE jobs SET status='running', started_at=?, message=? WHERE id=?",
                (datetime.utcnow().isoformat(), "Iniciando sincronização mock", job_id),
            )
            conn.commit()

        time.sleep(0.8)

        with db_conn() as conn:
            conn.row_factory = row_to_dict
            cur = conn.cursor()
            company = cur.execute(
                "SELECT * FROM companies WHERE id=?", (company_id,)
            ).fetchone()

        if not company:
            with db_conn() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE jobs SET status='error', finished_at=?, message=? WHERE id=?",
                    (datetime.utcnow().isoformat(), "Empresa não encontrada", job_id),
                )
                conn.commit()
            return

        docs_to_create = random.randint(18, 32)
        directions = ["entrada", "saida"]
        models = ["55", "65"]

        created = 0
        cnpj_dir = DOWNLOADS_DIR / company["cnpj"]
        cnpj_dir.mkdir(parents=True, exist_ok=True)

        with db_conn() as conn:
            cur = conn.cursor()
            for _ in range(docs_to_create):
                model = random.choice(models)
                direction = random.choice(directions)
                issue_date = (datetime.utcnow() - timedelta(days=random.randint(0, 45))).date().isoformat()
                amount = round(random.uniform(18.5, 1499.9), 2)
                chave = "".join(str(random.randint(0, 9)) for _ in range(44))
                xml_name = f"{chave}.xml"
                xml_path = cnpj_dir / xml_name
                xml_path.write_text(
                    f"<nfe><chave>{chave}</chave><modelo>{model}</modelo><direcao>{direction}</direcao><valor>{amount}</valor></nfe>",
                    encoding="utf-8",
                )

                cur.execute(
                    """
                    INSERT INTO documents (
                        company_id, model, direction, chave, issue_date, amount, xml_path, source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        company_id,
                        model,
                        direction,
                        chave,
                        issue_date,
                        amount,
                        str(xml_path.relative_to(BASE_DIR)) if str(xml_path).startswith(str(BASE_DIR)) else str(xml_path),
                        "mock_provider",
                        datetime.utcnow().isoformat(),
                    ),
                )
                created += 1

            cur.execute(
                "UPDATE jobs SET status='done', finished_at=?, message=?, total_documents=? WHERE id=?",
                (
                    datetime.utcnow().isoformat(),
                    "Sincronização concluída com sucesso (mock)",
                    created,
                    job_id,
                ),
            )
            conn.commit()
    except Exception as exc:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE jobs SET status='error', finished_at=?, message=? WHERE id=?",
                (datetime.utcnow().isoformat(), f"Falha na sincronização: {exc}", job_id),
            )
            conn.commit()


class AppHandler(BaseHTTPRequestHandler):
    def _serve_index(self):
        file_response(self, BASE_DIR / "static" / "index.html", "text/html; charset=utf-8")

    def _serve_asset(self, path):
        safe = (BASE_DIR / "static" / path).resolve()
        if not str(safe).startswith(str((BASE_DIR / "static").resolve())) or not safe.exists():
            self.send_error(404)
            return

        ctype = "text/plain; charset=utf-8"
        if safe.suffix == ".css":
            ctype = "text/css; charset=utf-8"
        elif safe.suffix == ".js":
            ctype = "application/javascript; charset=utf-8"
        file_response(self, safe, ctype)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            return self._serve_index()

        if parsed.path.startswith("/static/"):
            return self._serve_asset(parsed.path.replace("/static/", "", 1))

        if parsed.path == "/api/companies":
            with db_conn() as conn:
                conn.row_factory = row_to_dict
                cur = conn.cursor()
                companies = cur.execute(
                    "SELECT * FROM companies ORDER BY id DESC"
                ).fetchall()
            return json_response(self, 200, companies)

        if parsed.path == "/api/jobs":
            query = parse_qs(parsed.query)
            company_id = query.get("company_id", [None])[0]
            with db_conn() as conn:
                conn.row_factory = row_to_dict
                cur = conn.cursor()
                if company_id:
                    jobs = cur.execute(
                        "SELECT * FROM jobs WHERE company_id=? ORDER BY id DESC LIMIT 20",
                        (company_id,),
                    ).fetchall()
                else:
                    jobs = cur.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 50").fetchall()
            return json_response(self, 200, jobs)

        if parsed.path == "/api/documents":
            query = parse_qs(parsed.query)
            company_id = query.get("company_id", [None])[0]
            if not company_id:
                return json_response(self, 400, {"error": "company_id é obrigatório"})
            with db_conn() as conn:
                conn.row_factory = row_to_dict
                cur = conn.cursor()
                docs = cur.execute(
                    """
                    SELECT * FROM documents
                    WHERE company_id=?
                    ORDER BY id DESC LIMIT 200
                    """,
                    (company_id,),
                ).fetchall()
            return json_response(self, 200, docs)

        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length or 0)

        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return json_response(self, 400, {"error": "JSON inválido"})

        if parsed.path == "/api/companies":
            name = (payload.get("name") or "").strip()
            cnpj = "".join(ch for ch in (payload.get("cnpj") or "") if ch.isdigit())
            strategy = payload.get("strategy") or "api"
            cert_alias = payload.get("cert_alias")

            if not name or len(cnpj) != 14:
                return json_response(self, 400, {"error": "Nome e CNPJ válido são obrigatórios"})

            with db_conn() as conn:
                cur = conn.cursor()
                try:
                    cur.execute(
                        """
                        INSERT INTO companies (name, cnpj, state, strategy, cert_alias, created_at)
                        VALUES (?, ?, 'GO', ?, ?, ?)
                        """,
                        (name, cnpj, strategy, cert_alias, datetime.utcnow().isoformat()),
                    )
                except sqlite3.IntegrityError:
                    return json_response(self, 409, {"error": "CNPJ já cadastrado"})
                conn.commit()
                company_id = cur.lastrowid
            return json_response(self, 201, {"id": company_id})

        if parsed.path.startswith("/api/sync/"):
            try:
                company_id = int(parsed.path.split("/")[-1])
            except ValueError:
                return json_response(self, 400, {"error": "company_id inválido"})

            with db_conn() as conn:
                cur = conn.cursor()
                exists = cur.execute(
                    "SELECT id FROM companies WHERE id=?", (company_id,)
                ).fetchone()
                if not exists:
                    return json_response(self, 404, {"error": "Empresa não encontrada"})

                cur.execute(
                    "INSERT INTO jobs (company_id, status, message) VALUES (?, 'queued', ?)",
                    (company_id, "Aguardando execução"),
                )
                job_id = cur.lastrowid
                conn.commit()

            t = threading.Thread(target=run_mock_sync, args=(job_id, company_id), daemon=True)
            t.start()
            return json_response(self, 202, {"job_id": job_id, "status": "queued"})

        self.send_error(404)


def run(port=8000):
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", port), AppHandler)
    print(f"WEBNOTAS mockup rodando em http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
