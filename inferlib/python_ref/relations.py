"""관계. 결정 근거는 ontology/3_relations.md의 관계 표"""

import numpy as np
from scipy.optimize import linear_sum_assignment

from masks import neighbors


def represents(distances, search_radius):
    """표시 × 개체 거리 행렬에서 search_radius 이내 1:1 대응. (표시 위치, 개체 위치) 목록"""
    d = np.asarray(distances, dtype=float)
    if d.size == 0:
        return []
    cost = np.where(d <= search_radius, d, d.max() + search_radius + 1)
    rows, cols = linear_sum_assignment(cost)
    return [(r, c) for r, c in zip(rows, cols) if d[r, c] <= search_radius]


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
