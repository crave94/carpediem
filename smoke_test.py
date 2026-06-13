"""Smoke test: scrape + DB + image download + Flask test client."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import db
from scraper import scrape_character
from app import _save_image_locally, app


def main() -> int:
    db.init_db()
    print(f"DB at: {db.DB_PATH}")

    url = (
        "https://www.nexon.com/maplestory/rankings/europe/world-ranking/luna"
        "?world_type=interactive&page_index=1"
        "&search_type=character-name&search=XenCzar"
    )

    char = scrape_character(url)
    print(f"Scraped: {char.name} Lv.{char.level} EXP {char.exp:,} {char.job} rank #{char.rank}")

    image_path = _save_image_locally(char.image_url, char)
    print(f"Image saved: {image_path}")

    char_id = db.upsert_character(char, image_path=image_path)
    print(f"DB row id: {char_id}")

    print("\n--- Characters in DB ---")
    for row in db.list_characters():
        print(f"  #{row['id']} {row['name']} Lv.{row['level']} {row['job']} ({row['world']}) rank #{row['rank_position']}")

    print("\n--- Flask test client ---")
    client = app.test_client()
    r = client.get("/")
    print(f"GET /            -> {r.status_code}")
    r = client.post("/scrape", data={"url": url}, follow_redirects=False)
    print(f"POST /scrape     -> {r.status_code} (Location: {r.headers.get('Location')})")
    r = client.get(r.headers["Location"])
    print(f"GET {r.request.path:<28} -> {r.status_code} ({len(r.data)} bytes)")

    r = client.post(f"/characters/{char_id}/delete", follow_redirects=False)
    print(f"POST /characters/{char_id}/delete -> {r.status_code}")

    r = client.get("/")
    print(f"GET / (after delete) -> {r.status_code} ({len(r.data)} bytes)")

    print("\nALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
