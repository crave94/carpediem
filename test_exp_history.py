"""Verify daily exp snapshots: seed 7 days of data, check the detail page renders."""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

import db
from app import app, _save_image_locally
from scraper import Character

db.init_db()

# Use the existing XenCzar (id=2) or any character
char_id = None
for row in db.list_characters():
    if row["name"] == "XenCzar":
        char_id = row["id"]
        break

if char_id is None:
    # No XenCzar in DB yet: create a minimal record
    c = Character("XenCzar", 295, 500_000_000_000_000, "Xenon", 46,
                  "Luna", 30, "", "eu", "world", "http://x")
    char_id = db.upsert_character(c, image_path=None)
    print(f"Created XenCzar as id {char_id}")

# Clean any prior exp_history rows for this character
with db.get_conn() as conn:
    conn.execute("DELETE FROM exp_history WHERE character_id = ?", (char_id,))

# Seed 7 consecutive days of snapshots (yesterday-6 through today)
base_exp = 500_000_000_000_000
daily_gains = [12_345_678_901, 8_765_432_109, 22_111_222_333, 0,
               18_444_222_111, 9_999_000_111, 14_502_001_888]
print("\nSeeding 7 days of snapshots:")
running = base_exp
for i, gain in enumerate(daily_gains):
    d = date.today() - timedelta(days=(6 - i))
    running += gain
    db.record_exp_snapshot(char_id, running, day=d)
    print(f"  {d}  exp={running:>16,}  gain={gain:>13,}")

# Check get_exp_history
print("\nget_exp_history(days=30):")
for h in db.get_exp_history(char_id):
    print(f"  {h['day']}  exp={h['exp']:>16,}  gain={h['gain']}")

# Render detail page via test client
print("\nFlask detail page:")
client = app.test_client()
r = client.get(f"/characters/{char_id}")
print(f"  GET /characters/{char_id}  -> {r.status_code}  ({len(r.data)} bytes)")

# Sanity-check that the chart HTML is present
html = r.data.decode()
checks = [
    ("exp-chart__bar",       "bar elements"),
    ("exp-chart__fill",      "fill elements"),
    ("exp-chart__day",       "day labels"),
    ("exp-history",          "history section"),
]
for needle, label in checks:
    print(f"  {label:<20} {'OK' if needle in html else 'MISSING'} ({needle!r})")

# Show how many bars are in the response
import re
bars = re.findall(r'class="exp-chart__bar[^"]*"', html)
print(f"  Total bars rendered: {len(bars)}")

# Sample one bar
m = re.search(r'(<div class="exp-chart__bar[^"]*"[^>]*>.*?</div>\s*</div>\s*</div>)', html, re.S)
if m:
    snippet = m.group(1)[:400].replace("\n", " ")
    print(f"  Sample bar: {snippet[:200]}...")

print("\nOK")
