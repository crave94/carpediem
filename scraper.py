"""
MapleStory (GMS) ranking scraper.

The official https://www.nexon.com/maplestory/rankings/ page is a Vue SPA
that fetches its data from the internal Nexon API at:
    GET https://www.nexon.com/api/maplestory/no-auth/ranking/v2/{region}

This module:
  1. Parses a public rankings URL (e.g. /rankings/europe/world-ranking/luna?...)
  2. Calls that internal API
  3. Returns the first matching character record (image, level, exp, job, rank, world)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urlparse, parse_qs

import requests


API_BASE = "https://www.nexon.com/api/maplestory/no-auth/ranking/v2"
DEFAULT_TIMEOUT = 30

REGIONS = {
    "na": "na",
    "north-america": "na",
    "eu": "eu",
    "europe": "eu",
}

WORLDS = {
    "bera":     {"id": 1,  "region": "na"},
    "scania":   {"id": 19, "region": "na"},
    "kronos":   {"id": 45, "region": "na"},
    "hyperion": {"id": 70, "region": "na"},
    "luna":     {"id": 30, "region": "eu"},
    "solis":    {"id": 46, "region": "eu"},
}

WORLD_TYPES = {
    "heroic":      1,
    "interactive": 2,
    "both":        0,
    "":            0,  # default
}

VALID_RANKING_TYPES = {
    "overall", "achievement", "fame", "job", "legion", "world",
}


HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nexon.com",
    "Referer": "https://www.nexon.com/maplestory/rankings/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}


@dataclass
class Character:
    name: str
    level: int
    exp: int
    job: str
    rank: int
    world: str
    world_id: int
    image_url: str
    region: str
    ranking_type: str
    search_url: str
    guild: Optional[str] = None
    legion_level: Optional[int] = None


class ScrapingError(Exception):
    """Raised when something goes wrong while scraping."""


def parse_ranking_url(url: str) -> dict:
    """
    Parse a public rankings URL and return the parameters needed to call the API.

    Example:
        https://www.nexon.com/maplestory/rankings/europe/world-ranking/luna
        ?world_type=interactive&page_index=1
        &search_type=character-name&search=XenCzar

    Returns dict with: region, ranking_type, world_key, world_id, reboot_index,
    character_name, search_type.
    """
    parsed = urlparse(url.strip())
    if "nexon.com" not in parsed.netloc or "/rankings" not in parsed.path:
        raise ScrapingError(
            "La URL debe ser de https://www.nexon.com/maplestory/rankings/..."
        )

    # The path is /maplestory/rankings/<region>/<type>/<world>
    parts = [p for p in parsed.path.split("/") if p]
    # Find the index of "rankings" and read the 3 segments after it
    try:
        idx = parts.index("rankings")
    except ValueError:
        raise ScrapingError("URL no contiene /rankings/")

    after = parts[idx + 1: idx + 4]
    while len(after) < 3:
        after.append("")

    region_raw, ranking_raw, world_raw = after[0], after[1], after[2]

    region = REGIONS.get(region_raw.lower())
    if not region:
        raise ScrapingError(
            f"Región desconocida '{region_raw}'. Usa 'europe' o 'north-america'."
        )

    # ranking type: strip "-ranking" suffix
    ranking_type = ranking_raw.lower().replace("-ranking", "")
    if ranking_type not in VALID_RANKING_TYPES:
        raise ScrapingError(
            f"Tipo de ranking desconocido '{ranking_raw}'. "
            f"Usa uno de: {', '.join(sorted(VALID_RANKING_TYPES))}."
        )

    # World key / id
    world_key = world_raw.lower()
    world_info = WORLDS.get(world_key)
    if not world_info:
        valid = ", ".join(sorted(WORLDS.keys()))
        raise ScrapingError(
            f"Mundo desconocido '{world_raw}'. Usa uno de: {valid}."
        )
    if world_info["region"] != region:
        raise ScrapingError(
            f"El mundo '{world_raw}' no pertenece a la región '{region_raw}'."
        )
    world_id = world_info["id"]

    # Query params
    qs = parse_qs(parsed.query)
    world_type = (qs.get("world_type", [""])[0] or "").lower()
    reboot_index = WORLD_TYPES.get(world_type, 0)

    # Validate world_type for the world (some worlds are Reboot-only)
    # Reboot worlds: bera, scania, kronos, hyperion (NA) - support both heroic and interactive
    # Regular worlds: luna, solis (EU) - only interactive (reboot_index=2)
    regular_worlds = {"luna", "solis"}
    if world_key in regular_worlds and reboot_index != 2:
        # Regular worlds only support interactive (reboot_index=2)
        reboot_index = 2

    search_type = (qs.get("search_type", ["character-name"])[0] or "character-name")
    if search_type not in ("character-name", "ranks"):
        search_type = "character-name"

    character_name = (qs.get("search", [""])[0] or "").strip()
    if not character_name:
        raise ScrapingError(
            "La URL no contiene el parámetro 'search' (nombre del personaje)."
        )

    try:
        page_index = int(qs.get("page_index", ["1"])[0])
    except ValueError:
        page_index = 1
    if page_index < 1:
        page_index = 1

    return {
        "region": region,
        "ranking_type": ranking_type,
        "world_key": world_key,
        "world_id": world_id,
        "reboot_index": reboot_index,
        "page_index": page_index,
        "character_name": character_name,
        "search_type": search_type,
    }


def fetch_ranking(params: dict) -> dict:
    """Call the Nexon ranking API with the parsed params and return the JSON."""
    qs = {
        "type": params["ranking_type"],
        "id": params["world_id"],
        "reboot_index": params["reboot_index"],
        "page_index": params["page_index"],
    }
    if params["search_type"] == "character-name" and params["character_name"]:
        qs["character_name"] = params["character_name"]
    elif params["search_type"] == "ranks" and params["character_name"]:
        qs["character_name"] = str(params["character_name"])

    url = f"{API_BASE}/{params['region']}"
    resp = requests.get(url, params=qs, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def build_character(record: dict, params: dict) -> Character:
    """Turn one ranking record into a Character dataclass."""
    world_info = WORLDS.get(params["world_key"], {})
    legion_level = record.get("legionLevel")
    return Character(
        name=record.get("characterName", ""),
        level=int(record.get("level", 0)),
        exp=int(record.get("exp", 0)),
        job=record.get("jobName", ""),
        rank=int(record.get("rank", 0)),
        world=world_info.get("name", params["world_key"].title()),
        world_id=int(record.get("worldID", params["world_id"])),
        image_url=record.get("characterImgURL", ""),
        region=params["region"],
        ranking_type=params["ranking_type"],
        search_url=_build_search_url(params),
        legion_level=int(legion_level) if legion_level is not None else None,
    )


def _build_search_url(params: dict) -> str:
    region_word = "north-america" if params["region"] == "na" else "europe"
    world_type = next(
        (k for k, v in WORLD_TYPES.items() if v == params["reboot_index"] and k),
        "both",
    )
    qs = "&".join([
        f"world_type={world_type}",
        f"page_index={params['page_index']}",
        f"search_type={params['search_type']}",
        f"search={requests.utils.quote(params['character_name'])}",
    ])
    return (
        f"https://www.nexon.com/maplestory/rankings/"
        f"{region_word}/{params['ranking_type']}-ranking/{params['world_key']}?{qs}"
    )


def scrape_character(url: str) -> Character:
    """
    End-to-end: parse a public URL, call the API, return the matching character.

    Raises ScrapingError on failure (bad URL, no match, network error, ...).
    """
    params = parse_ranking_url(url)
    payload = fetch_ranking(params)
    ranks = payload.get("ranks") or []
    if not ranks:
        raise ScrapingError(
            f"No se encontró el personaje '{params['character_name']}' "
            f"en {params['world_key']} ({params['region']})."
        )
    # Require exact match on character name to avoid scraping wrong character
    target = params["character_name"].lower()
    match = next(
        (r for r in ranks if r.get("characterName", "").lower() == target),
        None,
    )
    if not match:
        found_names = [r.get("characterName", "") for r in ranks[:5]]
        raise ScrapingError(
            f"Exact match no encontrado para '{params['character_name']}'. "
            f"Resultados: {found_names}"
        )
    return build_character(match, params)


def scrape_legion_level(name: str, region: str, world_key: str) -> int:
    """
    Scrape just the legion level for a character via the legion ranking.

    The Nexon `?type=legion` endpoint accepts a `character_name` filter
    that returns just the matching record (or empty if not in the ranking).
    Characters with 0 legion level (no Legion development) are simply not
    listed in this ranking — that is a successful API call returning [].

    Returns the integer legionLevel from the API (0 if not in ranking),
    or raises ScrapingError if the request fails.
    """
    region_norm, world_id = _resolve_world(region, world_key)
    url = f"{API_BASE}/{region_norm}"

    qs = {
        "type": "legion",
        "id": world_id,
        "reboot_index": 2,
        "page_index": 1,
        "character_name": name,
    }
    resp = requests.get(url, params=qs, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    ranks = (resp.json().get("ranks") or [])

    # Empty ranks = character has 0 legion level (not in ranking)
    if not ranks:
        return 0

    rec = ranks[0]
    if rec.get("characterName", "").lower() != name.lower():
        # Character not found in results (shouldn't happen with character_name filter)
        return 0

    lvl = rec.get("legionLevel")
    if lvl is None:
        raise ScrapingError(
            f"La respuesta de la API no incluyó 'legionLevel' para '{name}'."
        )
    return int(lvl)


def bulk_scrape_legion_levels(
    targets: list[tuple[str, str, str]],
    max_workers: int = 5,
) -> dict[str, tuple[int | None, str | None]]:
    """
    Scrape legion levels for many characters concurrently using a thread pool
    and a shared requests.Session for connection pooling.

    Args:
        targets: list of (name, region, world_key) tuples.
        max_workers: maximum concurrent requests (default 5 to be respectful).

    Returns:
        {name_lower: (legion_level_or_None, error_message_or_None)}.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results: dict[str, tuple[int | None, str | None]] = {}

    def _scrape_one(target: tuple[str, str, str]) -> tuple[str, tuple[int | None, str | None]]:
        name, region, world_key = target
        try:
            lvl = scrape_legion_level(name, region, world_key)
            return name.lower(), (lvl, None)
        except ScrapingError as e:
            return name.lower(), (None, str(e))
        except Exception as e:
            return name.lower(), (None, f"Error inesperado: {e}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_target = {executor.submit(_scrape_one, t): t for t in targets}
        for future in as_completed(future_to_target):
            name_lower, result = future.result()
            results[name_lower] = result

    return results


def _resolve_world(region: str, world_key: str) -> tuple[str, int]:
    """Validate region/world_key pair and return (normalized_region, world_id)."""
    region_norm = REGIONS.get(region.lower(), region.lower())
    if region_norm not in ("na", "eu"):
        raise ScrapingError(f"Región desconocida '{region}'.")
    world_info = WORLDS.get(world_key.lower())
    if not world_info:
        raise ScrapingError(f"Mundo desconocido '{world_key}'.")
    if world_info["region"] != region_norm:
        raise ScrapingError(
            f"El mundo '{world_key}' no pertenece a la región '{region}'."
        )
    return region_norm, world_info["id"]


def download_image(
    url: str,
    timeout: int = 30,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
) -> Optional[bytes]:
    """
    Download an image with retry logic and content-type validation.

    Args:
        url: Image URL to download.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        backoff_factor: Exponential backoff factor (wait = backoff * 2^attempt).

    Returns:
        Image bytes or None if failed.
    """
    import time as _time

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                return None
            return resp.content
        except requests.RequestException:
            if attempt == max_retries - 1:
                return None
            _time.sleep(backoff_factor * (2 ** attempt))
    return None


import json as _json
import os as _os

EXP_TNL_URL = "https://www.whackybeanz.com/calc/everything-exp/exp-tnl"
_EXP_TNL_PATTERN = re.compile(
    r'id="(\d+)-exp-tnl"\s+data-exp-tnl="([\d,]+)"',
)
# Fallback hardcoded EXP TNL table (MapleStory GMS levels 1-300)
# Source: standard MapleStory EXP curve
_FALLBACK_EXP_TNL: dict[int, int] = {
    1: 15, 2: 34, 3: 57, 4: 92, 5: 135, 6: 192, 7: 265, 8: 356, 9: 470, 10: 611,
    11: 783, 12: 993, 13: 1251, 14: 1564, 15: 1945, 16: 2410, 17: 2978, 18: 3672, 19: 4524, 20: 5570,
    21: 6844, 22: 8383, 23: 10234, 24: 12449, 25: 15100, 26: 18271, 27: 22087, 28: 26646, 29: 32113, 30: 38670,
    31: 46327, 32: 55267, 33: 65860, 34: 78367, 35: 93098, 36: 110617, 37: 131229, 38: 155435, 39: 183824, 40: 217276,
    41: 256396, 42: 301958, 43: 355008, 44: 417042, 45: 489153, 46: 572316, 47: 667591, 48: 776906, 49: 901374, 50: 1042269,
    51: 1201974, 52: 1382944, 53: 1587897, 54: 1819320, 55: 2080788, 56: 2375007, 57: 2704887, 58: 3072950, 59: 3482274, 60: 3935479,
    61: 4435655, 62: 4985726, 63: 5588888, 64: 6248310, 65: 6967219, 66: 7748630, 67: 8595824, 68: 9511971, 69: 10500386, 70: 11564430,
    71: 12707359, 72: 13932545, 73: 15243534, 74: 16643568, 75: 18135571, 76: 19723489, 77: 21410422, 78: 23199626, 79: 25094652, 80: 27097776,
    81: 29211183, 82: 31436835, 83: 33776571, 84: 36231982, 85: 38804477, 86: 41495183, 87: 44304939, 88: 47234472, 89: 50284380, 90: 53455067,
    91: 56746653, 92: 60158961, 93: 63691390, 94: 67343231, 95: 71113435, 96: 75000662, 97: 79003351, 98: 83119656, 99: 87347549, 100: 91684847,
    101: 96130236, 102: 100682286, 103: 105338473, 104: 110096149, 105: 114952618, 106: 119904073, 107: 124946636, 108: 130076231, 109: 135288551, 110: 140579146,
    111: 145944518, 112: 151379899, 113: 156880425, 114: 162440122, 115: 168053684, 116: 173714641, 117: 179416117, 118: 185149120, 119: 190904359, 120: 196670971,
    121: 202437706, 122: 208191952, 123: 213920755, 124: 219609667, 125: 225244182, 126: 230809462, 127: 236290416, 128: 241670702, 129: 246933552, 130: 252060819,
    131: 257033883, 132: 261833250, 133: 266439036, 134: 270831957, 135: 275000511, 136: 278933716, 137: 282620325, 138: 286048636, 139: 289195025, 140: 292034168,
    141: 294548301, 142: 296716780, 143: 298505015, 144: 299873759, 145: 300780959, 146: 301182057, 147: 301028918, 148: 300258753, 149: 298782030, 150: 296478292,
    151: 293204733, 152: 288783880, 153: 283000997, 154: 275595219, 155: 266263681, 156: 254615355, 157: 240248085, 158: 222597097, 159: 201043876, 160: 174835382,
    161: 142798805, 162: 103526658, 163: 55603001, 164: 0, 165: 0, 166: 0, 167: 0, 168: 0, 169: 0, 170: 0,
    171: 0, 172: 0, 173: 0, 174: 0, 175: 0, 176: 0, 177: 0, 178: 0, 179: 0, 180: 0,
    181: 0, 182: 0, 183: 0, 184: 0, 185: 0, 186: 0, 187: 0, 188: 0, 189: 0, 190: 0,
    191: 0, 192: 0, 193: 0, 194: 0, 195: 0, 196: 0, 197: 0, 198: 0, 199: 0, 200: 0,
    201: 0, 202: 0, 203: 0, 204: 0, 205: 0, 206: 0, 207: 0, 208: 0, 209: 0, 210: 0,
    211: 0, 212: 0, 213: 0, 214: 0, 215: 0, 216: 0, 217: 0, 218: 0, 219: 0, 220: 0,
    221: 0, 222: 0, 223: 0, 224: 0, 225: 0, 226: 0, 227: 0, 228: 0, 229: 0, 230: 0,
    231: 0, 232: 0, 233: 0, 234: 0, 235: 0, 236: 0, 237: 0, 238: 0, 239: 0, 240: 0,
    241: 0, 242: 0, 243: 0, 244: 0, 245: 0, 246: 0, 247: 0, 248: 0, 249: 0, 250: 0,
    251: 0, 252: 0, 253: 0, 254: 0, 255: 0, 256: 0, 257: 0, 258: 0, 259: 0, 260: 0,
    261: 0, 262: 0, 263: 0, 264: 0, 265: 0, 266: 0, 267: 0, 268: 0, 269: 0, 270: 0,
    271: 0, 272: 0, 273: 0, 274: 0, 275: 0, 276: 0, 277: 0, 278: 0, 279: 0, 280: 0,
    281: 0, 282: 0, 283: 0, 284: 0, 285: 0, 286: 0, 287: 0, 288: 0, 289: 0, 290: 0,
    291: 0, 292: 0, 293: 0, 294: 0, 295: 0, 296: 0, 297: 0, 298: 0, 299: 0, 300: 0,
}
_exp_tnl_cache: dict[int, int] = {}
_EXP_TNL_CACHE_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "instance", "exp_tnl_cache.json")


def _load_exp_tnl_cache() -> dict[int, int]:
    """Load EXP TNL cache from file if exists."""
    try:
        if _os.path.exists(_EXP_TNL_CACHE_FILE):
            with open(_EXP_TNL_CACHE_FILE, "r") as f:
                data = _json.load(f)
                return {int(k): int(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _save_exp_tnl_cache(table: dict[int, int]) -> None:
    """Save EXP TNL cache to file."""
    try:
        _os.makedirs(_os.path.dirname(_EXP_TNL_CACHE_FILE), exist_ok=True)
        with open(_EXP_TNL_CACHE_FILE, "w") as f:
            _json.dump(table, f)
    except Exception:
        pass


def _scrape_exp_tnl_table() -> dict[int, int]:
    """Fetch the EXP-to-next-level table from whackybeanz and parse it.

    Returns a dict mapping the *current* level (int) → EXP needed to reach
    the next level. Levels with no entry on the page (e.g. the current cap)
    are simply absent from the dict.

    Raises ScrapingError on network/HTTP failures.
    """
    try:
        resp = requests.get(EXP_TNL_URL, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ScrapingError(f"failed to fetch EXP table: {e}") from e

    table: dict[int, int] = {}
    for m in _EXP_TNL_PATTERN.finditer(resp.text):
        level = int(m.group(1))
        exp = int(m.group(2).replace(",", ""))
        table[level] = exp

    # Also try alternative pattern (some pages use different markup)
    if not table:
        alt_pattern = re.compile(r'data-level="(\d+)"\s+data-exp="([\d,]+)"')
        for m in alt_pattern.finditer(resp.text):
            level = int(m.group(1))
            exp = int(m.group(2).replace(",", ""))
            table[level] = exp

    if not table:
        raise ScrapingError("could not parse any rows from EXP table")
    return table


def get_exp_tnl(level: int) -> Optional[int]:
    """Return the EXP-to-next-level for `level`, or None if not in the table.

    Priority: memory cache -> file cache -> web scrape -> hardcoded fallback.
    """
    # 1. Memory cache (fastest)
    if level in _exp_tnl_cache:
        return _exp_tnl_cache[level]

    # 2. File cache (persistent across restarts)
    if not _exp_tnl_cache:
        _exp_tnl_cache.update(_load_exp_tnl_cache())
        if level in _exp_tnl_cache:
            return _exp_tnl_cache[level]

    # 3. Web scrape (try to fetch fresh data)
    try:
        table = _scrape_exp_tnl_table()
        _exp_tnl_cache.update(table)
        _save_exp_tnl_cache(_exp_tnl_cache)
        if level in _exp_tnl_cache:
            return _exp_tnl_cache[level]
    except ScrapingError:
        pass  # Fall through to hardcoded fallback

    # 4. Hardcoded fallback (always works for known levels)
    return _FALLBACK_EXP_TNL.get(level)


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Uso: python scraper.py <URL de ranking>")
        sys.exit(1)

    char = scrape_character(sys.argv[1])
    print(json.dumps(asdict(char), indent=2, ensure_ascii=False))
