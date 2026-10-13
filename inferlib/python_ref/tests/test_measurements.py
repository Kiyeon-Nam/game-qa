import numpy as np
import pytest

import measurements as m
import relations as r

H, W = 40, 40


def rect(x0, y0, x1, y1):
    mask = np.zeros((H, W), bool)
    mask[y0:y1, x0:x1] = True
    return mask


def test_distance_zero_when_display_sits_on_entity_top():
    assert m.distance(rect(10, 8, 20, 10), rect(10, 10, 20, 20)) == 0


def test_distance_normalized_by_entity_height():
    assert m.distance(rect(10, 0, 20, 5), rect(10, 10, 20, 20)) == pytest.approx(0.5)


def test_overlap_ratio_embedded_character():
    wall = rect(0, 0, 30, 30) & ~rect(10, 10, 15, 20)
    assert m.overlap_ratio(rect(10, 10, 15, 20), wall) == 1


def test_overlap_ratio_sunk_into_floor():
    # 캐릭터 하단 5행이 바닥에 파묻힘. 바닥 마스크는 위로 열린 홈
    c = rect(10, 15, 15, 25)
    assert m.overlap_ratio(c, rect(0, 20, 40, 40) & ~c) == pytest.approx(0.5)


def test_overlap_ratio_standing_in_closed_room():
    room = rect(0, 0, 40, 40) & ~rect(5, 5, 35, 30)
    assert m.overlap_ratio(rect(10, 20, 15, 30), room) == 0


def test_overlap_ratio_character_on_floor():
    assert m.overlap_ratio(rect(10, 10, 15, 20), rect(0, 20, 40, 40)) == 0


def test_mutual_overlap_uses_smaller_area():
    assert m.mutual_overlap(rect(0, 0, 10, 10), rect(5, 0, 10, 5)) == 1


def test_contain_ratio():
    assert m.contain_ratio(rect(0, 0, 10, 10), rect(5, 0, 15, 10)) == pytest.approx(0.5)


def test_support_gap():
    floor = rect(0, 30, 40, 40)
    assert m.support_gap(rect(10, 20, 20, 30), floor) == 0
    assert m.support_gap(rect(10, 15, 20, 25), floor) == pytest.approx(0.5)


def test_support_gap_without_support_measures_to_screen_bottom():
    assert m.support_gap(rect(10, 20, 20, 30), np.zeros((H, W), bool)) == pytest.approx(1.0)


def test_edge_distance():
    c = rect(10, 10, 20, 30)
    assert m.edge_distance(rect(20, 15, 25, 18), c) == 0
    assert m.edge_distance(rect(23, 15, 25, 18), c) == pytest.approx(3 / 20)
    assert m.edge_distance(rect(20, 30, 22, 32), c) == 0


def test_foreground_coverage_display():
    bar, bush = rect(10, 10, 14, 11), rect(0, 0, 40, 40)
    assert m.foreground_coverage_display(bar, bush, 2.0) == 1
    assert m.foreground_coverage_display(bar, np.zeros((H, W), bool), 2.0) == 0


def test_foreground_coverage_object():
    box = rect(10, 10, 20, 20)
    assert m.foreground_coverage_object(box, rect(0, 20, 40, 21), 0.1) == 1
    assert m.foreground_coverage_object(box, rect(0, 21, 40, 40), 0.1) == 0


def test_represents_one_to_one_within_radius():
    assert sorted(r.represents([[0.1, 0.2], [0.15, 1.0]], 2.0)) == [(0, 1), (1, 0)]
    assert r.represents([[3.0]], 2.0) == []


def test_represents_leaves_display_unmatched_rather_than_breaking_good_pair():
    # 대응 수를 늘리려고 0.1 쌍을 깨지 않음
    assert r.represents([[0.1, 1.9], [1.9, 9.0]], 2.0) == [(0, 0)]


def test_touches():
    panel = rect(0, 0, 20, 20)
    assert r.touches(rect(15, 5, 20, 8), panel)
    assert not r.touches(rect(5, 5, 10, 8), panel)
    assert r.touches(rect(0, 5, 3, 8), np.ones((H, W), bool))
