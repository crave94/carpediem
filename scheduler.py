"""
Background scheduler for Carpediem.

Runs two periodic jobs in a daemon thread:

  1. Startup scrape: when the web app starts, iterate every character and
     record a fresh exp snapshot for today. Runs in its own thread so the
     web server is not blocked.

  2. Daily scheduled scrape: at SCHEDULER_HOUR:SCHEDULER_MINUTE in
     SCHEDULER_TIMEZONE, scrape every character again and record a snapshot.

If a single character fails (network error, not in ranking, etc.) it is
logged and skipped — the rest of the loop continues.

Idempotent: calling start_scheduler() more than once is a no-op.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import db
import requests
from scraper import ScrapingError, scrape_character, HEADERS


LOG = logging.getLogger("carpediem.scheduler")

SCHEDULER_HOUR = 11
SCHEDULER_MINUTE = 30
# Peru is UTC-5 year-round (no DST). Use zoneinfo when available for proper
# timezone handling, fallback to fixed offset for bare Python installs.
SCHEDULER_TIMEZONE_NAME = "America/Lima"
try:
    from zoneinfo import ZoneInfo
    SCHEDULER_TZ = ZoneInfo("America/Lima")
except ImportError:
    # Fallback for Python < 3.9 or systems without tzdata
    SCHEDULER_TZ = timezone(timedelta(hours=-5))
    SCHEDULER_TIMEZONE_NAME = "America/Lima (UTC-5 fixed)"


_scheduler_lock = threading.Lock()
_scheduler_started = False
_loop_thread: Optional[threading.Thread] = None
_startup_thread: Optional[threading.Thread] = None


def _ensure_log_handler() -> None:
    """Attach a single stream handler to the scheduler logger on first call."""
    if LOG.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    ))
    LOG.addHandler(handler)
    LOG.setLevel(logging.INFO)
    LOG.propagate = False


def _pet_now() -> datetime:
    return datetime.now(SCHEDULER_TZ)


def _seconds_until_next_run() -> float:
    now = _pet_now()
    target = now.replace(
        hour=SCHEDULER_HOUR,
        minute=SCHEDULER_MINUTE,
        second=0,
        microsecond=0,
    )
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def scrape_all_characters_exp() -> dict:
    """
    Scrape every character's current exp via the Nexon ranking API and
    record a snapshot for today in exp_history. Runs sequentially with rate limiting.

    Returns a small summary dict: {"ok": int, "fail": int, "failures": [...]}.
    """
    import time as _time

    characters = db.list_characters()
    ok = 0
    failures: list[tuple[str, str]] = []

    # Use a session for connection pooling
    with requests.Session() as session:
        session.headers.update(HEADERS)
        for i, c in enumerate(characters):
            # Rate limit: 2 requests/second (0.5s delay) after first request
            if i > 0:
                _time.sleep(0.5)
            try:
                fresh = scrape_character(c["search_url"])
                db.record_exp_snapshot(c["id"], fresh.exp)
                ok += 1
            except ScrapingError as e:
                failures.append((c["name"], str(e)))
            except Exception as e:
                LOG.exception("scheduler: scrape failed for %s", c["name"])
                failures.append((c["name"], f"Error: {e}"))
    return {"ok": ok, "fail": len(failures), "failures": failures}


def _startup_worker() -> None:
    LOG.info(
        "scheduler: startup scrape starting (%d characters)",
        len(db.list_characters()),
    )
    result = scrape_all_characters_exp()
    LOG.info(
        "scheduler: startup scrape done — %d ok, %d fail",
        result["ok"],
        result["fail"],
    )
    for name, err in result["failures"]:
        LOG.warning("scheduler: %s: %s", name, err)


def _loop_worker() -> None:
    while True:
        wait = _seconds_until_next_run()
        LOG.info(
            "scheduler: next daily scrape in %.0fs (at %02d:%02d %s)",
            wait, SCHEDULER_HOUR, SCHEDULER_MINUTE, SCHEDULER_TIMEZONE_NAME,
        )
        time.sleep(wait)
        LOG.info("scheduler: daily scrape starting")
        try:
            result = scrape_all_characters_exp()
            LOG.info(
                "scheduler: daily scrape done — %d ok, %d fail",
                result["ok"],
                result["fail"],
            )
            for name, err in result["failures"]:
                LOG.warning("scheduler: %s: %s", name, err)
        except Exception:
            LOG.exception("scheduler: unhandled error in daily loop")


def start_scheduler(run_on_startup: bool = True) -> None:
    """
    Start the background scheduler thread. Safe to call multiple times —
    subsequent calls are no-ops.

    Set run_on_startup=False to skip the immediate startup scrape (useful
    for tests / one-off scripts).
    """
    global _scheduler_started, _loop_thread, _startup_thread
    _ensure_log_handler()
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    _loop_thread = threading.Thread(
        target=_loop_worker, name="carpediem-scheduler", daemon=True,
    )
    _loop_thread.start()
    LOG.info("scheduler: loop thread started")

    if run_on_startup:
        _startup_thread = threading.Thread(
            target=_startup_worker, name="carpediem-startup-scrape", daemon=True,
        )
        _startup_thread.start()
        LOG.info("scheduler: startup scrape thread started")


if __name__ == "__main__":
    # Only run if explicitly requested via env var (prevents accidental execution)
    if os.environ.get("CARPEDIEM_RUN_SCHEDULER") != "1":
        print("Set CARPEDIEM_RUN_SCHEDULER=1 to run scheduler directly")
        print("Usage: CARPEDIEM_RUN_SCHEDULER=1 python scheduler.py")
        sys.exit(1)

    import sys
    logging.basicConfig(
        level=os.environ.get("CARPEDIEM_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    LOG.info("scheduler: running one-off scrape (no Flask)")
    result = scrape_all_characters_exp()
    LOG.info("done: %d ok, %d fail", result["ok"], result["fail"])
    for name, err in result["failures"]:
        LOG.warning("  %s: %s", name, err)
