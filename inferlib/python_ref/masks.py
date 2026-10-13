"""마스크 변환과 기하 보조 함수. 좌표는 픽셀 경계 기준 (픽셀 (x, y)는 [x, x+1) × [y, y+1))"""

import numpy as np
from pycocotools import mask as cocomask
from scipy import ndimage

FOUR = ndimage.generate_binary_structure(2, 1)


def decode(segmentation, height, width):
    """COCO polygon, 비압축 RLE, 압축 RLE를 bool 마스크로 변환"""
    if isinstance(segmentation, list):
        rle = cocomask.merge(cocomask.frPyObjects(segmentation, height, width))
    elif isinstance(segmentation["counts"], list):
        rle = cocomask.frPyObjects(segmentation, height, width)
    else:
        rle = segmentation
    return cocomask.decode(rle).astype(bool)


def encode(mask):
    """bool 마스크를 압축 COCO RLE로 변환"""
    rle = cocomask.encode(np.asfortranarray(mask.astype(np.uint8)))
    return {"size": [int(s) for s in rle["size"]], "counts": rle["counts"].decode("ascii")}


def bbox(mask):
    """(x0, y0, x1, y1). x1, y1은 마지막 픽셀의 다음 경계"""
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def inner_boundary(mask):
    """마스크 픽셀 중 4방향 이웃에 마스크 밖 픽셀이 있는 픽셀"""
    return mask & ~ndimage.binary_erosion(mask, FOUR, border_value=0)


def neighbors(mask):
    """마스크와 4방향으로 맞닿은 픽셀 (마스크 포함)"""
    return ndimage.binary_dilation(mask, FOUR)
