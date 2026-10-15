"""라벨(schemas/label.schema.json)을 Ultralytics YOLO 세그멘테이션 데이터셋으로 변환

- 클래스 ID: 라벨 category id 그대로 (0부터 연속)
- 인스턴스 하나 = 폴리곤 하나. 여러 조각은 폭 0 다리로 이어 붙이고, RLE는 외곽선으로 변환 (구멍 무시)
- relations는 학습에 쓰지 않음
- 학습·검증 분할: 이미지 파일 이름 정렬 후 seed로 섞음. 같은 라벨·seed면 같은 분할

실행: python convert.py <이미지 폴더> <출력 폴더> <라벨.json ...> [--val 0.2] [--seed 0]
"""

import argparse
import json
import random
import shutil
from pathlib import Path

import cv2
import numpy as np
import yaml
from pycocotools import mask as cocomask


def polygons(segmentation, height, width):
    """COCO segmentation을 픽셀 좌표 폴리곤 목록으로. 각 폴리곤은 (N, 2)"""
    if isinstance(segmentation, list):
        return [np.asarray(p, dtype=float).reshape(-1, 2) for p in segmentation]
    rle = segmentation
    if isinstance(rle["counts"], list):
        rle = cocomask.frPyObjects(rle, height, width)
    elif isinstance(rle["counts"], str):
        rle = {"size": rle["size"], "counts": rle["counts"].encode("ascii")}
    mask = cocomask.decode(rle).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [c.reshape(-1, 2).astype(float) for c in contours if len(c) >= 3]


def merge(parts):
    """폴리곤 여러 개를 가장 가까운 점끼리 폭 0 다리로 이어 하나로"""
    merged = parts[0]
    for part in parts[1:]:
        d = np.linalg.norm(merged[:, None] - part[None], axis=-1)
        a, b = np.unravel_index(d.argmin(), d.shape)
        part = np.roll(part, -b, axis=0)
        merged = np.concatenate([merged[: a + 1], part, part[:1], merged[a:]])
    return merged


def yolo_line(cls, polygon, width, height):
    xy = np.clip(polygon / [width, height], 0, 1)
    return " ".join([str(cls)] + [f"{v:.6f}" for v in xy.ravel()])


def split(names, val, seed):
    """(학습, 검증) 이미지 이름 집합. 이미지가 하나면 둘 다 그 이미지"""
    names = sorted(names)
    if len(names) == 1:
        return set(names), set(names)
    random.Random(seed).shuffle(names)
    n = min(len(names) - 1, max(1, round(len(names) * val)))
    return set(names[n:]), set(names[:n])


def convert(image_dir, out_dir, labels, val=0.2, seed=0):
    """labels: 라벨 dict 목록. data.yaml 경로 반환"""
    categories = sorted((c["id"], c["name"]) for c in labels[0]["categories"])
    if any(sorted((c["id"], c["name"]) for c in lb["categories"]) != categories for lb in labels):
        raise ValueError("라벨 파일마다 categories가 다름")
    if [i for i, _ in categories] != list(range(len(categories))):
        raise ValueError("category id가 0부터 연속이 아님")

    images, annotations = {}, {}
    for lb in labels:
        by_id = {}
        for img in lb["images"]:
            if img["file_name"] in images:
                raise ValueError(f"이미지 중복: {img['file_name']}")
            images[img["file_name"]] = img
            annotations[img["file_name"]] = []
            by_id[img["id"]] = img["file_name"]
        for a in lb["annotations"]:
            annotations[by_id[a["image_id"]]].append(a)

    out = Path(out_dir)
    train, valid = split(images, val, seed)
    for subset, names in (("train", train), ("val", valid)):
        (out / "images" / subset).mkdir(parents=True, exist_ok=True)
        (out / "labels" / subset).mkdir(parents=True, exist_ok=True)
        for name in sorted(names):
            img = images[name]
            shutil.copy2(Path(image_dir) / name, out / "images" / subset / name)
            lines = [
                yolo_line(a["category_id"], merge(polygons(a["segmentation"], img["height"], img["width"])), img["width"], img["height"])
                for a in annotations[name]
            ]
            (out / "labels" / subset / f"{Path(name).stem}.txt").write_text("\n".join(lines), encoding="utf-8")

    data = {"path": str(out.resolve()), "train": "images/train", "val": "images/val", "names": dict(categories)}
    path = out / "data.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image_dir")
    parser.add_argument("out_dir")
    parser.add_argument("labels", nargs="+")
    parser.add_argument("--val", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    labels = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.labels]
    print(convert(args.image_dir, args.out_dir, labels, args.val, args.seed))


if __name__ == "__main__":
    main()
