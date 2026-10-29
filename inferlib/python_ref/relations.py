"""관계. 결정 근거는 ontology/3_relations.md의 관계 표"""

import numpy as np
from scipy.optimize import linear_sum_assignment

from game_qa.inferlib.masks import neighbors


def represents(distances, search_radius):
    """대응한 쌍의 거리 합 + 대응하지 못한 표시 수 × search_radius가 최소인 1:1 대응.
    search_radius를 넘는 쌍은 후보에서 제외. (표시 위치, 개체 위치) 목록"""
    if not len(distances) or not len(distances[0]):
        return []
    d = np.asarray(distances, dtype=float)
    n, m = d.shape
    # 표시마다 자기 전용 미대응 열(비용 search_radius)을 붙임. 반경 밖 쌍은 미대응보다 비싸게
    unmatched = np.full((n, n), np.inf)
    np.fill_diagonal(unmatched, search_radius)
    cost = np.hstack([np.where(d <= search_radius, d, np.inf), unmatched])
    rows, cols = linear_sum_assignment(cost)
    return [(r, c) for r, c in zip(rows, cols) if c < m]


def nearest(values):
    """값이 가장 작은 위치. 없으면 None"""
    return int(np.argmin(values)) if len(values) else None


def largest_positive(values):
    """양수 중 값이 가장 큰 위치. 없으면 None"""
    if not len(values) or max(values) <= 0:
        return None
    return int(np.argmax(values))


def touches(x, p):
    """x가 p 안쪽에서 p 경계선에 닿음. 화면 밖은 p 밖으로 봄"""
    outside = np.pad(~p, 1, constant_values=True)
    near_outside = neighbors(outside)[1:-1, 1:-1]
    return bool((x & p & near_outside).any())
