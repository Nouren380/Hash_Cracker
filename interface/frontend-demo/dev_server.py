from flask import Flask, render_template, jsonify, request
import time
import re

app = Flask(__name__)

DEV_WORDLIST = {
    "5f4dcc3b5aa765d61d8327deb882cf99": "password",
    "e10adc3949ba59abbe56e057f20f883e": "123456",
}

DEV_HISTORY = [
    {
        "id": "h1",
        "hash": "5f4dcc3b5aa765d61d8327deb882cf99",
        "algorithm": "md5",
        "status": "found",
        "password": "password",
        "submittedAt": "2026-11-10T09:14:00Z",
    },
    {
        "id": "h2",
        "hash": "d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2",
        "algorithm": "md5",
        "status": "not_found",
        "password": None,
        "submittedAt": "2026-11-11T13:02:00Z",
    },
]

DEV_REPORTS = [
    {
        "id": "r1",
        "title": "Weekly cracking summary",
        "generatedAt": "2026-11-09T00:00:00Z",
        "totalJobs": len(DEV_HISTORY),
        "totalFound": sum(1 for record in DEV_HISTORY if record["status"] == "found"),
    }
]

ALGORITHMS = [
    {"id": "md5", "label": "MD5"},
    {"id": "sha1", "label": "SHA-1"},
    {"id": "sha256", "label": "SHA-256"},
    {"id": "sha512", "label": "SHA-512"},
]


def render(template_name, **kwargs):
    return render_template(template_name, algorithms=ALGORITHMS, demo_backend=True, **kwargs)


@app.route("/")
def dashboard():
    stats = None
    return render("dashboard.html", active_page="dashboard", stats=stats)


@app.route("/crack")
def crack():
    return render("crack.html", active_page="crack")


@app.route("/results")
def results():
    return render("results.html", active_page="results")


@app.route("/history")
def history():
    return render("history.html", active_page="history")


@app.route("/reports")
def reports():
    return render("reports.html", active_page="reports")


@app.route("/settings")
def settings():
    return render("settings.html", active_page="settings")


@app.route("/api/crack", methods=["POST"])
def api_crack():
    payload = request.get_json(silent=True) or {}
    hash_value = str(payload.get("hash", "")).strip().lower()
    algorithm = {32: "md5", 40: "sha1", 64: "sha256", 128: "sha512"}.get(len(hash_value))

    if not hash_value:
        return jsonify({"error": {"message": "The hash field is required."}}), 400

    if not algorithm or not re.fullmatch(r"[0-9a-f]+", hash_value):
        return jsonify({"error": {"message": "Unsupported hash format or length."}}), 400

    time.sleep(0.4)
    password = DEV_WORDLIST.get(hash_value)

    return jsonify(
        {
            "hash": hash_value,
            "algorithm": algorithm,
            "status": "found" if password else "not_found",
            "password": password,
            "durationMs": 410,
        }
    )


@app.route("/api/history", methods=["GET"])
def api_history():
    return jsonify({"records": DEV_HISTORY, "backendConnected": False})


@app.route("/api/reports", methods=["GET"])
def api_reports():
    return jsonify({"reports": DEV_REPORTS, "backendConnected": False})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
