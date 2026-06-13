"""
Flask web app for scraping MapleStory (GMS) ranking pages.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""

from __future__ import annotations

import hashlib
import os
from functools import wraps
from typing import Optional

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, abort, send_from_directory, session, jsonify,
)

import db
from scraper import (
    scrape_character, download_image, ScrapingError, Character,
    scrape_legion_level, bulk_scrape_legion_levels, get_exp_tnl,
    scrape_news,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directory - same logic as db.py for persistence
if "REPL_HOME" in os.environ:
    _DATA_DIR = os.path.join(os.environ["REPL_HOME"], "data")
elif "HOME" in os.environ:
    _DATA_DIR = os.path.join(os.environ["HOME"], "carpediem_data")
else:
    _DATA_DIR = os.path.join(BASE_DIR, "instance")

IMAGE_DIR = os.path.join(_DATA_DIR, "images")
JOB_IMG_DIR = os.path.join(BASE_DIR, "instance", "imgmaple")

# Ensure directories exist
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(JOB_IMG_DIR, exist_ok=True)

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = os.environ.get("CARPEDIEM_ADMIN_PASSWORD", "carpediem")


# Fallback hardcoded mapping for jobs without image files yet
JOB_TO_IMG_FALLBACK = {
    "Adele":            "adele.webp",
    "Angelic Buster":   "angelic_buster.webp",
    "Aran":             "aran.webp",
    "Arch Mage (F/P)":  "fire_poison_arch_mage.webp",
    "Battle Mage":      "battle_mage.webp",
    "Bishop":           "bishop.webp",
    "Blade Master":     "blade_master.webp",
    "Bow Master":       "bowmaster.webp",
    "Cannoneer":        "cannoneer.webp",
    "Corsair":          "corsair.webp",
    "Dawn Warrior":     "dawn_warrior.webp",
    "Demon Avenger":    "demon_avenger.webp",
    "Demon Slayer":     "demon_slayer.webp",
    "Dual Blade":       "dual_blade.webp",
    "Evan":             "evan.webp",
    "Hayato":           "hayato.webp",
    "Hero":             "hero.webp",
    "Kain":             "kain.webp",
    "Kaiser":           "kaiser.webp",
    "Khali":            "khali.webp",
    "Kinesis":          "kinesis.webp",
    "Luminous":         "luminous.webp",
    "Mihile":           "mihile.webp",
    "Night Lord":       "night_lord.webp",
    "Night Walker":     "night_walker.webp",
    "Paladin":          "paladin.webp",
    "Pathfinder":       "pathfinder.webp",
    "Phantom":          "phantom.webp",
    "Ren":              "ren.webp",
    "Shadower":         "shadower.webp",
    "Sia Astelle":      "sia_astelle.webp",
    "Thunder Breaker":  "thunder_breaker.webp",
    "Wild Hunter":      "wild_hunter.webp",
    "Xenon":            "xenon.webp",
    "Zero":             "zero.webp",
}

_job_img_cache: dict[str, Optional[str]] = {}


def _build_job_image_map() -> dict[str, str]:
    """Build job->filename map by scanning imgmaple directory.

    Looks for .webp files and converts filenames to job names.
    Falls back to hardcoded mapping for files that don't follow convention.
    """
    mapping = {}
    # Known filename -> job name mappings (for non-standard names)
    filename_to_job = {
        "adele.webp": "Adele",
        "angelic_buster.webp": "Angelic Buster",
        "aran.webp": "Aran",
        "fire_poison_arch_mage.webp": "Arch Mage (F/P)",
        "battle_mage.webp": "Battle Mage",
        "bishop.webp": "Bishop",
        "blade_master.webp": "Blade Master",
        "bowmaster.webp": "Bow Master",
        "cannoneer.webp": "Cannoneer",
        "corsair.webp": "Corsair",
        "dawn_warrior.webp": "Dawn Warrior",
        "demon_avenger.webp": "Demon Avenger",
        "demon_slayer.webp": "Demon Slayer",
        "dual_blade.webp": "Dual Blade",
        "evan.webp": "Evan",
        "hayato.webp": "Hayato",
        "hero.webp": "Hero",
        "kain.webp": "Kain",
        "kaiser.webp": "Kaiser",
        "khali.webp": "Khali",
        "kinesis.webp": "Kinesis",
        "luminous.webp": "Luminous",
        "mihile.webp": "Mihile",
        "night_lord.webp": "Night Lord",
        "night_walker.webp": "Night Walker",
        "paladin.webp": "Paladin",
        "pathfinder.webp": "Pathfinder",
        "phantom.webp": "Phantom",
        "ren.webp": "Ren",
        "shadower.webp": "Shadower",
        "sia_astelle.webp": "Sia Astelle",
        "thunder_breaker.webp": "Thunder Breaker",
        "wild_hunter.webp": "Wild Hunter",
        "xenon.webp": "Xenon",
        "zero.webp": "Zero",
    }

    # First, use explicit mapping for known files
    for filename, job in filename_to_job.items():
        if os.path.exists(os.path.join(JOB_IMG_DIR, filename)):
            mapping[job] = filename

    # Then scan for any additional .webp files not in mapping
    try:
        for filename in os.listdir(JOB_IMG_DIR):
            if filename.endswith('.webp') and filename not in filename_to_job:
                # Convert filename to job name (e.g., "new_job.webp" -> "New Job")
                job_name = filename[:-5].replace('_', ' ').replace('-', ' ').title()
                mapping[job_name] = filename
    except OSError:
        pass

    return mapping


def job_image_url(job: str) -> Optional[str]:
    """Return the relative URL of the background image for a job, or None."""
    # Check cache first
    if job in _job_img_cache:
        return _job_img_cache[job]

    # Build map on first call
    if not _job_img_cache:
        scanned_map = _build_job_image_map()
        # Merge with fallback (fallback only used if file exists)
        for job_name, filename in JOB_TO_IMG_FALLBACK.items():
            if job_name not in scanned_map and os.path.exists(os.path.join(JOB_IMG_DIR, filename)):
                scanned_map[job_name] = filename
        # Cache all results (including None for missing)
        for job_name, filename in scanned_map.items():
            _job_img_cache[job_name] = url_for("serve_job_image", filename=filename)

    return _job_img_cache.get(job)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "maplestory-scraper-dev-key")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB (was 64 KB)


@app.template_filter("job_img")
def _job_img_filter(job: str) -> Optional[str]:
    """Jinja2 filter: return the URL of the background image for a job, or None."""
    return job_image_url(job)


def _format_short(value) -> str:
    """Compact number: 9639 -> '9.6k', 545,835,511,529,912 -> '545.8T'."""
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if v == 0:
        return "0"
    sign = "-" if v < 0 else ""
    a = abs(v)
    if a < 1000:
        return f"{sign}{int(a)}"
    for unit, threshold in (
        ("T", 1_000_000_000_000),
        ("B", 1_000_000_000),
        ("M", 1_000_000),
        ("k", 1_000),
    ):
        if a >= threshold:
            return f"{sign}{a / threshold:.1f}{unit}"
    return f"{sign}{int(a)}"


@app.template_filter("format_short")
def _format_short_filter(value) -> str:
    """Jinja2 filter: compact number formatting with k/M/B/T suffix."""
    return _format_short(value)


def current_user() -> Optional[dict]:
    """Return the logged-in user dict, or None if not authenticated."""
    uid = session.get("user_id")
    if not uid:
        return None
    user = db.get_user_by_id(uid)
    if user:
        user["is_admin"] = bool(user.get("is_admin"))
    return user


def login_required(view):
    """Redirect to /login (preserving the original target) when no user is logged in."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Tenés que iniciar sesión.", "error")
            return redirect(url_for("login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    """Require a logged-in user whose `is_admin` flag is true."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Tenés que iniciar sesión.", "error")
            return redirect(url_for("login", next=request.full_path))
        if not session.get("is_admin"):
            flash("No tenés permisos para acceder al dashboard.", "error")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_global_data():
    welcome_char = None
    try:
        row = db.get_random_character()
        if row:
            welcome_char = dict(row)
    except Exception:
        pass
    return {
        "current_user": current_user(),
        "welcome_char": welcome_char
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = db.verify_user(username, password) if username and password else None
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = bool(user["is_admin"])
            flash(f"Bienvenido {username}.", "success")
            target = request.args.get("next") or url_for("index")
            return redirect(target)
        flash("Usuario o contraseña incorrectos.", "error")

    return render_template("login.html", next=request.args.get("next") or "")


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("login"))


def _save_image_locally(image_url: str, char: Character) -> Optional[str]:
    """Download the character image to instance/images and return the filename.

    Uses stable hash based on name + region + world_id (not mutable fields like world name).
    """
    if not image_url:
        return None
    os.makedirs(IMAGE_DIR, exist_ok=True)
    # Stable hash: name + region + world_id (world_id never changes for a world)
    digest = hashlib.sha1(
        f"{char.name}|{char.region}|{char.world_id}".encode()
    ).hexdigest()[:16]
    filename = f"{digest}.png"
    full_path = os.path.join(IMAGE_DIR, filename)
    data = download_image(image_url)
    if not data:
        return None
    with open(full_path, "wb") as f:
        f.write(data)
    return filename


@app.route("/")
def index():
    characters = db.list_characters()
    return render_template("index.html", characters=characters)


@app.route("/directory")
def directory():
    characters = db.list_characters()

    def get_range_label(level: int) -> str:
        tens = (level // 10) * 10
        return f"{tens} - {tens + 9}"

    grouped = {}
    for c in characters:
        job = c["job"] or "Unknown"
        lvl = c["level"] or 0
        range_label = get_range_label(lvl)

        if job not in grouped:
            grouped[job] = {}
        if range_label not in grouped[job]:
            grouped[job][range_label] = []
        grouped[job][range_label].append(c)

    sorted_grouped = []

    def range_key(label: str) -> int:
        if " - " in label:
            return int(label.split(" - ")[0])
        return 0

    for job in sorted(grouped.keys()):
        ranges = grouped[job]
        sorted_ranges = []
        for r_label in sorted(ranges.keys(), key=range_key, reverse=True):
            sorted_ranges.append({
                "label": r_label,
                "characters": ranges[r_label]
            })
        sorted_grouped.append({
            "job": job,
            "ranges": sorted_ranges
        })

    return render_template("directory.html", grouped_jobs=sorted_grouped)


@app.route("/info")
def info():
    # Try reading from cache file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if "REPL_HOME" in os.environ:
        _data_dir = os.path.join(os.environ["REPL_HOME"], "data")
    elif "HOME" in os.environ:
        _data_dir = os.path.join(os.environ["HOME"], "carpediem_data")
    else:
        _data_dir = os.path.join(base_dir, "instance")

    cache_path = os.path.join(_data_dir, "news_cache.json")

    news_list = []
    error = None

    import json
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                all_news = json.load(f)
                news_list = all_news[:6]
        except Exception as e:
            error = f"Error al leer la caché: {e}"
    else:
        # Cache doesn't exist yet, try to fetch it synchronously as fallback
        try:
            all_news = scrape_news()
            news_list = all_news[:6]
            # Save it to cache so it exists next time
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(all_news, f, ensure_ascii=False, indent=2)
        except Exception as e:
            error = str(e)

    return render_template("info.html", news_list=news_list, error=error)





DEFAULT_RANKING_URL = (
    "https://www.nexon.com/maplestory/rankings/europe/world-ranking/luna"
    "?world_type=interactive&page_index=1"
    "&search_type=character-name&search={name}"
)


def _build_url_for(name: str) -> str:
    """Build the fixed ranking URL, URL-encoding the character name."""
    from requests.utils import quote
    return DEFAULT_RANKING_URL.format(name=quote(name))


@app.route("/addpj", methods=["GET", "POST"])
@admin_required
def addpj():
    """
    Hidden page for adding a new character. Intentionally not linked from
    any navigation — the URL is the only way to reach it.

    The form accepts a single name or a comma-separated list, e.g.:
        XenCzar
        XenCzar, AllanJair, Maguiito0
    Each name is scraped in order; the result is one summary flash message.
    """
    if request.method == "POST":
        raw = (request.form.get("names") or "").strip()
        names = [n.strip() for n in raw.split(",") if n.strip()]

        if not names:
            flash("Ingresá al menos un nombre de personaje.", "error")
            return redirect(url_for("addpj"))

        libb_flag = 1 if request.form.get("libb") else 0

        results = []  # (name, ok, message, char_id_or_none)
        for name in names:
            url = _build_url_for(name)
            try:
                char = scrape_character(url)
                image_filename = _save_image_locally(char.image_url, char)
                char_id = db.upsert_character(
                    char, image_path=image_filename, libb=libb_flag,
                )
                # EXP snapshot will be recorded by scheduler on next run (or startup scrape)
                results.append((name, True, f"id #{char_id}", char_id))
            except ScrapingError as e:
                results.append((name, False, str(e), None))
            except Exception as e:  # network errors, database issues, etc.
                app.logger.exception("scrape failed for %s", name)
                results.append((name, False, f"Error: {e}", None))

        ok = [r for r in results if r[1]]
        fail = [r for r in results if not r[1]]

        if ok and not fail:
            if len(ok) == 1:
                flash(f"Personaje '{ok[0][0]}' guardado ({ok[0][2]}).", "success")
            else:
                names_str = ", ".join(r[0] for r in ok)
                flash(f"{len(ok)} personajes guardados: {names_str}.", "success")
        elif fail and not ok:
            msgs = "; ".join(f"{n}: {m}" for n, _, m, _ in fail)
            flash(f"Fallaron {len(fail)} personajes — {msgs}", "error")
        else:
            ok_names = ", ".join(r[0] for r in ok)
            fail_msgs = "; ".join(f"{n}: {m}" for n, _, m, _ in fail)
            flash(
                f"Guardados {len(ok)} ({ok_names}). "
                f"Fallaron {len(fail)}: {fail_msgs}",
                "error",
            )

        return redirect(url_for("index") if ok else url_for("addpj"))

    return render_template("addpj.html")


@app.route("/characters/<int:char_id>")
def character_detail(char_id: int):
    char = db.get_character(char_id)
    if not char:
        abort(404)
    all_chars = db.list_characters()
    char_rank = next(
        (i for i, c in enumerate(all_chars, 1) if c["id"] == char_id),
        None,
    )
    # Create a window of 7 characters around the current character's rank
    # 3 above, current, 3 below (adjust at boundaries)
    if char_rank:
        window_size = 7
        half = window_size // 2  # 3
        start = max(0, char_rank - 1 - half)  # char_rank is 1-based, convert to 0-based
        end = min(len(all_chars), start + window_size)
        nearby_chars = all_chars[start:end]
        nearby_start_rank = start + 1  # 1-based rank of first item in window
    else:
        nearby_chars = all_chars[:7]
        nearby_start_rank = 1
    history = db.get_exp_history(char_id, days=14)
    positive_gains = [h["gain"] for h in history if h["gain"] and h["gain"] > 0]
    max_gain = max(positive_gains) if positive_gains else 1
    for h in history:
        h["bar_height"] = (h["gain"] / max_gain * 100) if (h["gain"] and h["gain"] > 0) else 0
        h["exp_fmt"] = f"{h['exp']:,}"
        h["gain_fmt"] = f"{h['gain']:,}" if h["gain"] is not None else None

    exp_tnl = get_exp_tnl(char["level"])
    next_level = (char["level"] or 0) + 1
    if exp_tnl:
        progress_pct = min(char["exp"] / exp_tnl * 100, 100.0)
        progress_label = f"{progress_pct:.2f}%"
    else:
        progress_pct = None
        progress_label = None

    return render_template(
        "character.html",
        char=char,
        char_rank=char_rank,
        all_chars=all_chars,
        nearby_chars=nearby_chars,
        nearby_start_rank=nearby_start_rank,
        history=history,
        max_gain=max_gain,
        exp_tnl=exp_tnl,
        next_level=next_level if exp_tnl else None,
        progress_pct=progress_pct,
        progress_label=progress_label,
    )


@app.route("/characters/<int:char_id>/delete", methods=["POST"])
@admin_required
def character_delete(char_id: int):
    char = db.get_character(char_id)
    if not char:
        abort(404)
    # best-effort delete local image
    if char["image_path"]:
        try:
            os.remove(os.path.join(IMAGE_DIR, char["image_path"]))
        except OSError:
            pass
    db.delete_character(char_id)
    flash(f"Personaje '{char['name']}' eliminado.", "success")
    return redirect(url_for("index"))


@app.route("/characters/<int:char_id>/refresh", methods=["POST"])
@admin_required
def character_refresh(char_id: int):
    char = db.get_character(char_id)
    if not char:
        abort(404)
    try:
        fresh = scrape_character(char["search_url"])
    except ScrapingError as e:
        flash(f"No se pudo refrescar: {e}", "error")
        return redirect(url_for("character_detail", char_id=char_id))

    image_filename = char["image_path"] or _save_image_locally(fresh.image_url, fresh)
    db.upsert_character(fresh, image_path=image_filename)
    db.record_exp_snapshot(char_id, fresh.exp)
    flash(f"'{fresh.name}' actualizado.", "success")
    return redirect(url_for("character_detail", char_id=char_id))


@app.route("/characters/<int:char_id>/scrape-legion", methods=["POST"])
@admin_required
def character_scrape_legion(char_id: int):
    """Scrape the legion ranking for this character and update its legion_level."""
    char = db.get_character(char_id)
    if not char:
        abort(404)
    try:
        lvl = scrape_legion_level(
            char["name"], char["region"], char["world"].lower(),
        )
    except ScrapingError as e:
        flash(f"No se pudo obtener legion level: {e}", "error")
        return redirect(url_for("character_detail", char_id=char_id))
    db.set_legion_level(char_id, lvl)
    flash(f"Legion level de '{char['name']}': {lvl}.", "success")
    return redirect(url_for("character_detail", char_id=char_id))


@app.route("/dashboard/scrape-legion", methods=["POST"])
@admin_required
def dashboard_scrape_legion():
    """
    Scrape the legion level for every character.

    Uses a single paginated scan per world, so a world with many characters
    at varying ranks costs only a handful of API calls (not one per char).
    """
    characters = db.list_characters()
    if not characters:
        flash("No hay personajes para scrapear.", "error")
        return redirect(url_for("dashboard"))

    targets = [(c["name"], c["region"], c["world"]) for c in characters]
    try:
        results = bulk_scrape_legion_levels(targets)
    except Exception as e:
        app.logger.exception("bulk legion scrape failed")
        flash(f"Error de red: {e}", "error")
        return redirect(url_for("dashboard"))

    ok = []
    fail = []
    for c in characters:
        lvl, err = results.get(c["name"].lower(), (None, "Sin resultado"))
        if err is None and lvl is not None:
            db.set_legion_level(c["id"], lvl)
            ok.append((c["name"], lvl))
        else:
            fail.append((c["name"], err or "Sin resultado"))

    if ok and not fail:
        flash(
            f"Legion level actualizado para {len(ok)} personajes.",
            "success",
        )
    elif fail and not ok:
        msgs = "; ".join(f"{n}: {m}" for n, m in fail[:5])
        more = f" (+{len(fail)-5} más)" if len(fail) > 5 else ""
        flash(f"Fallaron {len(fail)} personajes — {msgs}{more}", "error")
    else:
        ok_names = ", ".join(n for n, _ in ok[:5])
        fail_msgs = "; ".join(f"{n}: {m}" for n, m in fail[:3])
        more_fail = f" (+{len(fail)-3} más)" if len(fail) > 3 else ""
        flash(
            f"Legion level: {len(ok)} ok ({ok_names}), "
            f"{len(fail)} fallaron — {fail_msgs}{more_fail}",
            "error",
        )
    return redirect(url_for("dashboard"))


@app.route("/instance/images/<path:filename>")
def serve_image(filename: str):
    return send_from_directory(IMAGE_DIR, filename)


@app.route("/instance/imgmaple/<path:filename>")
def serve_job_image(filename: str):
    return send_from_directory(JOB_IMG_DIR, filename)


@app.route("/api/search")
def api_search():
    """
    Live search endpoint for navbar dropdown.
    Returns JSON with matching characters (max 8).
    Searches in name, job, world, level, rank_position using SQL.
    """
    q = (request.args.get("q") or "").strip()
    if not q or len(q) < 2:
        return jsonify({"results": []})

    characters = db.search_characters(q, limit=8)
    results = []
    for c in characters:
        results.append({
            "id": c["id"],
            "name": c["name"],
            "level": c["level"],
            "job": c["job"],
            "world": c["world"],
            "rank_position": c["rank_position"],
            "image_path": c["image_path"],
            "url": url_for("character_detail", char_id=c["id"]),
        })

    return jsonify({"results": results})


@app.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    """Bulk-edit page: list all characters and toggle their 'liberado' flag."""
    characters = db.list_characters()
    return render_template("dashboard.html", characters=characters)


@app.route("/dashboard/update", methods=["POST"])
@admin_required
def dashboard_update():
    """
    Receive the bulk-edit form: each row has a hidden `char_id` and optional
    `libb_{id}` and `leader_{id}` checkboxes. Update each character accordingly.
    """
    char_ids = request.form.getlist("char_id")
    updated = 0
    for cid in char_ids:
        try:
            cid_int = int(cid)
        except ValueError:
            continue
        new_libb = 1 if request.form.get(f"libb_{cid}") else 0
        new_leader = 1 if request.form.get(f"leader_{cid}") else 0
        db.set_libb(cid_int, new_libb)
        db.set_leader(cid_int, new_leader)
        updated += 1
    flash(f"{updated} personajes actualizados.", "success")
    return redirect(url_for("dashboard"))


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    db.init_db()
    os.makedirs(IMAGE_DIR, exist_ok=True)
    if not db.get_user_by_username(DEFAULT_ADMIN_USERNAME):
        created = db.create_user(
            DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, is_admin=True,
        )
        if created is not None:
            print(
                f"[carpediem] Default admin user created — "
                f"username='{DEFAULT_ADMIN_USERNAME}' "
                f"password='{DEFAULT_ADMIN_PASSWORD}' (change it!)"
            )
    from scheduler import start_scheduler
    start_scheduler()
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

