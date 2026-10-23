"""측정값. 정의는 ontology/3_relations.md의 측정값 표"""

import math

import numpy as np
from scipy import ndimage

from game_qa.inferlib.masks import bbox


def _height(mask):
    _, y0, _, y1 = bbox(mask)
    return y1 - y0


def distance(i, e):
    """표시 하단 중심과 개체 bbox 상단 중심 사이 거리 / 개체 bbox 높이"""
    ix0, _, ix1, iy1 = bbox(i)
    ex0, ey0, ex1, ey1 = bbox(e)
    d = math.hypot((ix0 + ix1) / 2 - (ex0 + ex1) / 2, iy1 - ey0)
    return d / (ey1 - ey0)


def _fill_runs(a, terrain, out):
    """a의 행마다 연속 구간의 바로 바깥 양쪽 픽셀이 모두 terrain이면 그 구간을 out에 채움"""
    for y in np.flatnonzero(a.any(axis=1)):
        edges = np.diff(np.concatenate(([0], a[y].astype(np.int8), [0])))
        for s, e in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
            if s > 0 and e < a.shape[1] and terrain[y, s - 1] and terrain[y, e]:
                out[y, s:e] = True


def estimated_terrain(a, terrain):
    """모든 Terrain + 대상의 행·열 연속 구간 중 바로 바깥 양쪽이 모두 Terrain인 구간"""
    est = terrain.copy()
    _fill_runs(a, terrain, est)
    _fill_runs(a.T, terrain.T, est.T)
    return est


def overlap_ratio(a, terrain):
    """대상 중 추정 지형과 겹치는 면적 / 대상 면적. terrain은 모든 Terrain의 합집합"""
    return float((a & estimated_terrain(a, terrain)).sum() / a.sum())


def mutual_overlap(a, b):
    """두 요소가 겹치는 면적 / 작은 요소 면적"""
    return float((a & b).sum() / min(a.sum(), b.sum()))


def contain_ratio(p, x):
    """텍스트 중 p 안에 있는 면적 / 텍스트 면적"""
    return float((x & p).sum() / x.sum())


def support_gap(o, support):
    """오브젝트 하단과 바로 아래 지지 구조물 상단 사이 수직 간격 / 오브젝트 높이.
    아래에 지지 구조물이 없으면 화면 하단까지의 간격"""
    x0, y0, x1, y1 = bbox(o)
    below = support[y1:, x0:x1]
    rows = [np.argmax(col) for col in below.T if col.any()]
    gap = min(rows) if rows else below.shape[0]
    return gap / (y1 - y0)


def edge_distance(q, c):
    """두 마스크 사이 최소 간격(8방향 기준 픽셀 수) / 캐릭터 bbox 높이. 대각선 포함 맞닿거나 겹치면 0"""
    gap = ndimage.distance_transform_cdt(~c, metric="chessboard")[q].min() - 1
    return max(float(gap), 0.0) / _height(c)


def foreground_coverage_display(i, fg, fg_search_radius):
    """i 하단 중심에서 반지름 fg_search_radius × i bbox 너비인 원 중 전경 비율"""
    x0, _, x1, y1 = bbox(i)
    cx, cy, r = (x0 + x1) / 2, y1, fg_search_radius * (x1 - x0)
    ys, xs = np.mgrid[: i.shape[0], : i.shape[1]]
    region = (xs + 0.5 - cx) ** 2 + (ys + 0.5 - cy) ** 2 <= r**2
    return _coverage(region, fg)


def foreground_coverage_object(o, fg, support_gap_max):
    """o 바로 아래, 너비 o bbox 너비·높이 support_gap_max × o 높이인 사각형 중 전경 비율"""
    x0, y0, x1, y1 = bbox(o)
    region = np.zeros_like(o)
    region[y1 : y1 + math.ceil(support_gap_max * (y1 - y0)), x0:x1] = True
    return _coverage(region, fg)


def _coverage(region, fg):
    area = region.sum()
    return float((region & fg).sum() / area) if area else 0.0
