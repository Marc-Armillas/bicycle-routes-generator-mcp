from mtb_routes.core import analysis as a
from mtb_routes.core.models import ProtectedAreaCrossing, RouteRequest, Segment, Track, TrackPoint


def line(n: int, elevation) -> list[TrackPoint]:
    """Points heading north every ~11 m (0.0001° of latitude)."""
    return [TrackPoint(41.0 + i * 0.0001, 2.0, elevation(i)) for i in range(n)]


def track(points, segments=None) -> Track:
    dist = a.cumulative_distances(points)[-1]
    return Track(points, segments or [Segment(dist, {"highway": "track"})], dist, "test", "test")


def test_one_degree_of_latitude():
    assert abs(a.distance_m(41, 2, 42, 2) - 111_195) < 50


def test_elevation_gain_ignores_noise_below_threshold():
    noise = [100, 102, 99, 101, 100, 102, 100]
    assert a.elevation_gain(noise) == (0.0, 0.0)
    # +10, -5, +15, -20: all above the 4 m threshold
    assert a.elevation_gain([100, 110, 105, 120, 100]) == (25.0, 25.0)
    assert a.elevation_gain([100, 103, 106, 109]) == (9.0, 0.0)


def test_surface_classification():
    assert a.classify({"highway": "track"}) == "track"
    assert a.classify({"highway": "track", "surface": "asphalt"}) == "paved"
    assert a.classify({"highway": "track", "tracktype": "grade1"}) == "paved"
    assert a.classify({"highway": "path"}) == "path"
    assert a.classify({"highway": "path", "surface": "asphalt"}) == "path"
    assert a.classify({"highway": "footway", "surface": "paving_stones"}) == "paved"
    assert a.classify({"highway": "unclassified", "surface": "gravel"}) == "track"
    assert a.classify({"highway": "residential"}) == "paved"
    assert a.classify({}) == "unknown"


def test_traffic_access_and_technical_detection():
    assert a.has_traffic({"highway": "tertiary"})
    assert a.has_traffic({"highway": "primary_link"})
    assert a.has_traffic({"highway": "unclassified", "estimated_traffic_class": "5"})
    assert not a.has_traffic({"highway": "residential", "estimated_traffic_class": "2"})
    assert a.bike_forbidden({"highway": "path", "bicycle": "no"})
    assert a.bike_forbidden({"highway": "track", "access": "private"})
    assert not a.bike_forbidden({"highway": "track", "access": "no", "bicycle": "yes"})
    assert a.is_technical({"mtb:scale": "3"}) and a.is_technical({"highway": "steps"})
    assert not a.is_technical({"mtb:scale": "1"})


def test_heavy_traffic_detection_for_road_bikes():
    assert a.has_heavy_traffic({"highway": "primary"}) and a.has_heavy_traffic({"highway": "trunk_link"})
    assert a.has_heavy_traffic({"highway": "secondary", "estimated_traffic_class": "6"})
    assert not a.has_heavy_traffic({"highway": "tertiary"})
    assert not a.has_heavy_traffic({"highway": "secondary", "estimated_traffic_class": "5"})


def test_road_route_warns_about_unpaved_and_busy_roads_only():
    segs = [
        Segment(1000, {"highway": "tertiary"}),
        Segment(400, {"highway": "track", "surface": "gravel"}),
        Segment(600, {"highway": "primary"}),
    ]
    s = a.analyze(track(line(50, lambda i: 100.0), segs), RouteRequest("x", 2, trail_type="road"))
    traffic = [w for w in s.warnings if w.kind == "traffic" and w.start_km is not None]
    assert [(w.start_km, w.end_km) for w in traffic] == [(1.4, 2.0)]  # the primary, not the tertiary
    surface = [w for w in s.warnings if w.kind == "surface"]
    assert "road bike" in surface[0].message and (surface[1].start_km, surface[1].end_km) == (1.0, 1.4)
    mtb = a.analyze(track(line(50, lambda i: 100.0), segs), RouteRequest("x", 2))
    assert not [w for w in mtb.warnings if w.kind == "surface"]


def test_road_score_prefers_pavement():
    pts = line(100, lambda i: 100.0)
    paved = track(pts, [Segment(1000, {"highway": "tertiary"})])
    dirt = track(pts, [Segment(1000, {"highway": "track"})])
    road, mtb = RouteRequest("x", 2, trail_type="road"), RouteRequest("x", 2, trail_type="tracks")
    assert a.score(paved, a.analyze(paved, road), road) < a.score(dirt, a.analyze(dirt, road), road)
    assert a.score(dirt, a.analyze(dirt, mtb), mtb) < a.score(paved, a.analyze(paved, mtb), mtb)


def test_grade_over_12_percent_warns():
    # 300 m flat, ~300 m at 20 %, 300 m flat
    def ele(i):
        if i < 27:
            return 100.0
        if i < 54:
            return 100 + (i - 27) * 11.1 * 0.20
        return 100 + 27 * 11.1 * 0.20

    s = a.analyze(track(line(82, ele)), RouteRequest("x", 2))
    assert 17 < s.max_uphill_grade_pct < 23
    warnings = [w for w in s.warnings if w.kind == "grade"]
    assert len(warnings) == 1 and "climb" in warnings[0].message
    assert 0.2 < warnings[0].start_km < 0.4


def test_gentle_grade_does_not_warn():
    s = a.analyze(track(line(200, lambda i: 100 + i * 11.1 * 0.05)), RouteRequest("x", 2))
    assert not [w for w in s.warnings if w.kind == "grade"]
    assert 4 < s.max_uphill_grade_pct < 6
    assert abs(s.ascent_m - 199 * 11.1 * 0.05) < 10


def test_surface_breakdown_and_traffic_and_access_warnings():
    segs = [
        Segment(1000, {"highway": "track"}),
        Segment(500, {"highway": "secondary"}),
        Segment(300, {"highway": "path", "bicycle": "no"}),
        Segment(200, {"highway": "residential"}),
    ]
    s = a.analyze(track(line(50, lambda i: 100.0), segs), RouteRequest("x", 2))
    assert s.surface_pct["track"] == 50 and s.surface_pct["paved"] == 35 and s.surface_pct["path"] == 15
    traffic = [w for w in s.warnings if w.kind == "traffic" and w.start_km is not None]
    assert traffic[0].start_km == 1.0 and traffic[0].end_km == 1.5
    access = [w for w in s.warnings if w.kind == "access"]
    assert access and access[0].start_km == 1.5


def test_general_warnings_always_present():
    s = a.analyze(track(line(20, lambda i: 100.0)), RouteRequest("x", 2))
    general = [w.message for w in s.warnings if w.kind == "general"]
    assert any("barometric" in m for m in general)
    assert any("check it on a map" in m for m in general)


def test_collserola_protected_area_with_singletrack():
    segs = [Segment(1000, {"highway": "track"}), Segment(800, {"highway": "path"})]
    t = track(line(50, lambda i: 100.0), segs)
    s = a.analyze(t, RouteRequest("x", 2), [ProtectedAreaCrossing("Parc Natural de Collserola", 0.5, 1.8)])
    area = [w for w in s.warnings if w.kind == "protected_area"][0]
    assert "3 m" in area.message and "singletrack" in area.message


def test_distance_and_climb_exceeded_warnings():
    t = track(line(100, lambda i: 100 + (i % 20) * 3))  # ~1.1 km sawtooth
    s = a.analyze(t, RouteRequest("x", 5, max_climb_m=50))
    assert {"distance", "climb"} <= {w.kind for w in s.warnings}


def test_overlap_out_and_back():
    out = line(200, lambda i: 100.0)
    assert a.overlap_ratio(out) == 0
    assert a.overlap_ratio(out + out[::-1]) > 0.4


def test_score_penalises_traffic():
    pts = line(100, lambda i: 100.0)
    good = track(pts, [Segment(1000, {"highway": "track"})])
    bad = track(pts, [Segment(1000, {"highway": "primary"})])
    r = RouteRequest("x", 2, trail_type="tracks")
    assert a.score(good, a.analyze(good, r), r) < a.score(bad, a.analyze(bad, r), r)
