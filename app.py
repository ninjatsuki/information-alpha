"""Local web UI for the Information Alpha pipeline.

Run with: python app.py
Then open: http://127.0.0.1:5000
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from alpha_filter import filter_alpha
from ingestion import ingest_all
from obsidian_sink import INBOX, write_brief

load_dotenv()

app = Flask(__name__)
CACHE_FILE = INBOX / ".last_run.json"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/cached")
def cached():
    if CACHE_FILE.exists():
        return jsonify(json.loads(CACHE_FILE.read_text(encoding="utf-8")))
    return jsonify({"items": [], "timestamp": None, "raw_count": 0})


@app.route("/api/run", methods=["POST"])
def run():
    github_token = os.getenv("GITHUB_TOKEN")
    items = asyncio.run(ingest_all(github_token=github_token))
    alpha = filter_alpha(items)
    path = write_brief(alpha)

    result = {
        "items": alpha,
        "raw_count": len(items),
        "alpha_count": len(alpha),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "brief_path": str(path),
    }
    INBOX.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return jsonify(result)


if __name__ == "__main__":
    print("Information Alpha UI — http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
