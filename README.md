# mtb-routes

**English** · [Español](README.es.md)

**[⬇️ Download the Claude Desktop extension (mtb-routes.mcpb)](https://github.com/Marc-Armillas/mtb-routes/releases/latest/download/mtb-routes.mcpb)**

Generates **mountain bike** routes from a location and saves them as **GPX with elevation**.
The track is computed by a routing engine (BRouter or OpenRouteService) on **real
OpenStreetMap trails**: neither the AI nor the application invents coordinates.

You can use it:

- **With Claude** (Claude Desktop or Claude Code) through a local MCP server: "make me a
  ~25 km MTB loop from El Papiol, little climbing, on dirt tracks".
- **From the terminal**, without AI: `mtb-routes generate "El Papiol" --km 25 --type tracks`.

Every route comes with a summary (distance, climbing, maximum grade, % of pavement, dirt
track and singletrack) and **warnings**: sections with motor traffic, grades over 12 %,
protected areas, ways where bikes are not allowed and technical sections.

> 💾 **GPX files go to `/tmp/mtb-routes` by default.** macOS empties `/tmp` on restart and cleans
> up old files, so copy the routes you want to keep (or set `MTB_GPX_DIR` to another folder).

> ⚠️ **Always check the route on a map before riding.** OpenStreetMap data may be incomplete
> or out of date, and does not reflect temporary closures or every local regulation. Climbing
> is computed from a digital elevation model (~90 m) and **may differ from what a barometric
> watch or bike computer records** (often by 10-20 %); short ramps may be smoothed out.

## Easy install in Claude Desktop (`.mcpb` extension)

1. [Download `mtb-routes.mcpb`](https://github.com/Marc-Armillas/mtb-routes/releases/latest/download/mtb-routes.mcpb) (always the latest release), or build it with
   `npx @anthropic-ai/mcpb pack . dist/mtb-routes.mcpb`.
2. Double-click the file (or drag it into Claude Desktop → Settings → Extensions) and click
   **Install**.
3. Fill in the configuration: the GPX folder (`/tmp/mtb-routes` by default) and a contact email
   (required by the OpenStreetMap/Nominatim usage policy). The other fields are optional.
4. Ask Claude: "make me a 25 km MTB loop from El Papiol on dirt tracks".

No need to install Python: this is a `uv` extension, so Claude Desktop downloads Python and the
dependencies automatically the first time (it can take a minute). `.mcpb` is the successor of
the `.dxt` format; older Claude Desktop versions that only support `.dxt` cannot run `uv`
extensions.

## Manual install (CLI and Claude Code)

Requirements: macOS, Windows or Linux with [uv](https://docs.astral.sh/uv/) (it installs Python for you).

```bash
git clone <repository-url> mtb-routes
cd mtb-routes
uv sync
cp .env.example .env   # and edit it
```

### Configuration (environment variables)

There are no keys or personal data in the code: everything is configured through environment
variables (or a `.env` file in the folder you run the CLI from).

| Variable | Default | Purpose |
|---|---|---|
| `MTB_GPX_DIR` | `/tmp/mtb-routes` | Folder where GPX files are saved. The app only writes here (and to its `.mtb-routes/` subfolder with cache and index). On Windows the default is the system temp folder. |
| `MTB_CONTACT` | — | Email or URL sent in the User-Agent. **Recommended**: required by Nominatim's policy. |
| `MTB_ENGINE` | `brouter` | `brouter` or `ors`. |
| `MTB_BROUTER_URL` | `https://brouter.de` | BRouter server (public or local, see below). |
| `ORS_API_KEY` | — | Free [OpenRouteService](https://openrouteservice.org) key if `MTB_ENGINE=ors`. |
| `MTB_PROTECTED_AREAS` | `1` | Check protected areas with the Overpass API. |
| `MTB_GARMIN_MCP_COMMAND` | — | Only for `--garmin` in the CLI (see "Garmin"). |
| `MTB_DATA_DIR` | `<GPX folder>/.mtb-routes` | Where to keep the cache and index. |

## Command-line usage

```bash
uv run mtb-routes generate "El Papiol" --km 25 --type tracks --max-climb 500
uv run mtb-routes generate "41.4386,2.0108" --km 15            # coordinates work too
uv run mtb-routes generate "El Papiol" --km 20 --end "Sant Cugat del Vallès"   # point-to-point
uv run mtb-routes generate "El Papiol" --km 30 --via "Castellbisbal" --via "Molins de Rei"  # loop through via points
uv run mtb-routes generate "El Papiol" --km 40 --seed 7        # another reproducible alternative
uv run mtb-routes generate "El Papiol" --km 25 --json          # JSON output
uv run mtb-routes list
```

Trail types (`--type`):

- `tracks`: favours wide dirt tracks, little singletrack and no extreme ramps.
- `mixed` (default): general MTB.
- `singletrack`: more singletrack, less pavement.

Real example (abridged):

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

More examples with real output in [docs/pruebas-reales.md](docs/pruebas-reales.md) (in Spanish).

## Using it with Claude (MCP server)

The server exposes two tools:

- `generate_route(start, distance_km, max_climb_m?, trail_type?, loop=true, end?, name?, seed?, via?)`
  → GPX path, summary and warnings. `via` is a list of places the route must pass through, in
  order (e.g. "a loop from El Papiol passing through Castellbisbal and Molins de Rei").
- `list_routes()` → saved routes.

### Claude Code

```bash
claude mcp add mtb-routes \
  -e MTB_GPX_DIR=/tmp/mtb-routes -e MTB_CONTACT=you@example.com \
  -- uv run --directory /path/to/mtb-routes mtb-routes-mcp
```

### Claude Desktop (without the extension)

The `.mcpb` extension is the easiest option (see above). To configure it by hand instead:
Settings → Developer → Edit config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mtb-routes": {
      "command": "/absolute/path/to/uv",
      "args": ["run", "--directory", "/path/to/mtb-routes", "mtb-routes-mcp"],
      "env": {
        "MTB_GPX_DIR": "/tmp/mtb-routes",
        "MTB_CONTACT": "you@example.com"
      }
    }
  }
}
```

Use the absolute path to `uv` (`which uv` on macOS/Linux, `where uv` on Windows), because
Claude Desktop does not always inherit the terminal's `PATH`. Restart Claude Desktop.

### Building the extension

`manifest.json` describes the extension (`uv` type, tools and configuration fields) and
`.mcpbignore` keeps the tests, docs and your `.env` out of the package.

```bash
npx @anthropic-ai/mcpb validate manifest.json
npx @anthropic-ai/mcpb pack . dist/mtb-routes.mcpb
python scripts/make_icon.py    # only if you want to regenerate icon.png
```

### Publishing a release

1. Bump `version` in `manifest.json`, `pyproject.toml` and `src/mtb_routes/__init__.py` together.
2. Create and push a matching tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. The `Release` GitHub Actions workflow runs the tests, builds `mtb-routes.mcpb` and attaches
   it to a new GitHub Release. The download link at the top of this README always points to
   the latest one.

## Garmin, Wahoo and other platforms

The application is platform-independent: the output is a standard GPX file. Sending to
platforms is done by optional **exporters** sharing a common interface
(`export(route, config) -> ExportResult`, in `src/mtb_routes/exporters/`).

- **disk** (default): saves the GPX in `MTB_GPX_DIR`.
- **garmin**: delegates to an already installed Garmin MCP server (`upload_course` tool).
  - *With Claude (recommended)*: nothing to configure. Ask "upload it to Garmin" and Claude
    will call the Garmin MCP server's `upload_course` with the generated GPX and
    `activity_type="mountain_biking"`.
  - *From the CLI*: set `MTB_GARMIN_MCP_COMMAND` to the command that starts that server and use
    `--garmin`. Garmin credentials are handled by that server, never by this app.
  - Community Garmin MCP servers use Garmin Connect's unofficial web API and may stop working.
    The official API (Courses API) is only available to approved businesses.
- **wahoo**: not implemented. The Cloud API has `POST /v1/routes`, but you must request an app
  and get it approved (notes in `exporters/wahoo.py`).
- **Komoot** (API only for partners under contract) and **Strava** (its API cannot create
  routes): import the GPX manually on their websites.

## Routing engines

- **BRouter** (default, MIT, no key). Uses the `mtb` profile with `StrictNOBicycleaccess=1`
  (avoids ways tagged `bicycle=no`) and `avoid_unsafe=1`. The public `brouter.de` server makes
  no availability guarantees: the app sends at most 1 request per second and caches responses.
  For heavy use, run a local one (not yet tested in this project):

  ```bash
  mkdir -p segments4
  curl -o segments4/E0_N40.rd5 https://brouter.de/brouter/segments4/E0_N40.rd5   # Catalonia
  docker run -d -p 17777:17777 -v "$PWD/segments4:/segments4" ghcr.io/abrensch/brouter
  # and in .env: MTB_BROUTER_URL=http://localhost:17777
  ```

- **OpenRouteService** (optional): `MTB_ENGINE=ors` and `ORS_API_KEY` (free plan: 2,000
  routes/day, 40/min).

### How the loop is generated

1. The place is geocoded with Nominatim (or the coordinates you give are used).
2. 3-4 waypoints are placed on a circle passing through the start, with a random orientation
   (reproducible with `--seed`).
3. The engine routes start → waypoints → start on real trails.
4. The radius is adjusted until the requested distance is approached (about 2-4 requests).
5. Six candidates are generated and the best one is picked by distance, traffic, repeated
   trails, surface, forbidden access, climbing and grades.

With via points (`--via` / `via`), your points replace the random ones: the engine routes
start → via 1 → … → via N → start (or → end, for point-to-point), in the given order. The
distance comes from those points, not from `--km`; a warning is added if it differs by more
than 15 %.

## External services and their policies

- **Nominatim** (place lookup): [usage policy](https://operations.osmfoundation.org/policies/nominatim/).
  At most 1 request/second, an identifying User-Agent, cached results, no autocomplete or bulk
  queries. For heavy use, run your own Nominatim.
- **Overpass API** (protected areas): about 10,000 requests/day per IP as a guideline; one
  cached query per route.
- **brouter.de**: public server without guarantees; use a local one for heavy use.

## Development

```bash
uv run pytest              # tests with simulated engine, geocoder and areas (no network)
uv run pytest -m network   # optional test against the real services
```

Layout:

```text
src/mtb_routes/
├── core/            # models, loop generator, analysis and GPX (no network, no platforms)
├── engines/         # BRouter and OpenRouteService (RoutingEngine interface)
├── geo/             # Nominatim and protected areas (Overpass)
├── exporters/       # disk, garmin (via MCP), wahoo (pending)
├── net.py           # HTTP client: User-Agent, rate limiting, retries and cache
├── service.py       # reusable orchestration (CLI, MCP and a future remote server)
├── mcp_server.py    # MCP server (stdio)
└── cli.py
```

The core does not depend on the CLI or the MCP server, so it could later be offered as a
remote server (HTTP transport) by changing only the exporter and the transport.

## License and attribution

Code under the [MIT](LICENSE) license. See [NOTICE](NOTICE).

**Trail and place data © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors, under the ODbL license.** Generated GPX files include this attribution in their
metadata; keep it if you share them. BRouter elevation: SRTM (CGIAR-CSI).
