"""
Insurance Insights Assistant – Flask REST API
"""
import os
import sys

# Ensure the backend package root is on the path regardless of cwd
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, request
from flask_cors import CORS

from agents.orchestrator import InsuranceOrchestrator
from config import OPENAI_API_KEY
from database.setup import init_db, DB_PATH

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])

# Warn early if the API key is missing
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY is not set. "
          "Create backend/.env with OPENAI_API_KEY=sk-... before sending queries.")

# Initialise the database and the agent (once at startup)
if not os.path.exists(DB_PATH):
    print("Initialising database…")
    init_db()

_agent = InsuranceOrchestrator()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        resp = _agent.chat(message)
        return jsonify({
            "answer":      resp.answer,
            "sql":         resp.sql,
            "explanation": resp.explanation,
            "columns":     resp.columns,
            "rows":        resp.rows,
            "row_count":   resp.row_count,
            "error":       resp.error,
            "confidence":  resp.confidence,
        })
    except TypeError as exc:
        if "api_key" in str(exc) or "auth" in str(exc).lower():
            msg = ("OPENAI_API_KEY is not set or invalid. "
                   "Create backend/.env with OPENAI_API_KEY=sk-... and restart.")
            return jsonify({"error": msg}), 200
        app.logger.exception("TypeError in /api/chat")
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        app.logger.exception("Unhandled error in /api/chat")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/schema", methods=["GET"])
def schema():
    return jsonify(_agent.get_schema())


@app.route("/api/reset", methods=["POST"])
def reset():
    _agent.reset()
    return jsonify({"status": "conversation reset"})


@app.route("/api/suggest", methods=["GET"])
def suggest():
    """Return example questions to seed the UI."""
    examples = [
        "What is the total claims cost by region this quarter?",
        "Show me the loss ratio by policy type.",
        "Which 10 customers have the highest total premiums?",
        "How many active policies are there by policy type?",
        "What percentage of claims are denied vs approved?",
        "What is the average claim amount for auto policies?",
        "Show me the monthly claim count trend for 2024.",
        "Which state has the highest average risk score?",
        "What is the total premium revenue by region?",
        "List all settled claims over $50,000.",
    ]
    return jsonify({"suggestions": examples})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
