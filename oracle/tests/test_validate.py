import pytest

from validate import missing_measurements, violations

# 초안 임계값 (ontology/1_rules/README.md). foreground_cover_min은 미정이라 임의 값
PARAMS = {
    "search_radius": 2.0,
    "attach_distance": 0.5,
    "midpoint_ratio": 0.8,
    "char_terrain_overlap_max": 0.15,
    "item_terrain_overlap_max": 0.3,
    "support_gap_max": 0.1,
    "equip_gap_max": 0.05,
    "hud_overlap_min": 0.02,
    "hud_contain_min": 0.95,
    "text_contain_min": 0.98,
    "foreground_cover_min": 0.5,
}


# 테스트가 다루지 않는 측정값은 위반이 없는 값으로 채움. distance는 판정에 직접 쓰여 채우지 않음
NEUTRAL = {"overlap_ratio": 0.0, "support_gap": 0.0, "foreground_coverage": 0.0, "edge_distance": 0.0, "contain_ratio": 1.0, "mutual_overlap": 0.0}


def frame(instances, relations=(), measurements=()):
    f = {
        "instances": [{"id": i, "class": c} for i, c in instances],
        "relations": [{"type": t, "subject": s, "object": o} for t, s, o in relations],
        "measurements": [{"name": n, "args": list(a), "value": v} for n, a, v in measurements],
    }
    for name, args in missing_measurements(f):
        if name in NEUTRAL:
            f["measurements"].append({"name": name, "args": list(args), "value": NEUTRAL[name]})
    return f


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
    ((rule, targets),) = violations(f, PARAMS)
    assert rule == "R-003" and targets[0] == 3 and sorted(targets[1:]) == [1, 2]


def test_oxigraph_store_matches_default_store():
    """저장소만 바꾼 것이므로 rdflib 기본 저장소와 결과가 같아야 함"""
    f = frame(
        [(1, "HealthBar"), (2, "HealthBar"), (3, "Character"), (4, "Character"), (5, "Equipment")],
        relations=[("attachedTo", 5, 3)],
        measurements=[
            ("distance", [1, 3], 0.1), ("distance", [1, 4], 2.5), ("distance", [2, 3], 0.3), ("distance", [2, 4], 0.35), ("distance", [1, 5], 3.0), ("distance", [2, 5], 3.0),
            ("foreground_coverage", [1], 0.0), ("foreground_coverage", [2], 0.0),
            ("overlap_ratio", [3], 0.3), ("overlap_ratio", [4], 0.0), ("edge_distance", [5, 3], 0.2),
        ],
    )
    assert violations(f, PARAMS) == violations(f, PARAMS, store="Memory")
    assert violations(f, PARAMS)


def test_r002_display_far_from_its_target():
    f = frame([(1, "HealthBar"), (2, "Character")], relations=[("represents", 1, 2)], measurements=[("distance", [1, 2], 1.2), ("foreground_coverage", [1], 0.0)])
    assert violations(f, PARAMS) == [("R-002", (1, 2))]


def test_r002_defers_midpoint_case_to_r003():
    f = frame(
        [(1, "HealthBar"), (2, "Character"), (3, "Character")],
        relations=[("represents", 1, 2)],
        measurements=[("distance", [1, 2], 1.0), ("distance", [1, 3], 1.1), ("foreground_coverage", [1], 0.0)],
    )
    assert violations(f, PARAMS) == [("R-003", (1, 2, 3))]


def test_r005_item_in_terrain():
    f = frame([(1, "LooseObject")], measurements=[("overlap_ratio", [1], 0.5)])
    assert violations(f, PARAMS) == [("R-005", (1,))]


def test_r006_floating_object_and_exclusion():
    floating = frame([(1, "GroundedObject")], measurements=[("support_gap", [1], 0.5), ("foreground_coverage", [1], 0.0)])
    hidden = frame([(1, "GroundedObject")], measurements=[("support_gap", [1], 0.5), ("foreground_coverage", [1], 0.8)])
    assert violations(floating, PARAMS) == [("R-006", (1,))]
    assert violations(hidden, PARAMS) == []


def test_r009_partial_hud_overlap():
    partial = frame([(1, "HUDElement"), (2, "HUDElement")], measurements=[("mutual_overlap", [1, 2], 0.3)])
    nested = frame([(1, "HUDElement"), (2, "HUDElement")], measurements=[("mutual_overlap", [1, 2], 1.0)])
    assert violations(partial, PARAMS) == [("R-009", (1, 2))]
    assert violations(nested, PARAMS) == []


def test_r010_text_conditions():
    overflow = frame([(1, "TextLabel"), (2, "UIPanel")], relations=[("belongsTo", 1, 2)], measurements=[("contain_ratio", [2, 1], 0.8)])
    clipped = frame([(1, "TextLabel"), (2, "UIPanel")], relations=[("belongsTo", 1, 2), ("touches", 1, 2)], measurements=[("contain_ratio", [2, 1], 1.0)])
    other_panel = frame(
        [(1, "TextLabel"), (2, "UIPanel"), (3, "UIPanel")],
        relations=[("belongsTo", 1, 2), ("touches", 1, 3)],
        measurements=[("contain_ratio", [2, 1], 1.0), ("contain_ratio", [3, 1], 0.1)],
    )
    off_screen = frame([(1, "TextLabel")], relations=[("touches", 1, "ScreenBounds")])
    assert violations(overflow, PARAMS) == [("R-010", (1, 2))]
    assert violations(clipped, PARAMS) == [("R-010", (1, 2))]
    assert violations(other_panel, PARAMS) == []
    assert violations(off_screen, PARAMS) == [("R-010", (1, "ScreenBounds"))]


def test_missing_parameter_raises():
    params = dict(PARAMS)
    del params["equip_gap_max"]
    with pytest.raises(ValueError):
        violations(frame([]), params)


def test_r003_ties_give_one_violation_per_display():
    f = frame(
        [(1, "HealthBar"), (2, "Character"), (3, "Character"), (10, "Character")],
        measurements=[("distance", [1, 2], 1.0), ("distance", [1, 3], 1.0), ("distance", [1, 10], 1.0)],
    )
    assert violations(f, PARAMS) == [("R-003", (1, 2, 3))]


def test_r003_three_bars_on_one_target_is_one_violation():
    f = frame(
        [(1, "HealthBar"), (2, "HealthBar"), (4, "HealthBar"), (3, "Character")],
        measurements=[("distance", [1, 3], 0.1), ("distance", [2, 3], 0.2), ("distance", [4, 3], 0.3)],
    )
    ((rule, targets),) = violations(f, PARAMS)
    assert rule == "R-003" and targets[0] == 3 and sorted(targets[1:]) == [1, 2, 4]


def test_r009_either_direction_is_one_violation():
    f = frame([(2, "HUDElement"), (10, "HUDElement")], measurements=[("mutual_overlap", [10, 2], 0.3), ("mutual_overlap", [2, 10], 0.3)])
    assert violations(f, PARAMS) == [("R-009", (2, 10))]


def test_missing_measurement_raises():
    f = frame([(1, "HealthBar"), (2, "Character")])
    with pytest.raises(ValueError):
        violations(f, PARAMS)
