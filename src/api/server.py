import os
from dataclasses import asdict
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from src.data.parser import parse_csv
from src.data.pipeline import (
    compute_force_velocity_profile,
    compute_phase_breakdown,
    compute_session_summary,
    compute_stroke_metrics,
)

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "sample_data")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def _get_csv_files() -> list[str]:
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        return []
    return sorted(f.name for f in data_path.glob("*.csv"))


def _load_session(filename: str):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(filepath):
        return None
    return parse_csv(filepath)


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, "static"), path)


@app.route("/components/<path:path>")
def serve_components(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, "components"), path)


@app.route("/api/sessions")
def list_sessions():
    files = _get_csv_files()
    return jsonify(files)


@app.route("/api/sessions/<filename>")
def get_session(filename: str):
    records = _load_session(filename)
    if records is None:
        return jsonify({"error": "Session not found"}), 404
    summary = compute_session_summary(filename, records)
    return jsonify(asdict(summary))


@app.route("/api/sessions/<filename>/strokes")
def get_strokes(filename: str):
    records = _load_session(filename)
    if records is None:
        return jsonify({"error": "Session not found"}), 404
    rep_numbers = sorted(set(r.rep for r in records))
    strokes = [asdict(compute_stroke_metrics(records, rep)) for rep in rep_numbers]
    return jsonify(strokes)


@app.route("/api/sessions/<filename>/force-velocity")
def get_force_velocity(filename: str):
    records = _load_session(filename)
    if records is None:
        return jsonify({"error": "Session not found"}), 404
    profile = compute_force_velocity_profile(records)
    return jsonify(profile)


@app.route("/api/sessions/<filename>/phase-breakdown")
def get_phase_breakdown(filename: str):
    records = _load_session(filename)
    if records is None:
        return jsonify({"error": "Session not found"}), 404
    breakdown = compute_phase_breakdown(records)
    return jsonify(breakdown)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
