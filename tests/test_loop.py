import random

import pytest

from mtb_routes.core.analysis import distance_m
from mtb_routes.core.loop import circle_waypoints, generate_candidate, generate_candidates, offset
from mtb_routes.engines.base import EngineError

from .conftest import PAPIOL, FakeEngine


def test_offset_keeps_distance():
    target = offset(PAPIOL, 5000, 90)
    assert abs(distance_m(PAPIOL.lat, PAPIOL.lon, target.lat, target.lon) - 5000) < 1
    assert target.lon > PAPIOL.lon and abs(target.lat - PAPIOL.lat) < 0.001


def test_waypoints_surround_the_start():
    waypoints = circle_waypoints(PAPIOL, 3000, 0, 4, random.Random(1))
    assert len(waypoints) == 4
    for p in waypoints:
        assert 0 < distance_m(PAPIOL.lat, PAPIOL.lon, p.lat, p.lon) < 2 * 3000 * 1.2


@pytest.mark.parametrize("km", [15, 25, 40])
def test_converges_to_target_distance(engine, km):
    t = generate_candidate(engine, PAPIOL, km * 1000, "mixed", seed=42)
    assert abs(t.distance_m / (km * 1000) - 1) <= 0.10
    assert len(engine.calls) <= 6
    # The route starts and ends at the start point
    assert engine.calls[-1][0] == PAPIOL and engine.calls[-1][-1] == PAPIOL


def test_same_seed_same_route():
    a = generate_candidate(FakeEngine(), PAPIOL, 20_000, "mixed", seed=7)
    b = generate_candidate(FakeEngine(), PAPIOL, 20_000, "mixed", seed=7)
    assert a.waypoints == b.waypoints


def test_retries_when_engine_fails():
    engine = FakeEngine(initial_failures=2)
    t = generate_candidate(engine, PAPIOL, 15_000, "mixed", seed=3)
    assert t.distance_m > 0 and len(engine.calls) >= 3


def test_error_when_engine_always_fails():
    with pytest.raises(EngineError):
        generate_candidates(FakeEngine(initial_failures=999), PAPIOL, 15_000, "mixed", 1, n_candidates=2)


def test_generates_several_different_candidates(engine):
    candidates = generate_candidates(engine, PAPIOL, 25_000, "tracks", 100, n_candidates=3)
    assert len(candidates) == 3
    assert len({tuple(c.waypoints) for c in candidates}) == 3
