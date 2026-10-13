from validate import violations

# 초안 임계값 (ontology/1_rules/README.md). foreground_cover_min은 미정이라 임의 값
PARAMS = {
    "char_terrain_overlap_max": 0.15,
    "equip_gap_max": 0.05,
    "search_radius": 2.0,
    "attach_distance": 0.5,
    "midpoint_ratio": 0.8,
    "foreground_cover_min": 0.5,
}


def frame(instances, relations=(), measurements=()):
    return {
        "instances": [{"id": i, "class": c} for i, c in instances],
        "relations": [{"type": t, "subject": s, "object": o} for t, s, o in relations],
        "measurements": [{"name": n, "args": list(a), "value": v} for n, a, v in measurements],
    }


def test_r004_embedded_character():
    f = frame([(1, "Character"), (2, "Character")], measurements=[("overlap_ratio", [1], 0.4), ("overlap_ratio", [2], 0.05)])
    assert violations(f, PARAMS) == [("R-004", (1,))]


def test_r008_equipment_apart():
    f = frame(
        [(1, "Character"), (2, "Equipment"), (3, "Equipment")],
        relations=[("attachedTo", 2, 1), ("attachedTo", 3, 1)],
        measurements=[("edge_distance", [2, 1], 0.3), ("edge_distance", [3, 1], 0.0)],
    )
    assert violations(f, PARAMS) == [("R-008", (2, 1))]


def test_r001_display_without_target():
    f = frame([(1, "HealthBar"), (2, "Character")], measurements=[("distance", [1, 2], 3.0), ("foreground_coverage", [1], 0.0)])
    assert violations(f, PARAMS) == [("R-001", (1,))]


def test_r001_exclusions():
    edge = frame([(1, "HealthBar")], relations=[("touches", 1, "ScreenBounds")], measurements=[("foreground_coverage", [1], 0.0)])
    hidden = frame([(1, "HealthBar")], measurements=[("foreground_coverage", [1], 0.9)])
    hud = frame([(1, "HUDElement")])
    assert violations(edge, PARAMS) == []
    assert violations(hidden, PARAMS) == []
    assert violations(hud, PARAMS) == []


def test_r003_display_between_two_targets():
    f = frame(
        [(1, "HealthBar"), (2, "Character"), (3, "Character"), (4, "Character")],
        relations=[("represents", 1, 2)],
        measurements=[("distance", [1, 2], 1.0), ("distance", [1, 3], 1.1), ("distance", [1, 4], 1.9), ("foreground_coverage", [1], 0.0)],
    )
    assert violations(f, PARAMS) == [("R-003", (1, 2, 3))]


def test_r003_two_bars_on_one_target():
    f = frame(
        [(1, "HealthBar"), (2, "HealthBar"), (3, "Character")],
        measurements=[("distance", [1, 3], 0.1), ("distance", [2, 3], 0.3), ("foreground_coverage", [1], 0.0), ("foreground_coverage", [2], 0.0)],
    )
    assert violations(f, PARAMS) == [("R-003", (3, 1, 2))]


def test_oxigraph_store_matches_default_store():
    """저장소만 바꾼 것이므로 rdflib 기본 저장소와 결과가 같아야 함"""
    f = frame(
        [(1, "HealthBar"), (2, "HealthBar"), (3, "Character"), (4, "Character"), (5, "Equipment")],
        relations=[("attachedTo", 5, 3)],
        measurements=[
            ("distance", [1, 3], 0.1), ("distance", [1, 4], 2.5), ("distance", [2, 3], 0.3), ("distance", [2, 4], 0.35),
            ("foreground_coverage", [1], 0.0), ("foreground_coverage", [2], 0.0),
            ("overlap_ratio", [3], 0.3), ("overlap_ratio", [4], 0.0), ("edge_distance", [5, 3], 0.2),
        ],
    )
    assert violations(f, PARAMS) == violations(f, PARAMS, store="Memory")
    assert violations(f, PARAMS)
