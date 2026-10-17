# Fase 0 — Investigación: generador de rutas BTT con exportación GPX

Fecha: 17-10-2026 · Estado: **investigación previa a la implementación**

> Documento histórico: usa el nombre provisional «btt-rutas» y nombres en español. La app se llama
> ahora **mtb-routes** y su código está en inglés (ver [README](../README.es.md)).

Leyenda: ✅ comprobado en fuente oficial · ⚠️ fuente secundaria o no verificada del todo · ❓ por verificar al implementar

---

## 1. Motores de rutas, geocodificación y elevación

### 1.1 Comparativa de motores

| | **BRouter** | **OpenRouteService (ORS)** | **GraphHopper** |
|---|---|---|---|
| Licencia del software | MIT ✅ | GPL‑3.0 (servidor) | Apache‑2.0 |
| Uso como API pública | brouter.de, sin clave; sin política de uso publicada ⚠️ (servidor de demostración, sin garantías) | Clave gratuita obligatoria. Plan Standard: **2.000 rutas/día, 40/min** ✅ | Clave gratuita: **500 créditos/día**, solo uso **no comercial** ✅ |
| Perfil BTT | Sí, perfiles configurables (p. ej. `mtb`, `trekking`) con control fino de `surface`, `tracktype`, `smoothness`, pendiente | `cycling-mountain` + `steepness_difficulty` (0–3) ✅ | `mtb` existe, pero **no está en el plan gratuito** (solo car/bike/foot) ⚠️ |
| Ruta circular nativa | **No** ⚠️ → hay que generarla nosotros (ver 1.2) | **Sí**: `round_trip {length, points, seed}`; "experimental", la distancia puede desviarse mucho ✅ | Sí (`round_trip.distance`, `seed`) ✅, pero sin perfil mtb en gratis |
| Info de tramos (asfalto/pista/senda) | Sí: etiquetas OSM por segmento (`highway`, `surface`, `tracktype`) en la salida GeoJSON ❓ | Sí: `extra_info` = `surface`, `waytype`, `steepness`, `traildifficulty` ✅ | `details` (incl. `mtb_rating`) ✅ |
| Autoalojado | Muy ligero: Docker `ghcr.io/abrensch/brouter` + teselas `.rd5` de 5×5° (Cataluña = `E0_N40.rd5`, actualización semanal) ✅ | Posible (Docker), pesado: Java + importar PBF de España | Posible, pesado: Java + importar PBF |
| Elevación | SRTM 90 m (CGIAR v4.1) integrada, con filtrado de ruido ✅ | SRTM integrada (`elevation=true`) | Integrada |

**Recomendación**

- **Motor principal: BRouter**, por ser MIT, no requerir clave, tener los perfiles BTT más afinables y poder correr **en local y sin límites** (Docker + una tesela de unos cientos de MB ❓). Para pruebas de bajo volumen puede usarse `brouter.de` con moderación (User‑Agent identificativo, sin ráfagas).
- **Motor secundario: ORS** (adaptador opcional, el usuario pone su `ORS_API_KEY`), útil porque tiene ruta circular nativa y `extra_info`.
- **GraphHopper: descartado** para la API pública (sin perfil mtb gratuito y solo no comercial); el motor quedará detrás de una interfaz, así que se podría añadir autoalojado más adelante.

### 1.2 Cómo generar la ruta circular (clave del proyecto)

El modelo de IA **nunca** da coordenadas. Algoritmo propio, independiente del motor:

1. Geocodificar el inicio → (lat, lon).
2. Colocar 3–5 puntos de paso en un polígono alrededor del inicio, con radio inicial ≈ `distancia / (2π · factor_sinuosidad)` y un ángulo de rumbo aleatorio (semilla).
3. Pedir al motor la ruta inicio → P1 → … → inicio con el perfil BTT.
4. Ajustar el radio (bisección) hasta quedar a ±10 % de la distancia objetivo.
5. Generar N candidatas con semillas distintas y puntuarlas: distancia, desnivel vs. máximo pedido, % de pista/senda, % de asfalto con tráfico, tramos repetidos (ida y vuelta por el mismo camino), pendiente máxima.
6. Devolver la mejor y, opcionalmente, alternativas.

Coste: ~5–20 peticiones al motor por ruta → en local es irrelevante; con ORS cabe holgado en 2.000/día.

### 1.3 Geocodificación (nombre del lugar → coordenadas)

**Nominatim (OSM)** ✅ — gratuito, sin clave, con política estricta ([política](https://operations.osmfoundation.org/policies/nominatim/)):
- Máximo **1 petición/segundo**, un solo hilo.
- **User‑Agent propio** identificando la app (no el de la librería HTTP); conviene incluir un contacto configurable por variable de entorno.
- **Caché obligatoria** de resultados (guardaremos una caché local en disco).
- **Atribución** visible a OpenStreetMap (ODbL).
- Prohibido: autocompletado, consultas sistemáticas, revender resultados.
- La política exige que, si una IA sugiere el servicio, **enlace la política y explique sus restricciones** → lo haremos en el README y en la descripción de la herramienta MCP.
- Para uso intensivo o servidor remoto: instancia propia o proveedor comercial.

Además, `generar_ruta` aceptará coordenadas directas (`41.43,2.01`) para no depender del geocodificador.

### 1.4 Elevación

- **Primaria:** la del propio motor (BRouter/ORS usan SRTM ~90 m). Suficiente para desnivel y pendientes aproximadas.
- **Opcional:** re‑muestreo con **Open‑Meteo Elevation API** (Copernicus GLO‑90, gratis para uso no comercial, 100 puntos/petición, atribución a Copernicus y Open‑Meteo) ✅. Ojo: es un modelo de **superficie** (incluye árboles/edificios) y su mantenimiento por ESA está anunciado hasta 2026 ⚠️.
- **Futuro, para Cataluña:** MDT de alta resolución del ICGC ❓ (mejoraría mucho la pendiente máxima).
- Las pendientes se calcularán sobre ventanas de ~50–100 m con suavizado, porque punto a punto un MDT de 90 m da picos falsos.
- **Aviso fijo en cada resumen:** el desnivel de un modelo de elevación puede diferir del de un reloj o ciclocomputador con barómetro (a menudo ±10–20 %), y la ruta debe revisarse antes de salir.

### 1.5 Avisos

| Aviso | Fuente |
|---|---|
| Tráfico | Etiquetas OSM del trazado: `highway=primary/secondary/tertiary/trunk` (y `maxspeed` si existe) |
| Pendiente > 12 % | Perfil de elevación suavizado; se listan tramos con km de inicio y longitud |
| Zonas protegidas | **Overpass API** (`boundary=protected_area`, `leisure=nature_reserve`) sobre el bbox de la ruta; pauta de uso ≈ 10.000 peticiones/día y 1 GB/día por IP ✅; con caché |

**Relevante para El Papiol:** la ruta puede entrar en el **Parc Natural de la Serra de Collserola**, donde la ordenanza solo permite la bici en vías del mapa ciclista (pistas de **más de 3 m**), máximo 20 km/h, y prohíbe senderos estrechos ⚠️ (hay un borrador de 2023 que endurece las sanciones). Propuesta: aviso específico + penalizar `highway=path` dentro de zonas protegidas.

---

## 2. Envío de rutas a plataformas

| Plataforma | API oficial para subir rutas | ¿Accesible para un particular? | Viable ahora |
|---|---|---|---|
| **Garmin** | Courses API (Garmin Connect Developer Program) ✅ | **No**: solo empresas aprobadas (persona jurídica) ✅; además, **nuevas solicitudes en pausa** desde primavera de 2026, sin fecha de reapertura ⚠️ | **Sí, por vía no oficial**: el servidor MCP de Garmin existente (`upload_course`), que usa la cuenta del usuario. También: copiar el GPX por USB a `Garmin/NewFiles` en muchos Edge y relojes ❓ |
| **Wahoo** | Cloud API con `POST /v1/routes` y scope `routes_write` ⚠️ | Probable: se solicita una app en el portal, con revisión manual; Sandbox y Production son apps distintas ✅. No dice si exige empresa ❓ | **Posible a futuro** si aprueban una app Sandbox para uso personal. Posible necesidad de convertir GPX → FIT ❓ |
| **Komoot** | API v007 con scope `tour-upload` ✅ | **No**: solo socios con contrato firmado; usarla sin él está prohibido ✅ | No. Importación manual del GPX en la web |
| **Strava** | **No existe endpoint para crear rutas**; solo leer/exportar rutas. Las subidas GPX crean *actividades* ✅ | El API sí admite apps personales ("Single Player Mode", 200 peticiones/15 min) ✅, pero no sirve para rutas | No. Importación manual en la web (posiblemente solo suscriptores ⚠️) |

Candidatos para investigar después: Ride with GPS, Hammerhead, COROS, Suunto ❓.

**Integración con el MCP de Garmin — dos opciones:**
- **(a) Recomendada:** nuestro servidor no habla con Garmin. Devuelve la ruta del GPX y Claude encadena la llamada a `upload_course` del otro MCP. Sin acoplamiento ni credenciales en nuestra app.
- **(b)** El adaptador `garmin` actúa como **cliente MCP** y lanza el servidor de Garmin por stdio (comando configurable). Útil para la CLI sin IA. Más frágil.

Riesgo: el MCP de Garmin depende de la API web no oficial de Garmin Connect y puede romperse o chocar con sus términos. Lo dejaremos claro en el README.

---

## 3. Servidor MCP local y empaquetado

- **SDK:** oficial `mcp` (Python, con FastMCP) o `@modelcontextprotocol/sdk` (TypeScript). Transporte **stdio** en local; el mismo código puede exponerse por **Streamable HTTP** como servidor remoto más adelante.
- **Claude Code:** `claude mcp add btt-rutas -- uv run btt-rutas-mcp` (o equivalente).
- **Claude Desktop:** extensión **MCPB** (`.mcpb`, antes `.dxt`) ✅:
  - `npm i -g @anthropic-ai/mcpb` → `mcpb init` → `mcpb pack` → doble clic para instalar.
  - `manifest.json` con `user_config`: tipos `string`, `number`, `boolean`, **`directory`** (selector de carpeta, perfecto para la carpeta de GPX) y `file`; `sensitive: true` para claves (se guardan de forma segura).
  - Tipos de servidor: `node` (Node viene con Claude Desktop, cero dependencias), `python` (hay que incluir las dependencias; las compiladas no son portables) o **`uv`** (manifest 0.4+, Claude gestiona Python y las dependencias) ✅. Spec en 0.3 con ejemplos 0.4 ⚠️.
  - Sin sandbox: el servidor corre con los permisos del usuario → por eso limitaremos la escritura a la carpeta de GPX configurada.

### Estructura propuesta (Python)

```
btt-rutas/
├── pyproject.toml            # entry points: btt-rutas (CLI), btt-rutas-mcp
├── README.md                 # instalación, ejemplos, atribución OSM, avisos
├── LICENSE  NOTICE           # licencia del código + atribuciones (OSM/ODbL, SRTM, Copernicus)
├── .env.example              # variables de entorno, sin valores reales
├── src/btt_rutas/
│   ├── config.py             # lee variables de entorno (BTT_GPX_DIR, BTT_MOTOR, BROUTER_URL, ORS_API_KEY, BTT_CONTACTO…)
│   ├── nucleo/               # sin red ni plataformas: lógica pura y testeable
│   │   ├── modelos.py        # Punto, Ruta, Resumen, Aviso, Peticion
│   │   ├── circular.py       # generador de bucles (sección 1.2)
│   │   ├── analisis.py       # distancia, desnivel, pendiente máx., % superficies, avisos
│   │   └── gpx.py            # escritura GPX 1.1 con <ele> y metadatos de atribución
│   ├── motores/              # interfaz MotorRutas.ruta(puntos, perfil) -> Trazado
│   │   ├── base.py  brouter.py  ors.py
│   ├── geo/
│   │   ├── nominatim.py      # caché en disco + 1 req/s + User-Agent
│   │   └── zonas_protegidas.py  # Overpass + caché
│   ├── exportadores/         # interfaz exportar(ruta, config) -> ResultadoExportacion
│   │   ├── base.py           # protocolo + registro de exportadores
│   │   ├── disco.py          # por defecto
│   │   ├── garmin_mcp.py     # opción (b); la (a) no necesita código
│   │   └── wahoo.py          # esqueleto que lanza NotImplementedError, con notas
│   ├── servicio.py           # orquesta: geocodificar → generar → analizar → exportar
│   ├── mcp_server.py         # herramientas: generar_ruta, listar_rutas, exportar_ruta
│   └── cli.py
├── tests/
│   ├── fixtures/             # respuestas grabadas de BRouter/ORS/Nominatim/Overpass
│   └── test_*.py             # motor simulado, sin red
├── mcpb/manifest.json
└── docs/fase-0-investigacion.md
```

El servidor remoto futuro reutilizaría `servicio.py` sin cambios; solo cambia el exportador (devolver el GPX en vez de escribirlo en disco) y el transporte.

---

## 4. Decisiones y costes que dependen de ti

1. **Motor de rutas:** BRouter en local con Docker (recomendado; requiere Docker Desktop y descargar la tesela `E0_N40.rd5`), BRouter público para empezar, u ORS con tu clave gratuita. Puedo implementar BRouter + ORS desde el inicio.
2. **Lenguaje:** **Python** (recomendado: librerías geo y tests cómodos; MCPB tipo `uv`) o **TypeScript** (MCPB más sencillo porque Node viene con Claude Desktop).
3. **Contacto para el User‑Agent** de Nominatim/Overpass: un email o URL tuyo que irá en una variable de entorno, no en el código.
4. **Carpeta de GPX por defecto:** p. ej. `~/Documents/RutasBTT` (configurable).
5. **Garmin:** ¿usamos el MCP no oficial existente (riesgo de términos de uso) con la opción (a), o también la (b) para la CLI?
6. **Wahoo:** solo tú puedes solicitar una app Sandbox en su portal de desarrolladores, si te interesa.
7. **Licencia del proyecto:** MIT o Apache‑2.0 (recomiendo Apache‑2.0 por su cláusula de patentes; MIT si prefieres simplicidad).
8. **Peticiones a internet en la implementación:** las pruebas reales (El Papiol, 15/25/40 km) harán peticiones a Nominatim, al motor y a Overpass. Te pediré permiso antes de la primera.
9. **MCPB:** ¿lo empaquetamos en la primera versión o después de validar el núcleo y la CLI?
10. **Ubicación del proyecto:** ahora está en una carpeta temporal de esta sesión; conviene moverlo a una carpeta tuya.

**Costes económicos:** 0 € con todo lo anterior (planes gratuitos y autoalojado en tu ordenador). Solo habría coste si más adelante se ofrece como servidor remoto (alojamiento, y geocodificador propio o comercial).

---

## Fuentes

- BRouter: [repositorio (MIT, Docker, rd5)](https://github.com/abrensch/brouter) · [algoritmo de elevación](https://brouter.de/brouter/elevation.html)
- OpenRouteService: [planes](https://openrouteservice.org/plans/) · [opciones de ruta](https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/routing-options) · [foro: round trip](https://ask.openrouteservice.org/t/directions-api-accurate-target-distance-response/7475)
- GraphHopper: [precios](https://www.graphhopper.com/pricing/) · [referencia de rutas](https://docs.graphhopper.com/openapi/routing/postroute)
- [Política de uso de Nominatim](https://operations.osmfoundation.org/policies/nominatim/) · [Manual de Overpass](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html)
- [Open‑Meteo Elevation API](https://open-meteo.com/en/docs/elevation-api) · [Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)
- Garmin: [Courses API](https://developer.garmin.com/gc-developer-program/courses-api/) · [Terra: pausa del programa](https://tryterra.co/blog/garmin-connect-developer-program-pause)
- Wahoo: [Cloud API](https://developers.wahooligan.com/cloud) · [spec OpenAPI (apis.io)](https://apis.io/apis/wahoo/wahoo-routes-api/)
- Komoot: [documentación API v007](https://static.komoot.de/doc/external-api/v007/index.html)
- Strava: [referencia API](https://developers.strava.com/docs/reference/) · [límites](https://developers.strava.com/docs/rate-limits/)
- MCPB: [repositorio](https://github.com/modelcontextprotocol/mcpb) · [MANIFEST.md](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md) · [docs de Claude](https://claude.com/docs/connectors/building/mcpb)
- Collserola: [BOP Barcelona (ordenanza)](https://bop.diba.cat/anuncis/antic/022019009168) · [Trailforks](https://trailforks.com/region/collserola) · [NacióDigital](https://naciodigital.cat/esports/collserola-i-les-bicicletes-una-relacio-incompatible.html)
