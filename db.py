"""
SQLite persistence layer for scraped MapleStory characters.

Stores one row per (region, world, character_name) — re-scraping the same URL
updates the existing row instead of duplicating it.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Iterator, Optional

from scraper import Character
from werkzeug.security import check_password_hash, generate_password_hash


# Replit uses /home/runner/<repl-slug> as $HOME (persistent across deploys)
# Local dev uses repo root /instance
if "CARPEDIEM_DATA_DIR" in os.environ:
    _DATA_DIR = os.environ["CARPEDIEM_DATA_DIR"]
elif "REPL_HOME" in os.environ:
    _DATA_DIR = os.path.join(os.environ["REPL_HOME"], "data")
elif "HOME" in os.environ:
    _DATA_DIR = os.path.join(os.environ["HOME"], "carpediem_data")
else:
    _DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")

os.makedirs(_DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(_DATA_DIR, "maplestory.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS characters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    region          TEXT    NOT NULL,
    world           TEXT    NOT NULL,
    world_id        INTEGER NOT NULL,
    job             TEXT    NOT NULL,
    level           INTEGER NOT NULL,
    exp             INTEGER NOT NULL,
    rank_position   INTEGER NOT NULL,
    image_url       TEXT    NOT NULL,
    ranking_type    TEXT    NOT NULL,
    search_url      TEXT    NOT NULL,
    image_path      TEXT,
    guild           TEXT,
    libb            INTEGER NOT NULL DEFAULT 0,
    leader          INTEGER NOT NULL DEFAULT 0,
    amigo           INTEGER NOT NULL DEFAULT 0,
    legion_level    INTEGER,
    scraped_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (region, world, name, ranking_type)
);

CREATE TABLE IF NOT EXISTS exp_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id    INTEGER NOT NULL,
    exp             INTEGER NOT NULL,
    day             TEXT    NOT NULL,
    UNIQUE (character_id, day),
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_exp_history_char_day
    ON exp_history (character_id, day);

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    is_admin        INTEGER NOT NULL DEFAULT 0,
    discord_id      TEXT    UNIQUE,
    discord_avatar  TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    title           TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    price           TEXT    NOT NULL,
    image_filename  TEXT    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with Row factory, auto-committing on success."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist, then apply lightweight migrations."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """Apply idempotent ALTER TABLE migrations for columns added after v1."""
    existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(characters)")
    }
    if "guild" not in existing:
        conn.execute("ALTER TABLE characters ADD COLUMN guild TEXT")
    if "libb" not in existing:
        conn.execute(
            "ALTER TABLE characters ADD COLUMN libb INTEGER NOT NULL DEFAULT 0"
        )
    if "leader" not in existing:
        conn.execute(
            "ALTER TABLE characters ADD COLUMN leader INTEGER NOT NULL DEFAULT 0"
        )
    if "legion_level" not in existing:
        conn.execute("ALTER TABLE characters ADD COLUMN legion_level INTEGER")
    if "amigo" not in existing:
        conn.execute(
            "ALTER TABLE characters ADD COLUMN amigo INTEGER NOT NULL DEFAULT 0"
        )
        
    user_existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(users)")
    }
    if "discord_id" not in user_existing:
        conn.execute("ALTER TABLE users ADD COLUMN discord_id TEXT")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id)")
    if "discord_avatar" not in user_existing:
        conn.execute("ALTER TABLE users ADD COLUMN discord_avatar TEXT")
        
    try:
        conn.execute("SELECT id FROM market_posts LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS market_posts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            title           TEXT    NOT NULL,
            description     TEXT    NOT NULL,
            price           TEXT    NOT NULL,
            image_filename  TEXT    NOT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)


def upsert_character(
    char: Character, image_path: Optional[str] = None, guild: Optional[str] = None,
    libb: Optional[int] = None, legion_level: Optional[int] = None,
    amigo: Optional[int] = None,
) -> int:
    """
    Insert or update a character. Returns the row id.
    The natural key is (region, world, name, ranking_type).

    `guild`, `libb`, and `legion_level` are only updated if the parameter is not None.
    This allows explicitly setting `libb=0` to clear the flag, while `libb=None`
    preserves the existing value.
    """
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id FROM characters "
            "WHERE region = ? AND world = ? AND name = ? AND ranking_type = ?",
            (char.region, char.world, char.name, char.ranking_type),
        )
        existing = cur.fetchone()

        if existing:
            # Build dynamic UPDATE to only set fields that are not None
            updates = [
                "world_id = ?",
                "job = ?",
                "level = ?",
                "exp = ?",
                "rank_position = ?",
                "image_url = ?",
                "search_url = ?",
                "scraped_at = CURRENT_TIMESTAMP",
            ]
            params = [
                char.world_id, char.job, char.level, char.exp,
                char.rank, char.image_url, char.search_url,
            ]

            if image_path is not None:
                updates.append("image_path = ?")
                params.append(image_path)
            if guild is not None:
                updates.append("guild = ?")
                params.append(guild)
            if libb is not None:
                updates.append("libb = ?")
                params.append(1 if libb else 0)
            if amigo is not None:
                updates.append("amigo = ?")
                params.append(1 if amigo else 0)
            if legion_level is not None:
                updates.append("legion_level = ?")
                params.append(int(legion_level))

            params.append(existing["id"])
            conn.execute(
                f"UPDATE characters SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            return existing["id"]

        cur = conn.execute(
            """
            INSERT INTO characters
                (name, region, world, world_id, job, level, exp,
                 rank_position, image_url, ranking_type, search_url,
                 image_path, guild, libb, legion_level, amigo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                char.name, char.region, char.world, char.world_id,
                char.job, char.level, char.exp, char.rank,
                char.image_url, char.ranking_type, char.search_url,
                image_path, guild,
                libb if libb is not None else 0,
                legion_level,
                amigo if amigo is not None else 0,
            ),
        )
        return cur.lastrowid


def list_characters(limit: Optional[int] = None, offset: int = 0) -> list[sqlite3.Row]:
    """Return all characters: leaders first, then by level DESC, then exp DESC.

    Args:
        limit: Maximum number of rows to return (None = all).
        offset: Number of rows to skip.
    """
    with get_conn() as conn:
        sql = "SELECT * FROM characters ORDER BY leader DESC, level DESC, exp DESC, scraped_at DESC"
        params: tuple = ()
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params = (limit, offset)
        return list(conn.execute(sql, params))


def search_characters(query: str, limit: int = 8) -> list[sqlite3.Row]:
    """Search characters by name, job, world, level, or rank_position.

    Uses SQL LIKE for efficient searching.
    """
    q = f"%{query.lower()}%"
    with get_conn() as conn:
        return list(conn.execute(
            """
            SELECT * FROM characters
            WHERE lower(name) LIKE ? OR lower(job) LIKE ? OR lower(world) LIKE ?
               OR CAST(level AS TEXT) LIKE ? OR CAST(rank_position AS TEXT) LIKE ?
            ORDER BY leader DESC, level DESC, exp DESC
            LIMIT ?
            """,
            (q, q, q, q, q, limit),
        ))


def get_character(char_id: int) -> Optional[sqlite3.Row]:
    """Fetch a single character by id."""
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM characters WHERE id = ?", (char_id,))
        return cur.fetchone()


def get_random_character() -> Optional[sqlite3.Row]:
    """Fetch a random character from the database."""
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM characters ORDER BY RANDOM() LIMIT 1")
        return cur.fetchone()


def get_highest_level_character() -> Optional[sqlite3.Row]:
    """Fetch the character with the highest level in the database."""
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM characters ORDER BY level DESC, exp DESC LIMIT 1")
        return cur.fetchone()


def delete_character(char_id: int) -> bool:
    """Delete a character. Returns True if something was deleted."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM characters WHERE id = ?", (char_id,))
        return cur.rowcount > 0


def set_libb(char_id: int, libb: int) -> None:
    """Set the libb flag for a character (0 or 1)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE characters SET libb = ? WHERE id = ?",
            (1 if libb else 0, char_id),
        )


def set_leader(char_id: int, leader: int) -> None:
    """Set the leader flag for a character (0 or 1)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE characters SET leader = ? WHERE id = ?",
            (1 if leader else 0, char_id),
        )


def set_amigo(char_id: int, amigo: int) -> None:
    """Set the amigo flag for a character (0 or 1)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE characters SET amigo = ? WHERE id = ?",
            (1 if amigo else 0, char_id),
        )


def set_legion_level(char_id: int, legion_level: int) -> None:
    """Set the legion_level for a character."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE characters SET legion_level = ? WHERE id = ?",
            (int(legion_level), char_id),
        )


def record_exp_snapshot(char_id: int, exp: int, day: Optional[date] = None) -> None:
    """
    Record the character's exp for a given day (default: today).
    If a row already exists for (character_id, day) it is overwritten.
    """
    day_str = (day or date.today()).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO exp_history (character_id, exp, day)
            VALUES (?, ?, ?)
            ON CONFLICT(character_id, day) DO UPDATE SET exp = excluded.exp
            """,
            (char_id, exp, day_str),
        )


def get_exp_history(char_id: int, days: int = 14) -> list[dict]:
    """
    Return the last `days` daily exp snapshots for a character, oldest first.

    Each entry: {"day": "2024-05-20", "exp": 532..., "gain": 1_234_567 | None}.
    `gain` is the difference vs the previous snapshot, or None for the first
    entry (no prior data to compare against).
    """
    with get_conn() as conn:
        rows = list(conn.execute(
            "SELECT day, exp FROM exp_history "
            "WHERE character_id = ? ORDER BY day ASC",
            (char_id,),
        ))

    if days and len(rows) > days:
        rows = rows[-days:]

    history = []
    prev_exp: Optional[int] = None
    for day_str, exp in rows:
        gain = (exp - prev_exp) if prev_exp is not None else None
        history.append({"day": day_str, "exp": exp, "gain": gain})
        prev_exp = exp
    return history


def create_user(
    username: str, password: str, is_admin: bool = False
) -> Optional[int]:
    """
    Create a new user with a hashed password. Returns the new id, or None if
    the username is already taken.
    """
    pw_hash = generate_password_hash(password)
    with get_conn() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) "
                "VALUES (?, ?, ?)",
                (username, pw_hash, 1 if is_admin else 0),
            )
        except sqlite3.IntegrityError:
            return None
        return cur.lastrowid


def upsert_discord_user(discord_id: str, username: str, avatar: str, is_admin: bool = False) -> int:
    """
    Insert or update a Discord user. 
    If it's a new user and username collides, appends part of discord_id to username.
    """
    with get_conn() as conn:
        cur = conn.execute("SELECT id, is_admin FROM users WHERE discord_id = ?", (discord_id,))
        row = cur.fetchone()
        if row:
            # Update info, but never revoke admin here, only grant if requested
            new_is_admin = 1 if is_admin or row["is_admin"] else 0
            conn.execute(
                "UPDATE users SET username = ?, discord_avatar = ?, is_admin = ? WHERE id = ?",
                (username, avatar, new_is_admin, row["id"])
            )
            return row["id"]
        
        # Resolve username collision
        final_username = username
        while True:
            cur = conn.execute("SELECT id FROM users WHERE username = ?", (final_username,))
            if not cur.fetchone():
                break
            final_username = f"{username}_{discord_id[-4:]}"

        cur = conn.execute(
            "INSERT INTO users (username, password_hash, is_admin, discord_id, discord_avatar) "
            "VALUES (?, ?, ?, ?, ?)",
            (final_username, "discord_oauth", 1 if is_admin else 0, discord_id, avatar)
        )
        return cur.lastrowid


def get_user_by_username(username: str) -> Optional[dict]:
    """Return the user row for `username`, or None if not found."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, is_admin, created_at "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row else None


def insert_market_post(user_id: int, title: str, description: str, price: str, image_filename: str) -> int:
    """Insert a new market post and return its ID."""
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO market_posts (user_id, title, description, price, image_filename)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, title, description, price, image_filename)
        )
        return cur.lastrowid


def get_all_market_posts() -> list[dict]:
    """Return all market posts joined with their author's info, ordered by newest first."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.title, p.description, p.price, p.image_filename, p.created_at,
                   u.username, u.discord_avatar, p.user_id, u.discord_id
            FROM market_posts p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

def get_market_post_by_id(post_id: int) -> Optional[dict]:
    """Return a single market post with its author's info, or None."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT p.id, p.title, p.description, p.price, p.image_filename, p.created_at,
                   u.username, u.discord_avatar, p.user_id, u.discord_id
            FROM market_posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
            """,
            (post_id,)
        ).fetchone()
        return dict(row) if row else None

def delete_market_post(post_id: int) -> None:
    """Delete a market post by its ID."""
    with get_conn() as conn:
        conn.execute("DELETE FROM market_posts WHERE id = ?", (post_id,))

def get_user_by_id(user_id: int) -> Optional[dict]:
    """Return the user row for `user_id`, or None if not found."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, is_admin, created_at, discord_id "
            "FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def verify_user(username: str, password: str) -> Optional[dict]:
    """
    Return the user row if the password matches, else None.
    """
    user = get_user_by_username(username)
    if not user:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None
    return user


def list_users() -> list[dict]:
    """Return all users (without password hashes), newest first."""
    with get_conn() as conn:
        rows = list(conn.execute(
            "SELECT id, username, is_admin, created_at FROM users "
            "ORDER BY created_at DESC, id DESC"
        ))
    return [dict(r) for r in rows]


def update_user_password(user_id: int, new_password: str) -> None:
    """Hash and store a new password for the given user."""
    pw_hash = generate_password_hash(new_password)
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (pw_hash, user_id),
        )


def set_user_admin(user_id: int, is_admin: bool) -> None:
    """Toggle the admin flag for a user."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_admin = ? WHERE id = ?",
            (1 if is_admin else 0, user_id),
        )


def delete_user(user_id: int) -> None:
    """Delete a user by id."""
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


def get_all_weekly_exp_gains() -> dict[int, int]:
    """
    Return a dict of {character_id: weekly_exp_gain} for all characters.
    The weekly gain is calculated as the difference between the most recent EXP
    and the EXP from the earliest snapshot in the last 8 days.
    """
    from datetime import date, timedelta
    start_date = (date.today() - timedelta(days=8)).isoformat()
    with get_conn() as conn:
        rows = list(conn.execute(
            "SELECT character_id, exp, day FROM exp_history "
            "WHERE day >= ? "
            "ORDER BY character_id, day ASC",
            (start_date,),
        ))
    
    grouped = {}
    for r in rows:
        cid = r["character_id"]
        if cid not in grouped:
            grouped[cid] = []
        grouped[cid].append(r["exp"])
        
    gains = {}
    for cid, exps in grouped.items():
        if len(exps) >= 2:
            gains[cid] = exps[-1] - exps[0]
        else:
            gains[cid] = 0
    return gains

