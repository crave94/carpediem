#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------
# 1️⃣  Variables – cámbialas según corresponda
# -------------------------------------------------
REPO_URL="https://github.com/crave94/carpediem.git"
APP_DIR="/var/www/carpediem"
VENV_DIR="${APP_DIR}/venv"

# Copia tus secretos aquí (puedes también usar un .env)
export SECRET_KEY="WklB5qRzY8t5Z2tP2D0x5G9YVjI0bU9iY3VwTkt4MzJkT1VhM0VNR2VGVzh6Nw=="
export CARPEDIEM_ADMIN_PASSWORD="carpediem"
export CARPEDIEM_SCHEDULER=1            # 1 = habilitar scheduler
export PORT=8000

# -------------------------------------------------
# 2️⃣  Preparar el sistema
# -------------------------------------------------
apt-get update
apt-get install -y python3-venv python3-pip git

# -------------------------------------------------
# 3️⃣  Obtener el código
# -------------------------------------------------
if [[ -d "${APP_DIR}" ]]; then
    echo "📂 El directorio ya existe → actualizando"
    cd "${APP_DIR}"
    git fetch --all
    git reset --hard origin/main
else
    echo "📦 Clonando repositorio"
    git clone "${REPO_URL}" "${APP_DIR}"
    cd "${APP_DIR}"
fi

# -------------------------------------------------
# 4️⃣  Entorno virtual e instalación de dependencias
# -------------------------------------------------
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt

# -------------------------------------------------
# 5️⃣  Inicializar la base de datos (crea tablas si no existen)
# -------------------------------------------------
python -c 'import db; db.init_db()'

# -------------------------------------------------
# 6️⃣  Crear el archivo de servicio systemd
# -------------------------------------------------
SERVICE_FILE="/etc/systemd/system/carpediem.service"
cat <<'EOF' > "${SERVICE_FILE}"
[Unit]
Description=Carpediem Flask App
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/carpediem
Environment=SECRET_KEY=${SECRET_KEY}
Environment=CARPEDIEM_ADMIN_PASSWORD=${CARPEDIEM_ADMIN_PASSWORD}
Environment=CARPEDIEM_SCHEDULER=${CARPEDIEM_SCHEDULER}
Environment=PORT=${PORT}
ExecStart=/var/www/carpediem/venv/bin/gunicorn --workers 2 --threads 4 --bind 127.0.0.1:${PORT} main:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# -------------------------------------------------
# 7️⃣  Recargar systemd y habilitar el servicio
# -------------------------------------------------
systemctl daemon-reload
systemctl enable carpediem.service
systemctl restart carpediem.service

# -------------------------------------------------
# 8️⃣  Verificar que el servicio está activo
# -------------------------------------------------
systemctl status carpediem.service --no-pager

set -euo pipefail

# -------------------------------------------------
# 1️⃣  Variables – cámbialas según corresponda
# -------------------------------------------------
REPO_URL="https://github.com/crave94/carpediem.git"
APP_DIR="/var/www/carpediem"
VENV_DIR="${APP_DIR}/venv"

# Copia tus secretos aquí (puedes también usar un .env)
export SECRET_KEY="WklB5qRzY8t5Z2tP2D0x5G9YVjI0bU9iY3VwTkt4MzJkT1VhM0VNR2VGVzh6Nw=="
export CARPEDIEM_ADMIN_PASSWORD="carpediem"
export CARPEDIEM_SCHEDULER=1            # 1 = habilitar scheduler
export PORT=8000

# -------------------------------------------------
# 2️⃣  Preparar el sistema
# -------------------------------------------------
apt-get update
apt-get install -y python3-venv python3-pip git

# -------------------------------------------------
# 3️⃣  Obtener el código
# -------------------------------------------------
if [[ -d "${APP_DIR}" ]]; then
    echo "📂 El directorio ya existe → actualizando"
    cd "${APP_DIR}"
    git fetch --all
    git reset --hard origin/main
else
    echo "📦 Clonando repositorio"
    git clone "${REPO_URL}" "${APP_DIR}"
    cd "${APP_DIR}"
fi

# -------------------------------------------------
# 4️⃣  Entorno virtual e instalación de dependencias
# -------------------------------------------------
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt

# -------------------------------------------------
# 5️⃣  Inicializar la base de datos (crea tablas si no existen)
# -------------------------------------------------
python -c 'import db; db.init_db()'

# -------------------------------------------------
# 6️⃣  Crear el archivo de servicio systemd
# -------------------------------------------------
SERVICE_FILE="/etc/systemd/system/carpediem.service"
cat <<'EOF' > "${SERVICE_FILE}"
[Unit]
Description=Carpediem Flask App
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/carpediem
Environment=SECRET_KEY=${SECRET_KEY}
Environment=CARPEDIEM_ADMIN_PASSWORD=${CARPEDIEM_ADMIN_PASSWORD}
Environment=CARPEDIEM_SCHEDULER=${CARPEDIEM_SCHEDULER}
Environment=PORT=${PORT}
ExecStart=/var/www/carpediem/venv/bin/gunicorn --workers 2 --threads 4 --bind 127.0.0.1:${PORT} main:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# -------------------------------------------------
# 7️⃣  Recargar systemd y habilitar el servicio
# -------------------------------------------------
systemctl daemon-reload
systemctl enable carpediem.service
systemctl restart carpediem.service

# -------------------------------------------------
# 8️⃣  Verificar que el servicio está activo
# -------------------------------------------------
systemctl status carpediem.service --no-pager

set -euo pipefail

# -------------------------------------------------
# 1️⃣  Variables – cámbialas según corresponda
# -------------------------------------------------
REPO_URL="https://github.com/crave94/carpediem.git"
APP_DIR="/var/www/carpediem"
VENV_DIR="${APP_DIR}/venv"

# Copia tus secretos aquí (puedes también usar un .env)
export SECRET_KEY="WklB5qRzY8t5Z2tP2D0x5G9YVjI0bU9iY3VwTkt4MzJkT1VhM0VNR2VGVzh6Nw=="
export CARPEDIEM_ADMIN_PASSWORD="carpediem"
export CARPEDIEM_SCHEDULER=1            # 1 = habilitar scheduler
export PORT=8000

# -------------------------------------------------
# 2️⃣  Preparar el sistema
# -------------------------------------------------
apt-get update
apt-get install -y python3-venv python3-pip git

# -------------------------------------------------
# 3️⃣  Obtener el código
# -------------------------------------------------
if [[ -d "${APP_DIR}" ]]; then
    echo "📂 El directorio ya existe → actualizando"
    cd "${APP_DIR}"
    git fetch --all
    git reset --hard origin/main
else
    echo "📦 Clonando repositorio"
    git clone "${REPO_URL}" "${APP_DIR}"
    cd "${APP_DIR}"
fi

# -------------------------------------------------
# 4️⃣  Entorno virtual e instalación de dependencias
# -------------------------------------------------
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt

# -------------------------------------------------
# 5️⃣  Inicializar la base de datos (crea tablas si no existen)
# -------------------------------------------------
python -c 'import db; db.init_db()'

# -------------------------------------------------
# 6️⃣  Crear el archivo de servicio systemd
# -------------------------------------------------
SERVICE_FILE="/etc/systemd/system/carpediem.service"
cat <<'EOF' > "${SERVICE_FILE}"
[Unit]
Description=Carpediem Flask App
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/carpediem
Environment=SECRET_KEY=${SECRET_KEY}
Environment=CARPEDIEM_ADMIN_PASSWORD=${CARPEDIEM_ADMIN_PASSWORD}
Environment=CARPEDIEM_SCHEDULER=${CARPEDIEM_SCHEDULER}
Environment=PORT=${PORT}
ExecStart=/var/www/carpediem/venv/bin/gunicorn --workers 2 --threads 4 --bind 127.0.0.1:${PORT} main:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# -------------------------------------------------
# 7️⃣  Recargar systemd y habilitar el servicio
# -------------------------------------------------
systemctl daemon-reload
systemctl enable carpediem.service
systemctl restart carpediem.service

# -------------------------------------------------
# 8️⃣  Verificar que el servicio está activo
# -------------------------------------------------
systemctl status carpediem.service --no-pager
