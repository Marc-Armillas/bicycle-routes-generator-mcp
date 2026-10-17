# Pruebas reales desde Madrid

Fecha: 17-10-2026 · Motor: BRouter público (perfiles `mtb` y `fastbike`) · Semilla: 2026 ·
6 candidatas por ruta circular. Para repetirlas:

```bash
uv run bicycle-routes generate "Casa de Campo, Madrid" --km 15 --type mixed --seed 2026
uv run bicycle-routes generate "Casa de Campo, Madrid" --km 25 --type tracks --max-climb 500 --seed 2026
uv run bicycle-routes generate "Casa de Campo, Madrid" --km 40 --type mixed --seed 2026
uv run bicycle-routes generate "Madrid" --km 60 --type road --seed 2026
uv run bicycle-routes generate "Casa de Campo, Madrid" --km 30 --via "El Pardo, Madrid" --via "Aravaca, Madrid" --seed 2026
```

Los datos de OSM cambian cada semana, así que con la misma semilla la ruta puede variar ligeramente.
La salida de la aplicación está en inglés; `<carpeta GPX>` es la carpeta configurada en `BIKE_GPX_DIR`.

## BTT 15 km (`mixed`)

```text
MTB Casa de Campo 15 km loop
  Start: Casa de Campo, Madrid, Comunidad de Madrid, España
  Distance: 14.9 km · Climbing: +149 m / -151 m · Elevation 615–696 m
  Max grade: 10.3 % uphill, 8.0 % downhill
  Surface: paved 32.8 % · track 19.1 % · singletrack 48.1 %
  Engine: brouter (mtb) · candidates evaluated: 6
  GPX: <carpeta GPX>/mtb-casa-de-campo-15-km-loop-20261017-163740.gpx
  Warnings:
   - [general] Climbing and grades come from a digital elevation model (~90 m resolution) and may differ from what a barometric watch or bike computer records (often by 10-20 %); short ramps may be smoothed out.
   - [general] Route generated automatically from OpenStreetMap: check it on a map before riding (trail condition, access, temporary closures and local regulations).
  Trail data © OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright
```

## BTT 25 km (`tracks`, máx. 500 m)

```text
MTB Casa de Campo 26 km loop
  Start: Casa de Campo, Madrid, Comunidad de Madrid, España
  Distance: 25.9 km · Climbing: +214 m / -216 m · Elevation 615–722 m
  Max grade: 10.3 % uphill, 8.0 % downhill
  Surface: paved 31.2 % · track 20.8 % · singletrack 48.0 %
  Engine: brouter (mtb) · candidates evaluated: 6
  GPX: <carpeta GPX>/mtb-casa-de-campo-26-km-loop-20261017-162318.gpx
  Warnings:
   - [general] Climbing and grades come from a digital elevation model (~90 m resolution) and may differ from what a barometric watch or bike computer records (often by 10-20 %); short ramps may be smoothed out.
   - [general] Route generated automatically from OpenStreetMap: check it on a map before riding (trail condition, access, temporary closures and local regulations).
  Trail data © OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright
```

## BTT 40 km (`mixed`)

```text
MTB Casa de Campo 38 km loop
  Start: Casa de Campo, Madrid, Comunidad de Madrid, España
  Distance: 37.8 km · Climbing: +336 m / -338 m · Elevation 615–725 m
  Max grade: 10.3 % uphill, 13.3 % downhill
  Surface: paved 28.8 % · track 40.6 % · singletrack 30.6 %
  Engine: brouter (mtb) · candidates evaluated: 6
  GPX: <carpeta GPX>/mtb-casa-de-campo-38-km-loop-20261017-162524.gpx
  Warnings:
   - [traffic] 0.3 km on roads with motor traffic in 1 section(s); ride carefully.
   - [traffic] Road with traffic (km 27.3–27.6).
   - [grade] Steep descent over 12 % (max ~13 %, km 9.2–9.3).
   - [general] Climbing and grades come from a digital elevation model (~90 m resolution) and may differ from what a barometric watch or bike computer records (often by 10-20 %); short ramps may be smoothed out.
   - [general] Route generated automatically from OpenStreetMap: check it on a map before riding (trail condition, access, temporary closures and local regulations).
  Trail data © OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright
```

## Carretera 60 km (`road`)

```text
Road Madrid 60 km loop
  Start: Madrid, Comunidad de Madrid, España
  Distance: 59.6 km · Climbing: +584 m / -584 m · Elevation 602–730 m
  Max grade: 10.7 % uphill, 14.0 % downhill
  Surface: paved 99.7 % · track 0.0 % · singletrack 0.3 %
  Engine: brouter (fastbike) · candidates evaluated: 6
  GPX: <carpeta GPX>/road-madrid-60-km-loop-20261017-162841.gpx
  Warnings:
   - [traffic] 4.0 km on busy roads (main roads or heavy estimated traffic) in 9 section(s); ride carefully.
   - [traffic] Busy road (km 15.6–15.7).
   - [traffic] Busy road (km 20.4–20.8).
   - [traffic] Busy road (km 33.3–33.5).
   - [traffic] Busy road (km 45.4–47.3).
   - [traffic] Busy road (km 49.2–49.2).
   - [traffic] Busy road (km 51.8–52.0).
   - [traffic] Busy road (km 56.3–56.5).
   - [traffic] Busy road (km 57.3–57.7).
   - [grade] Steep descent over 12 % (max ~14 %, km 30.5–30.6).
   - [access] According to OpenStreetMap bikes are not allowed or you must dismount (km 0.1–0.2, 103 m); look for an alternative or push the bike.
   - [access] According to OpenStreetMap bikes are not allowed or you must dismount (km 59.5–59.6, 35 m); look for an alternative or push the bike.
   - [general] Climbing and grades come from a digital elevation model (~90 m resolution) and may differ from what a barometric watch or bike computer records (often by 10-20 %); short ramps may be smoothed out.
   - [general] Route generated automatically from OpenStreetMap: check it on a map before riding (trail condition, access, temporary closures and local regulations).
  Trail data © OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright
```

## BTT 30 km con puntos de paso (`--via`)

```text
MTB Casa de Campo 35 km loop
  Start: Casa de Campo, Madrid, Comunidad de Madrid, España
  Via: El Pardo, Fuencarral-El Pardo, Madrid, Comunidad de Madrid, 28048, España
  Via: Moncloa-Aravaca, Madrid, Comunidad de Madrid, España
  Distance: 34.8 km · Climbing: +231 m / -233 m · Elevation 586–665 m
  Max grade: 10.8 % uphill, 15.5 % downhill
  Surface: paved 44.6 % · track 9.9 % · singletrack 45.5 %
  Engine: brouter (mtb) · candidates evaluated: 1
  GPX: <carpeta GPX>/mtb-casa-de-campo-35-km-loop-20261017-163555.gpx
  Warnings:
   - [distance] The route is 34.8 km instead of the requested 30 km: it must pass through the requested via points.
   - [grade] Steep descent over 12 % (max ~16 %, km 2.2–2.5).
   - [general] Climbing and grades come from a digital elevation model (~90 m resolution) and may differ from what a barometric watch or bike computer records (often by 10-20 %); short ramps may be smoothed out.
   - [general] Route generated automatically from OpenStreetMap: check it on a map before riding (trail condition, access, temporary closures and local regulations).
  Trail data © OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright
```

## Observaciones

- **BTT 15 y 25 km**: rutas suaves (+149 m y +214 m), sin tráfico. El 48 % de «senda» no son
  senderos técnicos: casi todo son caminos peatonales del parque con la bici permitida
  (`highway=footway` + `bicycle=yes`, y `highway=path` de tierra), que la app cuenta como senda
  porque OpenStreetMap no los marca como pista.
- **`tracks` frente a `mixed`**: en la Casa de Campo, que es bastante llana, el tipo `tracks`
  apenas cambia el resultado: la ruta de 25 km sale casi igual que con `mixed`.
- **BTT 40 km**: 37,8 km (un 5,5 % menos de lo pedido), +336 m y un 41 % de pista. Solo
  0,3 km con tráfico y una bajada de ~13 %.
- **Carretera 60 km**: 99,7 % asfalto. «Madrid» se geocodifica en el centro de la ciudad, así
  que la salida y la llegada pasan por calles donde OpenStreetMap no permite la bici (los dos
  avisos de `access`, de 103 y 35 m). Para rutas de carretera conviene salir de un punto de las
  afueras o dar coordenadas.
- **Puntos de paso**: «Aravaca, Madrid» se ha geocodificado como el distrito
  «Moncloa-Aravaca» en lugar del barrio de Aravaca. Es un buen ejemplo de por qué conviene
  revisar las líneas `Via:` de la salida y, si hace falta, dar más detalle o coordenadas. La
  ruta sale de 34,8 km en lugar de 30, y la app lo avisa.
- **Zonas protegidas**: no se detectó ninguna en estas rutas. Overpass devolvió errores 502
  temporales en varias ejecuciones; cuando pasa, la app no falla, sino que lo indica con un
  aviso. Las salidas de arriba son de ejecuciones en las que Overpass respondió.

## Historial de ajustes

Los perfiles y la puntuación se ajustaron en las pruebas iniciales, cerca de Barcelona:

- En una primera versión, la puntuación eligió para el tipo `tracks` una candidata con un 32 %
  de senda y una rampa del 34 %. Se reforzó la penalización de senda y de rampas fuertes para
  ese tipo.
- Calibración del desnivel: el cálculo de la app daba un 7-10 % más que el desnivel filtrado de
  BRouter sobre las mismas rutas, dentro del margen esperable de un modelo de elevación de 90 m.
