# Carpediem - MapleStory Guild Tracker

**Stack:** Flask + Bootstrap 5 (dark mode) + SQLite + APScheduler
**Purpose:** Track MapleStory (GMS Luna/Europe) character rankings, EXP history, legion levels, and guild roster with "Liberado/Líder" flags.

---

## Project Structure

```
carpediem/
├── app.py              # Main Flask app, routes, filters, scrapers integration
├── db.py               # SQLite operations (characters, users, exp_history)
├── scraper.py          # Nexon ranking scraping (character, legion, EXP TNL)
├── scheduler.py        # APScheduler daily snapshots (03:00 UTC)
├── main.py             # Replit entry point (gunicorn)
├── requirements.txt
├── .replit             # Replit config
├── templates/
│   ├── base.html       # Layout, navbar, search dropdown, background FX
│   ├── index.html      # Character cards grid
│   ├── character.html  # Detail page (EXP chart, progress bar, LIBERADO mark)
│   ├── dashboard.html  # Admin bulk-edit (libb/leader/delete)
│   ├── addpj.html      # Hidden add-char page (comma-separated names)
│   ├── login.html
│   └── 404.html
├── static/
│   └── style.css       # Custom theme (MapleStory purple/blue), animations
├── instance/
│   ├── carpediem.db    # SQLite (gitignored)
│   └── images/         # Character portraits (gitignored)
└── instance/imgmaple/  # Job class background images (webp)
```

---

## Key Features

| Feature | Route | Notes |
|---------|-------|-------|
| Character list | `/` | Grid cards with job backgrounds |
| Character detail | `/characters/<id>` | EXP chart (14d), progress bar, LIBERADO mark |
| Dashboard (admin) | `/dashboard` | Toggle Liberado/Líder, delete, scrape legion |
| Add characters | `/addpj` | Hidden, comma-separated names, auto-scrape |
| Live search | `/api/search?q=` | Navbar dropdown, searches name/job/world/level |
| Legion bulk scrape | `/dashboard/scrape-legion` | World-paginated, efficient |
| Auto daily snapshot | Scheduler | 03:00 UTC, records EXP for history chart |

---

## Data Model (SQLite)

**characters**
- `id`, `name`, `job`, `level`, `exp`, `world`, `region`, `ranking_type`
- `image_path`, `search_url`, `libb` (bool), `leader` (bool)
- `legion_level`, `rank_position`, `updated_at`

**exp_history**
- `id`, `character_id`, `exp`, `gain`, `recorded_at` (daily snapshots)

**users**
- `id`, `username`, `password_hash`, `is_admin`

---

## Styling System (style.css)

**CSS Variables (MapleStory Theme):**
```css
--ms-purple: #A855F7;      --ms-purple-glow: #C084FC;
--ms-blue: #3B82F6;        --ms-blue-glow: #60A5FA;
--ms-gradient: linear-gradient(135deg, var(--ms-purple), var(--ms-blue));
--bg: #0f172a;             --bg-card-2: #1e293b;
```

**Background Layers (7):**
1. Animated gradient mesh (5 radial gradients, 20s)
2. Color wash gradient (30s)
3. Grid pattern (80px, 40s)
4. SVG noise texture (8s)
5. Vignette (radial)
6. Floating particles (6 orbs, organic drift)
7. Twinkling stars (~80, JS-generated)

**Respects `prefers-reduced-motion`** - all animations disable.

---

## Jinja2 Filters (app.py)

| Filter | Use Case |
|--------|----------|
| `format_short` | `76340927848138` → `76.3T` (k/M/B/T) |
| `job_img` | Returns `/instance/imgmaple/<job>.webp` URL |

---

## Scraper (scraper.py)

- **Target:** `nexon.com/maplestory/rankings/europe/world-ranking/luna`
- **Mode:** Interactive world, character-name search
- **Selectors:** Fragile - depends on Nexon HTML structure
- **Rate limit:** Be respectful; bulk legion uses paginated world scan

**Character fields scraped:** name, job, level, exp, world, ranking_type, image_url, legion_level

---

## Authentication

- Simple session-based (Flask `session`)
- Default admin: `admin` / `CARPEDIEM_ADMIN_PASSWORD` env var
- Decorators: `@login_required`, `@admin_required`
- Context processor injects `current_user` into all templates

---

## Deployment (Replit)

**Files needed:**
- `main.py` → `gunicorn --bind 0.0.0.0:8080 main:app`
- `.replit` config with `SECRET_KEY`, `CARPEDIEM_ADMIN_PASSWORD` in Secrets
- DB/images in `/home/runner/<repl>/data/` (persistent)

**Scheduler note:** Free Replit sleeps → daily snapshot pauses. Use Replit Deployments (Always On) or external cron.

---

## Common Tasks

**Add character manually:**
```bash
# Via /addpj page (admin only) or:
python -c "
from app import app, db
from scraper import scrape_character
with app.app_context():
    char = scrape_character('https://.../search=Nombre')
    db.upsert_character(char, libb=1)
"
```

**Reset DB:**
```bash
rm instance/carpediem.db
python -c "import db; db.init_db()"
```

**Run locally:**
```bash
pip install -r requirements.txt
python app.py  # http://127.0.0.1:5000
```

---

## Known Limitations

- Scraper breaks if Nexon changes HTML
- No API key - relies on public ranking pages
- EXP TNL table hardcoded up to Lv 300 (scraper.get_exp_tnl)
- Images stored locally (ephemeral on Replit free tier)
- Single-threaded scraper; bulk legion can take minutes

---

## Extending Ideas

- Discord webhook on level up
- Guild weekly EXP report (PDF/image)
- Character comparison view
- PWA manifest for mobile install
- Dark/light theme toggle (currently dark-only)