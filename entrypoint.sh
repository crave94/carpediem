#!/bin/sh
# Initialise the SQLite DB and ensure an admin user exists
python - <<'PY'
import db, os

db.init_db()
if not db.get_user_by_username('admin'):
    db.create_user('admin', os.getenv('CARPEDIEM_ADMIN_PASSWORD', 'carpediem'), is_admin=True)
PY

# Finally start the Flask app via gunicorn
exec gunicorn --workers 1 --threads 4 --bind 0.0.0.0:${PORT:-8001} main:app
