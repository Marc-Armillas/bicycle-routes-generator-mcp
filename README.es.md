# Bicycle routes generator MCP

[English](README.md) · **Español**

**[⬇️ Descargar la extensión para Claude Desktop (bicycle-routes-generator-mcp.mcpb)](https://github.com/Marc-Armillas/bicycle-routes-generator-mcp/releases/latest/download/bicycle-routes-generator-mcp.mcpb)**

Genera rutas de **bicicleta de montaña** y de **carretera** a partir de un lugar y las guarda
como **GPX con elevación**. El trazado lo calcula un motor de rutas (BRouter u
OpenRouteService) sobre **caminos y carreteras reales de OpenStreetMap**: ni la IA ni la
aplicación inventan coordenadas.

Se puede usar:

- **Con Claude** (Claude Desktop o Claude Code) mediante un servidor MCP local: «hazme una
  ruta circular de BTT de ~25 km desde la Casa de Campo de Madrid, poco desnivel, por pistas»
  (mira [qué pasa cuando se lo pides a Claude](#ejemplo-qué-pasa-cuando-se-lo-pides-a-claude)).
- **Desde la terminal**, sin IA: `bicycle-routes generate "Casa de Campo, Madrid" --km 25 --type tracks`.

Cada ruta devuelve un resumen (distancia, desnivel, pendiente máxima, % de asfalto, pista y
senda) y **avisos**: tramos con tráfico, pendientes superiores al 12 %, zonas protegidas,
caminos donde la bici no está permitida y tramos técnicos. El código y los mensajes de la
aplicación están en inglés; Claude te los presenta en tu idioma.

> 💾 **Los GPX se guardan por defecto en `/tmp/bicycle-routes`.** macOS vacía `/tmp` al reiniciar y
> borra los archivos antiguos, así que copia las rutas que quieras conservar (o cambia
> `BIKE_GPX_DIR` a otra carpeta).

> ⚠️ **Revisa siempre la ruta en un mapa antes de salir.** Los datos de OpenStreetMap pueden
> estar incompletos o desactualizados, y no reflejan cierres temporales ni toda la normativa
> local. El desnivel se calcula con un modelo digital de elevación (~90 m) y **puede diferir
> del que mida un reloj o ciclocomputador con barómetro** (a menudo un 10-20 %); las rampas
> cortas pueden quedar suavizadas.

## Instalación fácil en Claude Desktop (extensión `.mcpb`)

1. [Descarga `bicycle-routes-generator-mcp.mcpb`](https://github.com/Marc-Armillas/bicycle-routes-generator-mcp/releases/latest/download/bicycle-routes-generator-mcp.mcpb) (siempre la última versión), o genéralo con
   `npx @anthropic-ai/mcpb pack . dist/bicycle-routes-generator-mcp.mcpb`.
2. Haz doble clic en el archivo (o arrástralo a Claude Desktop → Ajustes → Extensiones) y pulsa
   **Instalar**.
3. Rellena la configuración: carpeta de los GPX (por defecto `/tmp/bicycle-routes`) y un email de contacto
   (lo exige la política de uso de OpenStreetMap/Nominatim). El resto de campos son opcionales.
4. Pídele a Claude: «hazme una ruta circular de BTT de 25 km desde la Casa de Campo de Madrid por pistas».

No hace falta instalar Python: la extensión es de tipo `uv` y Claude Desktop descarga Python y
las dependencias automáticamente la primera vez (puede tardar un minuto). El formato `.mcpb` es
el sucesor de `.dxt`; las versiones antiguas de Claude Desktop que solo admitan `.dxt` no
soportan extensiones de tipo `uv`.

## Instalación manual (CLI y Claude Code)

Requisitos: macOS, Windows o Linux con [uv](https://docs.astral.sh/uv/) (instala Python por ti).

```bash
git clone <url-del-repositorio> bicycle-routes-generator-mcp
cd bicycle-routes-generator-mcp
uv sync
cp .env.example .env   # y edítalo
```

### Configuración (variables de entorno)

No hay claves ni datos personales en el código: todo se configura con variables de entorno
(o un archivo `.env` en la carpeta desde la que ejecutas la CLI).

| Variable | Por defecto | Para qué |
|---|---|---|
| `BIKE_GPX_DIR` | `/tmp/bicycle-routes` | Carpeta donde se guardan los GPX. La app solo escribe aquí (y en su subcarpeta `.bicycle-routes/` con caché e índice). En Windows, por defecto es la carpeta temporal del sistema. |
| `BIKE_CONTACT` | — | Email o URL que se envía en el User-Agent. **Recomendado**: lo exige la política de Nominatim. |
| `BIKE_ENGINE` | `brouter` | `brouter` u `ors`. |
| `BIKE_BROUTER_URL` | `https://brouter.de` | Servidor BRouter (público o local, ver abajo). |
| `ORS_API_KEY` | — | Clave gratuita de [OpenRouteService](https://openrouteservice.org) si `BIKE_ENGINE=ors`. |
| `BIKE_PROTECTED_AREAS` | `1` | Comprobar zonas protegidas con Overpass API. |
| `BIKE_GARMIN_MCP_COMMAND` | — | Solo para `--garmin` en la CLI (ver «Garmin»). |
| `BIKE_DATA_DIR` | `<carpeta GPX>/.bicycle-routes` | Dónde guardar caché e índice. |

## Uso desde la terminal

```bash
uv run bicycle-routes generate "Casa de Campo, Madrid" --km 25 --type tracks --max-climb 500
uv run bicycle-routes generate "40.4242,-3.7559" --km 15            # también con coordenadas
uv run bicycle-routes generate "Casa de Campo, Madrid" --km 20 --end "El Pardo, Madrid"   # ruta lineal
uv run bicycle-routes generate "Casa de Campo, Madrid" --km 30 --via "El Pardo, Madrid" --via "Aravaca, Madrid"  # circular por puntos de paso
uv run bicycle-routes generate "Madrid" --km 60 --type road         # bici de carretera
uv run bicycle-routes generate "Casa de Campo, Madrid" --km 40 --seed 7   # otra alternativa reproducible
uv run bicycle-routes generate "Casa de Campo, Madrid" --km 25 --json     # salida JSON
uv run bicycle-routes list
```

Tipos de camino (`--type`):

- `tracks`: prioriza pistas anchas, poca senda y sin rampas extremas.
- `mixed` (por defecto): BTT general.
- `singletrack`: más senda y menos asfalto.
- `road`: bici de carretera. Carreteras asfaltadas con poco tráfico; avisa de los tramos sin
  asfaltar y solo de las vías muy transitadas (carreteras principales o con tráfico estimado
  alto), no de las secundarias normales.

Ejemplo real (resumido; la salida de la aplicación está en inglés):

```text
MTB Casa de Campo 38 km loop
  Start: Casa de Campo, Madrid, Comunidad de Madrid, España
  Distance: 37.8 km · Climbing: +336 m / -338 m · Elevation 615–725 m
  Max grade: 10.3 % uphill, 13.3 % downhill
  Surface: paved 28.8 % · track 40.6 % · singletrack 30.6 %
  Engine: brouter (mtb) · candidates evaluated: 6
  GPX: /tmp/bicycle-routes/mtb-casa-de-campo-38-km-loop-20261017-163919.gpx
  Warnings:
   - [traffic] 0.3 km on roads with motor traffic in 1 section(s); ride carefully.
   - [traffic] Road with traffic (km 27.3–27.6).
   - [grade] Steep descent over 12 % (max ~13 %, km 9.2–9.3).
   - [general] Climbing and grades come from a digital elevation model (~90 m resolution)…
   - [general] Route generated automatically from OpenStreetMap: check it on a map before riding…
```

Más ejemplos con salidas reales en [docs/pruebas-reales.md](docs/pruebas-reales.md).

## Uso con Claude (servidor MCP)

El servidor expone dos herramientas:

- `generate_route(start, distance_km, max_climb_m?, trail_type?, loop=true, end?, name?, seed?, via?)`
  → ruta del GPX, resumen y avisos. `via` es una lista de lugares por los que la ruta debe
  pasar, en orden (p. ej. "circular desde la Casa de Campo pasando por El Pardo y Aravaca").
- `list_routes()` → rutas guardadas.

### Ejemplo: qué pasa cuando se lo pides a Claude

**Tú:** *«Hazme una ruta circular de BTT de unos 40 km desde la Casa de Campo de Madrid.»*

**1. Claude llama a la herramienta**, eligiendo los argumentos a partir de lo que le pides:

```json
generate_route({ "start": "Casa de Campo, Madrid", "distance_km": 40, "trail_type": "mixed" })
```

**2. El servidor MCP calcula la ruta** en tu ordenador (entre 10 y 60 segundos):

1. Busca «Casa de Campo, Madrid» en Nominatim (OpenStreetMap) → `40.424, -3.756`.
2. Genera 6 rutas circulares candidatas con BRouter por caminos reales, ajustando cada una a
   unos 40 km.
3. Las puntúa (distancia, tráfico, caminos repetidos, superficie, accesos prohibidos, desnivel)
   y se queda con la mejor.
4. La analiza: desnivel, pendientes, superficie, tramos con tráfico, tramos técnicos y zonas
   protegidas (Overpass API).
5. Guarda el GPX con elevación en tu carpeta de GPX.

**3. Le devuelve esto a Claude** (salida real, resumida; obtenida con `"seed": 2026` para que se
pueda reproducir: sin semilla, cada petición da una ruta distinta):

```json
{
  "name": "MTB Casa de Campo 38 km loop",
  "gpx_file": "/tmp/bicycle-routes/mtb-casa-de-campo-38-km-loop-20261017-163919.gpx",
  "start": { "name": "Casa de Campo, Madrid, Comunidad de Madrid, España", "lat": 40.4241907, "lon": -3.755858 },
  "summary": {
    "distance_km": 37.8, "ascent_m": 336, "descent_m": 338,
    "min_elevation_m": 615, "max_elevation_m": 725,
    "max_uphill_grade_pct": 10.3, "max_downhill_grade_pct": 13.3,
    "surface_pct": { "paved": 28.8, "track": 40.6, "path": 30.6, "unknown": 0.0 },
    "warnings": [
      { "kind": "traffic", "message": "0.3 km on roads with motor traffic in 1 section(s); ride carefully." },
      { "kind": "traffic", "message": "Road with traffic (km 27.3–27.6).", "start_km": 27.32, "end_km": 27.61 },
      { "kind": "grade", "message": "Steep descent over 12 % (max ~13 %, km 9.2–9.3).", "start_km": 9.22, "end_km": 9.34 },
      { "kind": "general", "message": "Climbing and grades come from a digital elevation model (~90 m resolution)…" },
      { "kind": "general", "message": "Route generated automatically from OpenStreetMap: check it on a map before riding…" }
    ]
  },
  "engine": "brouter (mtb)",
  "activity_type": "mountain_biking",
  "candidates_evaluated": 6,
  "attribution": "Trail data © OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright"
}
```

**4. Claude te responde** en tu idioma, con el resumen y todos los avisos. Por ejemplo
(ilustrativo; la redacción de Claude varía):

> He creado una **ruta circular de 37,8 km** desde la Casa de Campo con **+336 m** de desnivel:
> 41 % pista, 31 % senda y 29 % asfalto. Ten cuidado con **0,3 km por una carretera con
> tráfico** (km 27,3–27,6) y con una **bajada pronunciada de ~13 %** en el km 9,2. El desnivel
> sale de un modelo de elevación y puede diferir del de tu reloj, así que revisa la ruta en un
> mapa antes de salir. GPX: `/tmp/bicycle-routes/mtb-casa-de-campo-38-km-loop-20261017-163919.gpx`

A partir de ahí puedes seguir en la misma conversación:

| Tú dices | Lo que hace Claude |
|---|---|
| «Dame otra opción» | Vuelve a llamar a `generate_route` con otra `seed` |
| «Con menos desnivel, 200 m como mucho» | Añade `max_climb_m: 200` |
| «Que pase por El Pardo» | Añade `via: ["El Pardo, Madrid"]` |
| «Ahora una de carretera de 60 km desde Madrid» | Usa `trail_type: "road"` (asfalto y poco tráfico) |
| «Súbela a Garmin» | Llama a `upload_course` del MCP de Garmin con el GPX, si lo tienes instalado |
| «¿Qué rutas tengo guardadas?» | Llama a `list_routes` |

### Claude Code

```bash
claude mcp add bicycle-routes-generator-mcp \
  -e BIKE_GPX_DIR=/tmp/bicycle-routes -e BIKE_CONTACT=tu-email@ejemplo.com \
  -- uv run --directory /ruta/a/bicycle-routes-generator-mcp bicycle-routes-mcp
```

### Claude Desktop (sin extensión)

Lo más sencillo es la extensión `.mcpb` (ver arriba). Si prefieres configurarlo a mano:
Ajustes → Desarrollador → Editar configuración (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "bicycle-routes-generator-mcp": {
      "command": "/ruta/absoluta/a/uv",
      "args": ["run", "--directory", "/ruta/a/bicycle-routes-generator-mcp", "bicycle-routes-mcp"],
      "env": {
        "BIKE_GPX_DIR": "/tmp/bicycle-routes",
        "BIKE_CONTACT": "tu-email@ejemplo.com"
      }
    }
  }
}
```

Usa la ruta absoluta de `uv` (`which uv` en macOS/Linux, `where uv` en Windows), porque
Claude Desktop no siempre hereda el `PATH` de la terminal. Reinicia Claude Desktop.

### Generar la extensión

`manifest.json` describe la extensión (tipo `uv`, herramientas y campos de configuración) y
`.mcpbignore` excluye del paquete los tests, la documentación y tu `.env`.

```bash
npx @anthropic-ai/mcpb validate manifest.json
npx @anthropic-ai/mcpb pack . dist/bicycle-routes-generator-mcp.mcpb
python scripts/make_icon.py    # solo si quieres regenerar icon.png
```

### Publicar una versión

1. Sube `version` a la vez en `manifest.json`, `pyproject.toml` y `src/bicycle_routes/__init__.py`.
2. Crea y sube una etiqueta con esa versión:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. El flujo `Release` de GitHub Actions ejecuta los tests, genera `bicycle-routes-generator-mcp.mcpb` y lo adjunta
   a una nueva Release de GitHub. El enlace de descarga del principio de este README apunta
   siempre a la última.
4. Un segundo job publica esa versión en el
   [registro oficial de MCP](https://registry.modelcontextprotocol.io) como
   `io.github.Marc-Armillas/bicycle-routes-generator-mcp`: rellena `server.json` con la versión,
   la URL de la release y el SHA-256 del `.mcpb`, y se autentica con GitHub OIDC (sin secretos).
   Si el registro lo rechaza, la Release de GitHub ya está publicada.

## Garmin, Wahoo y otras plataformas

La aplicación es independiente de cualquier plataforma: el resultado es un GPX estándar. Los
envíos a plataformas son **exportadores** opcionales con una interfaz común
(`export(route, config) -> ExportResult`, en `src/bicycle_routes/exporters/`).

- **disk** (por defecto): guarda el GPX en `BIKE_GPX_DIR`.
- **garmin**: delega en un servidor MCP de Garmin ya instalado (herramienta `upload_course`).
  - *Con Claude (recomendado)*: no hay que configurar nada. Pide «súbela a Garmin» y Claude
    llamará a `upload_course` del MCP de Garmin con el GPX generado y
    `activity_type="mountain_biking"` (`"road_biking"` en rutas de carretera).
  - *Desde la CLI*: define `BIKE_GARMIN_MCP_COMMAND` con el comando que arranca ese servidor y
    usa `--garmin`. Las credenciales de Garmin las gestiona ese servidor, nunca esta app.
  - Los MCP de Garmin comunitarios usan la API web no oficial de Garmin Connect y pueden dejar
    de funcionar. La API oficial (Courses API) es solo para empresas aprobadas.
- **wahoo**: no implementado. La Cloud API tiene `POST /v1/routes`, pero requiere solicitar y
  obtener la aprobación de una app (notas en `exporters/wahoo.py`).
- **Komoot** (API solo para socios con contrato) y **Strava** (su API no permite crear rutas):
  importa el GPX manualmente en su web.

## Motores de rutas

- **BRouter** (por defecto, MIT, sin clave). Usa el perfil `mtb` con
  `StrictNOBicycleaccess=1` (evita caminos con `bicycle=no`) y `avoid_unsafe=1`; para `road`,
  el perfil `fastbike` con `consider_traffic=1` (mismas rutas que `fastbike-lowtraffic`). El servidor
  público `brouter.de` no garantiza disponibilidad: la app hace como máximo 1 petición por
  segundo y cachea las respuestas. Para uso intensivo, levanta uno local (no probado aún en
  este proyecto):

  ```bash
  mkdir -p segments4
  curl -o segments4/W5_N40.rd5 https://brouter.de/brouter/segments4/W5_N40.rd5   # Madrid y centro peninsular
  docker run -d -p 17777:17777 -v "$PWD/segments4:/segments4" ghcr.io/abrensch/brouter
  # y en .env: BIKE_BROUTER_URL=http://localhost:17777
  ```

- **OpenRouteService** (opcional): `BIKE_ENGINE=ors` y `ORS_API_KEY` (plan gratuito: 2.000
  rutas/día, 40/min). Perfil `cycling-mountain`, o `cycling-road` para `road`.

### Cómo se genera la ruta circular

1. El lugar se convierte en coordenadas con Nominatim (o se usan las que des).
2. Se colocan 3-4 puntos de paso sobre un círculo que pasa por el inicio, con orientación
   aleatoria (reproducible con `--seed`).
3. El motor calcula inicio → puntos → inicio por caminos reales.
4. Se ajusta el radio hasta acercarse a la distancia pedida (unas 2-4 peticiones).
5. Se generan 6 candidatas y se elige la mejor según distancia, tráfico, caminos repetidos,
   superficie, accesos prohibidos, desnivel y pendientes.

Con puntos de paso (`--via` / `via`), los puntos aleatorios se sustituyen por los tuyos: el
motor calcula inicio → via 1 → … → via N → inicio (o → final, si es lineal), en el orden
dado. La distancia la marcan esos puntos, no `--km`; si difiere más de un 15 % se avisa.

## Servicios externos y sus políticas

- **Nominatim** (búsqueda de lugares): [política de uso](https://operations.osmfoundation.org/policies/nominatim/).
  Máximo 1 petición/segundo, User-Agent identificativo, resultados cacheados, sin
  autocompletado ni consultas masivas. Para uso intensivo, instala tu propio Nominatim.
- **Overpass API** (zonas protegidas): ≈10.000 peticiones/día por IP como pauta; una consulta
  por ruta, cacheada.
- **brouter.de**: servidor público sin garantías; usa uno local para uso intensivo.

## Desarrollo

```bash
uv run pytest              # tests con motor, geocodificador y zonas simulados (sin red)
uv run pytest -m network   # prueba opcional contra los servicios reales
```

Estructura:

```text
src/bicycle_routes/
├── core/            # modelos, generador de bucles, análisis y GPX (sin red ni plataformas)
├── engines/         # BRouter y OpenRouteService (interfaz RoutingEngine)
├── geo/             # Nominatim y zonas protegidas (Overpass)
├── exporters/       # disk, garmin (vía MCP), wahoo (pendiente)
├── net.py           # cliente HTTP: User-Agent, ritmo, reintentos y caché
├── service.py       # orquestación reutilizable (CLI, MCP y futuro servidor remoto)
├── mcp_server.py    # servidor MCP (stdio)
└── cli.py
```

El núcleo no depende de la CLI ni del MCP, así que podría ofrecerse más adelante como
servidor remoto (transporte HTTP) cambiando solo el exportador y el transporte.

## Licencia y atribución

Código bajo licencia [MIT](LICENSE). Ver [NOTICE](NOTICE).

**Datos de caminos y lugares © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright),
bajo licencia ODbL.** Los GPX generados incluyen esta atribución en sus metadatos; mantenla si
los compartes. Elevación de BRouter: SRTM (CGIAR-CSI).
