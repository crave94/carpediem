#!/usr/bin/env python3
"""
Entry point for Replit / Gunicorn deployment.

Usage:
    Local:     python main.py
    Replit:    gunicorn --bind 0.0.0.0:8080 main:app
"""

import os
import sys

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env early (for local dev). Replit injects Secrets as env vars.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import app

# Optional: disable scheduler in production deployments (gunicorn workers)
# because multiple workers would run multiple schedulers.
# Set CARPEDIEM_SCHEDULER=1 in Replit Secrets to enable.
if os.environ.get("CARPEDIEM_SCHEDULER", "0") == "1":
    try:
        from scheduler import start_scheduler
        start_scheduler(run_on_startup=True)
    except Exception as e:
        print(f"[carpediem] Scheduler not started: {e}", file=sys.stderr)

if __name__ == "__main__":
    # Local development server (not for production)
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)