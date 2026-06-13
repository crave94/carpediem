# Guía de Despliegue en Replit — Carpediem

**Proyecto:** Tracker de Guild MapleStory (GMS Luna/Europe)
**Stack:** Flask + SQLite + Bootstrap 5 + APScheduler
**Tiempo estimado:** 10-15 minutos

---

## 1. Preparación Local (Opcional)

```bash
# Verificar que todo funciona localmente
cd carpediem
pip install -r requirements.txt
python main.py
# Abrir http://127.0.0.1:5000
```

---

## 2. Subir a Replit

### Opción A: Importar desde GitHub (Recomendado)
1. Entra a [replit.com](https://replit.com) → **Create Repl**
2. Selecciona **Import from GitHub**
3. Pega la URL de tu repo: `https://github.com/TU_USUARIO/carpediem`
4. Click **Import from GitHub**

### Opción B: Subir archivos manualmente
1. Create Repl → **Python** → Ponle nombre `carpediem`
2. Arrastra TODOS los archivos del proyecto (incluye carpetas `templates/`, `static/`, `instance/imgmaple/`)
3. **Importante:** La carpeta `instance/images/` NO la subas (se crea sola), pero `instance/imgmaple/` SÍ (contiene las imágenes de jobs)

---

## 3. Configurar Secrets (🔒 Icono lateral izquierdo)

| Secret | Valor | Descripción |
|--------|-------|-------------|
| `SECRET_KEY` | `openssl rand -hex 32` | Clave secreta Flask (genera una aleatoria) |
| `CARPEDIEM_ADMIN_PASSWORD` | `tu_password_seguro` | Password del usuario admin por defecto |
| `CARPEDIEM_SCHEDULER` | `0` | **Deja en 0** para Deployments (ver paso 6) |

> **Generar SECRET_KEY:** En terminal local: `python -c "import secrets; print(secrets.token_hex(32))"`

---

## 4. Verificar Estructura de Archivos

```
carpediem/                    ← Root del Repl
├── main.py                   ← Entry point (gunicorn lo usa)
├── app.py                    ← Flask app
├── db.py                     ← SQLite layer
├── scraper.py                ← Nexon scraping
├── scheduler.py              ← Background jobs
├── requirements.txt          ← Dependencias
├── .replit                   ← Config Replit
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── character.html
│   ├── dashboard.html
│   ├── addpj.html
│   ├── login.html
│   └── 404.html
├── static/
│   └── style.css
├── instance/
│   └── imgmaple/             ← 60+ archivos .webp (jobs)
└── data/                     ← Se crea solo (DB + images)
```

---

## 5. Primer Run (Botón ▶ Run)

1. Click **Run** (botón verde arriba)
2. Replit hará `pip install -r requirements.txt` automáticamente
3. Verás logs en la consola:
   ```
   [carpediem] Default admin user created — username='admin' password='...'
   * Running on http://0.0.0.0:8080
   ```
4. Abre la pestaña **Webview** (o click en la URL que aparece)

**Prueba:**
- Login: `admin` / tu `CARPEDIEM_ADMIN_PASSWORD`
- Agrega un personaje en `/addpj` (ej: `XenCzar`)
- Verifica que scrapea y guarda

---

## 6. Deploy a Producción (Deployments)

> **Gratis:** Replit "Autoscale Deployments" duerme tras inactividad.
> **Pago ($7/mes):** "Reserved VM Deployment" = Always On + scheduler funcionando.

### Pasos:
1. Botón **Deploy** (esquina sup. der.) → **Deployments**
2. Selecciona **Autoscale** (gratis) o **Reserved VM** (pago)
3. **Build Command:** (deja vacío, usa requirements.txt)
4. **Run Command:** (usa el de `.replit` → `gunicorn --bind 0.0.0.0:8080 ...`)
5. **Secrets:** Se copian automáticamente del Repl
6. Click **Deploy**

### ⚠️ IMPORTANTE: Scheduler en Producción

| Plan | Configuración |
|------|---------------|
| **Autoscale (gratis)** | `CARPEDIEM_SCHEDULER=0` (NO uses scheduler; el repl duerme) |
| **Reserved VM (pago)** | `CARPEDIEM_SCHEDULER=1` en **UN SOLO** replica |

**Para habilitar scheduler en Reserved VM:**
1. En Deployment settings → **Secrets** → Agrega `CARPEDIEM_SCHEDULER=1`
2. **Scale:** Pon **Min replicas = 1, Max replicas = 1** (evita schedulers duplicados)
3. Redeploy

---

## 7. Verificación Post-Deploy

| Check | Cómo probar |
|-------|-------------|
| Web carga | Abre URL del deployment |
| Login | `admin` / password |
| Scrape personaje | Ve a `/addpj`, pon `XenCzar`, submit |
| Ver detalle | Click "Ver" en lista → gráfica EXP |
| Dashboard admin | `/dashboard` → toggle Liberado/Líder |
| Búsqueda navbar | Ctrl+K → escribe nombre |

---

## 8. Troubleshooting Común

### "ModuleNotFoundError: scraper"
→ Verifica que `scraper.py` está en root del Repl (no en subcarpeta).

### "Database is locked" / "no such table"
→ El path `data/` no se crea. En Shell de Replit:
```bash
mkdir -p ~/carpediem_data
ls -la ~/carpediem_data/
```
Debe aparecer `maplestory.db` tras primer scrape.

### Imágenes de jobs no cargan (404)
→ Falta carpeta `instance/imgmaple/` con los `.webp`. Sube todos los archivos de `instance/imgmaple/` local.

### Modal login oscurecido / no interactuable
→ Ya solucionado en `style.css` (z-index -100 para fondos). Si persiste: refresca cache (Ctrl+Shift+R).

### Scheduler no corre
- Autoscale gratis: **Normal**, el repl duerme.
- Reserved VM: Revisa `CARPEDIEM_SCHEDULER=1` y **Max replicas = 1**.

### Error 500 en `/api/search`
→ Logs en consola del Deployment. Común: Nexon cambió HTML → actualiza `scraper.py` selectores.

---

## 9. Mantenimiento

### Actualizar código
1. Push a GitHub → Replit auto-sync (si importaste desde GitHub)
2. O edita directo en Replit → Botón **Deploy** → **Redeploy**

### Backup DB (manual)
```bash
# En Shell de Replit
cp ~/carpediem_data/maplestory.db ~/carpediem_data/backup_$(date +%F).db
```

### Cambiar password admin
```bash
# En Shell de Replit
python3 -c "
import sqlite3, os
from werkzeug.security import generate_password_hash
db = os.path.expanduser('~/carpediem_data/maplestory.db')
conn = sqlite3.connect(db)
conn.execute('UPDATE users SET password_hash=? WHERE username=?',
             (generate_password_hash('NUEVO_PASSWORD'), 'admin'))
conn.commit()
print('Password actualizado')
"
```

---

## 10. Archivos Clave Creados/Modificados

| Archivo | Cambio |
|---------|--------|
| `main.py` | Entry point gunicorn + carga .env + scheduler opcional |
| `.replit` | Config run/deploy + secrets docs |
| `requirements.txt` | Agregado gunicorn, apscheduler, beautifulsoup4, lxml |
| `db.py` | `DB_PATH` usa `REPL_HOME` → `~/data/maplestory.db` (persistente) |
| `app.py` | `IMAGE_DIR` usa mismo `_DATA_DIR` que `db.py` |

---

## Contacto / Soporte

- **Issues:** GitHub Issues del repo
- **Logs:** Consola Replit (desarrollo) / Deployment Logs (producción)
- **Nexon API:** Pública, sin key, rate-limit no documentado → sé respetuoso

---

*Generado automáticamente — Carpediem MapleStory Guild Tracker*