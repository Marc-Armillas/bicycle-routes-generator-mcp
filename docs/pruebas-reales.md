# Pruebas reales desde El Papiol

Fecha: 17-10-2026 · Motor: BRouter público (perfil `mtb`) · Semilla: 2026 · 6 candidatas por ruta.
Los GPX se guardaron en `~/Downloads`. Para repetirlas:

```bash
uv run mtb-routes generate "El Papiol" --km 15 --type mixed --seed 2026
uv run mtb-routes generate "El Papiol" --km 25 --type tracks --max-climb 500 --seed 2026
uv run mtb-routes generate "El Papiol" --km 40 --type mixed --seed 2026
```

Los datos de OSM cambian cada semana, así que con la misma semilla la ruta puede variar ligeramente.
La salida de la aplicación está en inglés.

## 15 km

```text
MTB El Papiol 16 km loop
  Start: el Papiol, Baix Llobregat, Barcelona, Catalunya, 08754, España
  Distance: 16.5 km · Climbing: +136 m / -139 m · Elevation 20–123 m
  Max grade: 17.0 % uphill, 10.5 % downhill
  Surface: paved 15.2 % · track 71.3 % · singletrack 13.5 %
  Engine: brouter (mtb) · candidates evaluated: 6
  GPX: ~/Downloads/mtb-el-papiol-16-km-loop-20261017-121732.gpx
  Warnings:
   - [traffic] 0.6 km on roads with motor traffic in 3 section(s); ride carefully.
   - [traffic] Road with traffic (km 0.0–0.2).
   - [traffic] Road with traffic (km 15.3–15.6).
   - [traffic] Road with traffic (km 16.3–16.5).
   - [grade] Steep climb over 12 % (max ~17 %, km 15.7–16.0).
   - [protected_area] The route crosses the protected area «Parc Natural de Collserola» (km 0.9–3.2). Follow its regulations. In Collserola bikes are only allowed on the park's cycling network (tracks wider than 3 m), at 20 km/h maximum. It includes about 0.7 km of singletrack inside the area: check it is allowed.
   - [protected_area] The route crosses the protected area «Parc Agrari del Baix Llobregat» (km 3.8–9.5). Follow its regulations. It includes about 0.2 km of singletrack inside the area: check it is allowed.
   - [protected_area] The route crosses the protected area «Parc Agrari del Baix Llobregat» (km 14.4–15.2). Follow its regulations.
   - [general] Climbing and grades come from a digital elevation model (~90 m resolution) and may differ from what a barometric watch or bike computer records (often by 10-20 %); short ramps may be smoothed out.
   - [general] Route generated automatically from OpenStreetMap: check it on a map before riding (trail condition, access, temporary closures and local regulations).
  Trail data © OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright
```

## 25 km

```text
MTB El Papiol 26 km loop
  Start: el Papiol, Baix Llobregat, Barcelona, Catalunya, 08754, España
  Distance: 25.9 km · Climbing: +442 m / -443 m · Elevation 20–266 m
  Max grade: 17.0 % uphill, 18.0 % downhill
  Surface: paved 18.7 % · track 67.3 % · singletrack 14.1 %
  Engine: brouter (mtb) · candidates evaluated: 6
  GPX: ~/Downloads/mtb-el-papiol-26-km-loop-20261017-121732.gpx
  Warnings:
   - [traffic] 1.2 km on roads with motor traffic in 6 section(s); ride carefully.
   - [traffic] Road with traffic (km 0.0–0.2).
   - [traffic] Road with traffic (km 0.8–1.1).
   - [traffic] Road with traffic (km 21.6–21.7).
   - [traffic] Road with traffic (km 22.5–22.6).
   - [traffic] Road with traffic (km 24.8–25.0).
   - [traffic] Road with traffic (km 25.7–25.9).
   - [grade] 8 sections (about 2.2 km) are steeper than 12 %; listing the 6 steepest.
   - [grade] Steep descent over 12 % (max ~17 %, km 0.5–0.7).
   - [grade] Steep climb over 12 % (max ~17 %, km 8.4–8.9).
   - [grade] Steep descent over 12 % (max ~15 %, km 15.5–15.7).
   - [grade] Steep descent over 12 % (max ~18 %, km 15.7–16.0).
   - [grade] Steep descent over 12 % (max ~17 %, km 16.3–16.7).
   - [grade] Steep climb over 12 % (max ~17 %, km 25.2–25.4).
   - [technical] Technical section or steps (km 16.5–16.5).
   - [protected_area] The route crosses the protected area «Parc Agrari del Baix Llobregat» (km 1.3–6.8). Follow its regulations. It includes about 0.1 km of singletrack inside the area: check it is allowed.
   - [protected_area] The route crosses the protected area «Parc Agrari del Baix Llobregat» (km 23.9–24.6). Follow its regulations.
   - [general] Climbing and grades come from a digital elevation model (~90 m resolution) and may differ from what a barometric watch or bike computer records (often by 10-20 %); short ramps may be smoothed out.
   - [general] Route generated automatically from OpenStreetMap: check it on a map before riding (trail condition, access, temporary closures and local regulations).
  Trail data © OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright
```

## 40 km

```text
MTB El Papiol 39 km loop
  Start: el Papiol, Baix Llobregat, Barcelona, Catalunya, 08754, España
  Distance: 39.5 km · Climbing: +1203 m / -1205 m · Elevation 14–312 m
  Max grade: 31.5 % uphill, 45.1 % downhill
  Surface: paved 19.7 % · track 58.3 % · singletrack 22.0 %
  Engine: brouter (mtb) · candidates evaluated: 6
  GPX: ~/Downloads/mtb-el-papiol-39-km-loop-20261017-121733.gpx
  Warnings:
   - [traffic] 0.9 km on roads with motor traffic in 6 section(s); ride carefully.
   - [traffic] Road with traffic (km 0.0–0.2).
   - [traffic] Road with traffic (km 10.9–10.9).
   - [traffic] Road with traffic (km 18.1–18.2).
   - [traffic] Road with traffic (km 26.9–27.0).
   - [traffic] Road with traffic (km 38.3–38.6).
   - [traffic] Road with traffic (km 39.3–39.5).
   - [grade] 25 sections (about 7.2 km) are steeper than 12 %; listing the 6 steepest.
   - [grade] Steep climb over 12 % (max ~22 %, km 3.7–4.0).
   - [grade] Steep climb over 12 % (max ~32 %, km 18.6–19.5).
   - [grade] Steep descent over 12 % (max ~45 %, km 20.2–20.8).
   - [grade] Steep climb over 12 % (max ~24 %, km 27.6–28.1).
   - [grade] Steep descent over 12 % (max ~42 %, km 30.9–31.3).
   - [grade] Steep descent over 12 % (max ~23 %, km 32.3–32.5).
   - [technical] Technical section or steps (km 33.1–33.1).
   - [protected_area] The route crosses the protected area «Parc Natural de Collserola» (km 0.9–9.6). Follow its regulations. In Collserola bikes are only allowed on the park's cycling network (tracks wider than 3 m), at 20 km/h maximum. It includes about 2.0 km of singletrack inside the area: check it is allowed.
   - [protected_area] The route crosses the protected area «Parc Agrari del Baix Llobregat» (km 11.0–14.0). Follow its regulations.
   - [protected_area] The route crosses the protected area «Parc Agrari del Baix Llobregat» (km 37.1–38.1). Follow its regulations.
   - [general] Climbing and grades come from a digital elevation model (~90 m resolution) and may differ from what a barometric watch or bike computer records (often by 10-20 %); short ramps may be smoothed out.
   - [general] Route generated automatically from OpenStreetMap: check it on a map before riding (trail condition, access, temporary closures and local regulations).
  Trail data © OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright
```

## Observaciones

- **15 km (`mixed`)**: ruta llana (+136 m) por el Parc Agrari del Baix Llobregat y el borde de
  Collserola; 71 % pista. Sale 1,5 km más larga de lo pedido (+10 %).
- **25 km (`tracks`, máx. 500 m)**: +442 m, 67 % pista y 14 % senda, pendiente máxima ~17-18 %.
  En una primera versión la puntuación eligió una candidata con un 32 % de senda y una rampa
  del 34 %. Se reforzó la penalización de senda y de rampas fuertes para el tipo `tracks`.
- **40 km (`mixed`)**: +1.203 m, con tramos muy empinados (bajadas del 42-45 % según el modelo
  de elevación, comprobado en el perfil: ~100 m de bajada en ~300 m). Es exigente. Para algo
  más suave, usa `--max-climb` o `--type tracks`.
- Los tramos con tráfico son sobre todo la salida y llegada por el centro de El Papiol
  (el punto que devuelve Nominatim está en una carretera local) y algunos cruces.
- Calibración del desnivel: nuestro cálculo da un 7-10 % más que el desnivel filtrado de
  BRouter sobre las mismas rutas, dentro del margen esperable de un modelo de 90 m.
