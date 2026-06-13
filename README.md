# Carpediem

Mini web app en Python (Flask + SQLite) que scrapea la página oficial de
rankings de [MapleStory Global](https://www.nexon.com/maplestory/rankings/)
para extraer la **imagen, nivel, experiencia, job, rank y mundo** de un
personaje, y los guarda en una base de datos local.

## Cómo funciona (TL;DR)

La página de Nexon es una SPA Vue.js que carga los datos desde un endpoint
interno. En lugar de parsear HTML, el scraper hace la misma llamada a la API
que hace el navegador:

```
GET https://www.nexon.com/api/maplestory/no-auth/ranking/v2/{region}
    ?type={overall|achievement|fame|job|legion|world}
    &id={worldId|filter}
    &reboot_index={0=both | 1=heroic | 2=interactive}
    &page_index={n}
    &character_name={name}
```

Descubierto inspeccionando `web.nxfs.nexon.com/maplestory/assets/index-CfVsgydV.js`.

## Estructura

```
carpediem/
├── app.py                # Flask: rutas, form, renderizado
├── scraper.py            # Parseo de URL + llamada a la API + dataclass Character
├── db.py                 # SQLite (sin ORM, sqlite3 puro)
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html        # Form + grid de personajes guardados
│   ├── character.html    # Detalle (imagen, stats, refresh, delete, chart 14d)
│   ├── dashboard.html    # Bulk-edit + scrape masivo de legion
│   ├── addpj.html        # Form oculto para agregar personajes
│   └── 404.html
├── static/
│   └── style.css
└── instance/             # Auto-creada
    ├── maplestory.db
    └── images/           # Avatares descargados
```

## Instalación

```powershell
# 1) Instalar dependencias
pip install -r requirements.txt

# 2) Iniciar el servidor
python app.py
```

Luego abrí <http://127.0.0.1:5000> en el navegador.

## Uso

1. Abrí <http://127.0.0.1:5000> en el navegador. Ahí ves la grilla de
   personajes guardados.

2. Para agregar uno nuevo, andá a la página oculta
   <http://127.0.0.1:5000/addpj> (no está linkeada desde la navegación;
   tenés que tipear la URL o tenerla en bookmarks). Escribí el nombre
   del personaje (la URL está fijada a `europe/world-ranking/luna` con
   `world_type=interactive`). Ejemplo: `XenCzar`. Hacé clic en
   **Scrapear y guardar**.

3. El personaje aparece en la grilla con su avatar. Hacé clic para ver
   nivel, experiencia, job, rank y mundo. Podés **Refrescar** los datos o
   **Eliminar** el registro.

> Si querés cambiar el mundo o el tipo de ranking, editá
> `DEFAULT_RANKING_URL` en `app.py:59`. La ruta `/addpj` es la única vía
> para agregar personajes; `/scrape` ya no existe.

## Uso como CLI (opcional)

```powershell
python scraper.py "https://www.nexon.com/maplestory/rankings/europe/world-ranking/luna?world_type=interactive&page_index=1&search_type=character-name&search=XenCzar"
```

Imprime el JSON con todos los campos.

## Regiones y mundos soportados

| Región     | URL path         | Mundos                          |
|------------|------------------|---------------------------------|
| North America | `north-america` | bera, scania, kronos, hyperion |
| Europe     | `europe`         | luna, solis                     |

Si Nexon agrega mundos nuevos, agregalos en `WORLDS` dentro de `scraper.py`.

## Limitaciones

- **Guild no disponible para GMS**: el endpoint de ranking que usamos
  (`/api/maplestory/no-auth/ranking/v2/{region}`) no devuelve el nombre del
  guild del personaje. La OpenAPI oficial de Nexon sí expone ese campo, pero
  solo está disponible para KMS / TMS / MSEA. En GMS no hay forma pública de
  obtenerlo. La columna `guild` queda en `NULL` hasta nuevo aviso.
- Los avatares se descargan una vez desde `msavatar1.nexon.net`. La URL de la
  API puede cambiar; si lo hace, ajustá `API_BASE` en `scraper.py`.
- La API de Nexon es no documentada. Si rompe, va a haber que re-inspeccionar
  el bundle de la SPA.
- No hay rate limiting; si scrapeás miles de URLs seguidas podrías recibir
  un 429.

## Disclaimer

Esto usa un endpoint público de Nexon, pero **no es una API oficial soportada**.
Usalo con criterio. No afiliado a Nexon o MapleStory.
