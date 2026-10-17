# mtb-routes

[English](README.md) · **Español**

**[⬇️ Descargar la extensión para Claude Desktop (mtb-routes.mcpb)](https://github.com/Marc-Armillas/mtb-routes/releases/latest/download/mtb-routes.mcpb)**

Genera rutas de **bicicleta de montaña** a partir de un lugar y las guarda como **GPX con
elevación**. El trazado lo calcula un motor de rutas (BRouter u OpenRouteService) sobre
**caminos reales de OpenStreetMap**: ni la IA ni la aplicación inventan coordenadas.

Se puede usar:

- **Con Claude** (Claude Desktop o Claude Code) mediante un servidor MCP local: «hazme una
  ruta circular de BTT de ~25 km desde El Papiol, poco desnivel, por pistas».
- **Desde la terminal**, sin IA: `mtb-routes generate "El Papiol" --km 25 --type tracks`.

Cada ruta devuelve un resumen (distancia, desnivel, pendiente máxima, % de asfalto, pista y
senda) y **avisos**: tramos con tráfico, pendientes superiores al 12 %, zonas protegidas,
caminos donde la bici no está permitida y tramos técnicos. El código y los mensajes de la
aplicación están en inglés; Claude te los presenta en tu idioma.

> 💾 **Los GPX se guardan por defecto en `/tmp/mtb-routes`.** macOS vacía `/tmp` al reiniciar y
> borra los archivos antiguos, así que copia las rutas que quieras conservar (o cambia
> `MTB_GPX_DIR` a otra carpeta).

> ⚠️ **Revisa siempre la ruta en un mapa antes de salir.** Los datos de OpenStreetMap pueden
> estar incompletos o desactualizados, y no reflejan cierres temporales ni toda la normativa
> local. El desnivel se calcula con un modelo digital de elevación (~90 m) y **puede diferir
> del que mida un reloj o ciclocomputador con barómetro** (a menudo un 10-20 %); las rampas
> cortas pueden quedar suavizadas.

## Instalación fácil en Claude Desktop (extensión `.mcpb`)

1. [Descarga `mtb-routes.mcpb`](https://github.com/Marc-Armillas/mtb-routes/releases/latest/download/mtb-routes.mcpb) (siempre la última versión), o genéralo con
   `npx @anthropic-ai/mcpb pack . dist/mtb-routes.mcpb`.
2. Haz doble clic en el archivo (o arrástralo a Claude Desktop → Ajustes → Extensiones) y pulsa
   **Instalar**.
3. Rellena la configuración: carpeta de los GPX (por defecto `/tmp/mtb-routes`) y un email de contacto
   (lo exige la política de uso de OpenStreetMap/Nominatim). El resto de campos son opcionales.
4. Pídele a Claude: «hazme una ruta circular de BTT de 25 km desde El Papiol por pistas».

No hace falta instalar Python: la extensión es de tipo `uv` y Claude Desktop descarga Python y
las dependencias automáticamente la primera vez (puede tardar un minuto). El formato `.mcpb` es
el sucesor de `.dxt`; las versiones antiguas de Claude Desktop que solo admitan `.dxt` no
soportan extensiones de tipo `uv`.

## Instalación manual (CLI y Claude Code)

Requisitos: macOS, Windows o Linux con [uv](https://docs.astral.sh/uv/) (instala Python por ti).

```bash
git clone <url-del-repositorio> mtb-routes
cd mtb-routes
uv sync
cp .env.example .env   # y edítalo
```

### Configuración (variables de entorno)

No hay claves ni datos personales en el código: todo se configura con variables de entorno
(o un archivo `.env` en la carpeta desde la que ejecutas la CLI).

| Variable | Por defecto | Para qué |
|---|---|---|
| `MTB_GPX_DIR` | `/tmp/mtb-routes` | Carpeta donde se guardan los GPX. La app solo escribe aquí (y en su subcarpeta `.mtb-routes/` con caché e índice). En Windows, por defecto es la carpeta temporal del sistema. |
| `MTB_CONTACT` | — | Email o URL que se envía en el User-Agent. **Recomendado**: lo exige la política de Nominatim. |
| `MTB_ENGINE` | `brouter` | `brouter` u `ors`. |
| `MTB_BROUTER_URL` | `https://brouter.de` | Servidor BRouter (público o local, ver abajo). |
| `ORS_API_KEY` | — | Clave gratuita de [OpenRouteService](https://openrouteservice.org) si `MTB_ENGINE=ors`. |
| `MTB_PROTECTED_AREAS` | `1` | Comprobar zonas protegidas con Overpass API. |
| `MTB_GARMIN_MCP_COMMAND` | — | Solo para `--garmin` en la CLI (ver «Garmin»). |
| `MTB_DATA_DIR` | `<carpeta GPX>/.mtb-routes` | Dónde guardar caché e índice. |

## Uso desde la terminal

```bash
uv run mtb-routes generate "El Papiol" --km 25 --type tracks --max-climb 500
uv run mtb-routes generate "41.4386,2.0108" --km 15            # también con coordenadas
uv run mtb-routes generate "El Papiol" --km 20 --end "Sant Cugat del Vallès"   # ruta lineal
uv run mtb-routes generate "El Papiol" --km 30 --via "Castellbisbal" --via "Molins de Rei"  # circular por puntos de paso
uv run mtb-routes generate "El Papiol" --km 40 --seed 7        # otra alternativa reproducible
uv run mtb-routes generate "El Papiol" --km 25 --json          # salida JSON
uv run mtb-routes list
```

Tipos de camino (`--type`):

- `tracks`: prioriza pistas anchas, poca senda y sin rampas extremas.
- `mixed` (por defecto): BTT general.
- `singletrack`: más senda y menos asfalto.

Ejemplo real (resumido; la salida de la aplicación está en inglés):

```text
MTB El Papiol 26 km loop
  Distance: 25.9 km · Climbing: +442 m / -443 m · Elevation 20–266 m
  Max grade: 17.0 % uphill, 18.0 % downhill
  Surface: paved 18.7 % · track 67.3 % · singletrack 14.1 %
  GPX: /tmp/mtb-routes/mtb-el-papiol-26-km-loop-20261017-121732.gpx
  Warnings:
   - [traffic] 1.2 km on roads with motor traffic in 6 section(s); ride carefully.
   - [grade] 8 sections (about 2.2 km) are steeper than 12 %; listing the 6 steepest.
   - [protected_area] The route crosses the protected area «Parc Agrari del Baix Llobregat»…
```

Más ejemplos con salidas reales en [docs/pruebas-reales.md](docs/pruebas-reales.md).

## Uso con Claude (servidor MCP)

El servidor expone dos herramientas:

- `generate_route(start, distance_km, max_climb_m?, trail_type?, loop=true, end?, name?, seed?, via?)`
  → ruta del GPX, resumen y avisos. `via` es una lista de lugares por los que la ruta debe
  pasar, en orden (p. ej. "circular desde El Papiol pasando por Castellbisbal y Molins de Rei").
- `list_routes()` → rutas guardadas.

### Claude Code

```bash
claude mcp add mtb-routes \
  -e MTB_GPX_DIR=/tmp/mtb-routes -e MTB_CONTACT=tu-email@ejemplo.com \
  -- uv run --directory /ruta/a/mtb-routes mtb-routes-mcp
```

### Claude Desktop (sin extensión)

Lo más sencillo es la extensión `.mcpb` (ver arriba). Si prefieres configurarlo a mano:
Ajustes → Desarrollador → Editar configuración (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mtb-routes": {
      "command": "/ruta/absoluta/a/uv",
      "args": ["run", "--directory", "/ruta/a/mtb-routes", "mtb-routes-mcp"],
      "env": {
        "MTB_GPX_DIR": "/tmp/mtb-routes",
        "MTB_CONTACT": "tu-email@ejemplo.com"
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
npx @anthropic-ai/mcpb pack . dist/mtb-routes.mcpb
python scripts/make_icon.py    # solo si quieres regenerar icon.png
```

### Publicar una versión

1. Sube `version` a la vez en `manifest.json`, `pyproject.toml` y `src/mtb_routes/__init__.py`.
2. Crea y sube una etiqueta con esa versión:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. El flujo `Release` de GitHub Actions ejecuta los tests, genera `mtb-routes.mcpb` y lo adjunta
   a una nueva Release de GitHub. El enlace de descarga del principio de este README apunta
   siempre a la última.

## Garmin, Wahoo y otras plataformas

La aplicación es independiente de cualquier plataforma: el resultado es un GPX estándar. Los
envíos a plataformas son **exportadores** opcionales con una interfaz común
(`export(route, config) -> ExportResult`, en `src/mtb_routes/exporters/`).

- **disk** (por defecto): guarda el GPX en `MTB_GPX_DIR`.
- **garmin**: delega en un servidor MCP de Garmin ya instalado (herramienta `upload_course`).
  - *Con Claude (recomendado)*: no hay que configurar nada. Pide «súbela a Garmin» y Claude
    llamará a `upload_course` del MCP de Garmin con el GPX generado y
    `activity_type="mountain_biking"`.
  - *Desde la CLI*: define `MTB_GARMIN_MCP_COMMAND` con el comando que arranca ese servidor y
    usa `--garmin`. Las credenciales de Garmin las gestiona ese servidor, nunca esta app.
  - Los MCP de Garmin comunitarios usan la API web no oficial de Garmin Connect y pueden dejar
    de funcionar. La API oficial (Courses API) es solo para empresas aprobadas.
- **wahoo**: no implementado. La Cloud API tiene `POST /v1/routes`, pero requiere solicitar y
  obtener la aprobación de una app (notas en `exporters/wahoo.py`).
- **Komoot** (API solo para socios con contrato) y **Strava** (su API no permite crear rutas):
  importa el GPX manualmente en su web.

## Motores de rutas

- **BRouter** (por defecto, MIT, sin clave). Usa el perfil `mtb` con
  `StrictNOBicycleaccess=1` (evita caminos con `bicycle=no`) y `avoid_unsafe=1`. El servidor
  público `brouter.de` no garantiza disponibilidad: la app hace como máximo 1 petición por
  segundo y cachea las respuestas. Para uso intensivo, levanta uno local (no probado aún en
  este proyecto):

  ```bash
  mkdir -p segments4
  curl -o segments4/E0_N40.rd5 https://brouter.de/brouter/segments4/E0_N40.rd5   # Cataluña
  docker run -d -p 17777:17777 -v "$PWD/segments4:/segments4" ghcr.io/abrensch/brouter
  # y en .env: MTB_BROUTER_URL=http://localhost:17777
  ```

- **OpenRouteService** (opcional): `MTB_ENGINE=ors` y `ORS_API_KEY` (plan gratuito: 2.000
  rutas/día, 40/min).

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
src/mtb_routes/
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
