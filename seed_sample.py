"""Leave the XenCzar sample character in the DB so the user sees something on first run."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import db
from scraper import scrape_character
from app import _save_image_locally


def main() -> int:
    db.init_db()
    url = (
        "https://www.nexon.com/maplestory/rankings/europe/world-ranking/luna"
        "?world_type=interactive&page_index=1"
        "&search_type=character-name&search=XenCzar"
    )
    char = scrape_character(url)
    image = _save_image_locally(char.image_url, char)
    char_id = db.upsert_character(char, image_path=image)
    print(f"Saved: #{char_id} {char.name} Lv.{char.level} image={image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
