"""Flask application connecting the interface, dictionary attack and SQLite."""
import os
import re
import sys
from pathlib import Path
from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from Database.db_manager import DBManager
FRONTEND = ROOT / "interface" / "frontend-demo"
app = Flask(__name__, template_folder=str(FRONTEND / "templates"), static_folder=str(FRONTEND / "static"))
app.config["DATABASE_PATH"] = os.environ.get("HASH_CRACKER_DB", str(ROOT / "Database" / "hash_cracker.db"))
app.config["WORDLIST_PATH"] = os.environ.get("HASH_CRACKER_WORDLIST", str(ROOT / "Core" / "password_list.txt"))
ALGORITHMS = [{"id": "md5", "label": "MD5"}, {"id": "sha1", "label": "SHA-1"}, {"id": "sha256", "label": "SHA-256"}, {"id": "sha512", "label": "SHA-512"}]
SUPPORTED = {"md5": ("MD5", 32), "sha1": ("SHA-1", 40), "sha256": ("SHA-256", 64), "sha512": ("SHA-512", 128)}

def database():
    return DBManager(db_path=app.config["DATABASE_PATH"])

def render(template, **kwargs):
    return render_template(template, algorithms=ALGORITHMS, **kwargs)

@app.get("/")
def dashboard():
    return render("dashboard.html", active_page="dashboard", stats=None)

@app.get("/crack")
def crack():
    return render("crack.html", active_page="crack")

@app.get("/results")
def results():
    return render("results.html", active_page="results")

@app.get("/history")
def history():
    return render("history.html", active_page="history")

@app.get("/reports")
def reports():
    return render("reports.html", active_page="reports")

@app.get("/settings")
def settings():
    return render("settings.html", active_page="settings")

def error(message, status):
    return jsonify({"error": {"message": message}}), status

@app.post("/api/crack")
def api_crack():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error("Send a JSON object containing a hash.", 400)
    value = payload.get("hash")
    if not isinstance(value, str) or not value.strip():
        return error("Enter a hash value.", 400)
    value = value.strip()
    if not re.fullmatch(r"[0-9a-fA-F]+", value):
        return error("The hash must contain only hexadecimal characters (0-9, a-f).", 400)
    match = next(((algorithm, name) for algorithm, (name, length) in SUPPORTED.items() if len(value) == length), None)
    if match is None:
        return error("Unsupported hash length. Use a hexadecimal hash of 32, 40, 64, or 128 characters.", 400)
    algorithm, name = match
    if not Path(app.config["WORDLIST_PATH"]).is_file():
        return error("The server wordlist is unavailable.", 503)
    with database() as db:
        session_id = db.run_tracked_attack(value, app.config["WORDLIST_PATH"], algorithm=name, return_session=True)
        session = db.get_session(session_id)
        if session["status"] not in ("found", "not_found"):
            return error("The attack could not be completed. Check the server wordlist.", 503)
        return jsonify({"hash": value, "algorithm": algorithm, "status": session["status"], "password": session["cracked_password"], "durationMs": session["duration_ms"]})

@app.get("/api/history")
def api_history():
    with database() as db:
        return jsonify({"records": db.get_history(), "backendConnected": True})

@app.delete("/api/history")
def api_clear_history():
    try:
        with database() as db:
            deleted = db.clear_history()
        return jsonify({"deleted": deleted})
    except RuntimeError as exc:
        return error(str(exc), 409)

@app.get("/api/reports")
def api_reports():
    with database() as db:
        return jsonify({"reports": db.get_reports(), "backendConnected": True})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
