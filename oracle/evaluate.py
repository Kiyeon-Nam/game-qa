"""판정 평가: 정답 위반과 판정 리포트 비교 (검증 계획: 버그 주입 테스트셋)

- 정답: 판정 리포트 형식(schemas/report.schema.json). 대상 id는 라벨(schemas/label.schema.json) 인스턴스 id
- 탐지: (프레임, 규칙) 단위 precision·recall. 정답 프레임마다 리포트 필요
- 근거 일치율: 맞게 탐지한 (프레임, 규칙) 중 위반 대상 집합이 정답과 같은 비율
- 대상 id 대응: 추론 결과 인스턴스를 같은 클래스의 라벨 인스턴스와 마스크 IoU가 큰 순으로 1:1 대응
  - IOU_MIN 미만은 대응 없음 (그 대상은 불일치)
  - 라벨로 만든 추론 결과는 id가 같아 대응 없이 비교
- 라벨 이미지의 프레임: (file_name, 0)

실행: python -m game_qa.oracle.evaluate <정답 폴더> <리포트 폴더> [--labels <라벨.json> --results <추론 결과 폴더>]
"""

import argparse
import json
from pathlib import Path

import numpy as np
from pycocotools import mask as cocomask

from game_qa.inferlib.masks import decode

IOU_MIN = 0.5  # 초안 (COCO 관례)
SCREEN = "ScreenBounds"


def key(frame):
    return (frame["source"], frame["index"])


def match_instances(labeled, inferred, iou_min=IOU_MIN):
    """추론 결과 인스턴스 id → 라벨 인스턴스 id. 인스턴스: id, class, rle (압축 COCO RLE)"""
    pairs = []
    for p in inferred:
        for g in labeled:
            if p["class"] == g["class"]:
                iou = cocomask.iou([p["rle"]], [g["rle"]], [0])[0][0]
                if iou >= iou_min:
                    pairs.append((-iou, p["id"], g["id"]))
    out, used = {}, set()
    for _, p, g in sorted(pairs):
        if p not in out and g not in used:
            out[p] = g
            used.add(g)
    return out


def evaluate(truths, reports, mappings=None):
    """truths, reports: 판정 리포트 목록. mappings: 프레임 → (추론 결과 id → 라벨 id), 없으면 id가 같음"""
    predicted = {key(r["frame"]): r for r in reports}
    tp = fp = fn = agree = 0
    for truth in truths:
        frame = key(truth["frame"])
        if frame not in predicted:
            raise ValueError(f"리포트 없음: {frame}")
        ids = (mappings or {}).get(frame)

        def to_label(t):
            return t if ids is None or t == SCREEN else ids.get(t)

        want, got = {}, {}
        for v in truth["violations"]:
            want.setdefault(v["rule"], set()).add(frozenset(v["targets"]))
        for v in predicted[frame]["violations"]:
            got.setdefault(v["rule"], set()).add(frozenset(map(to_label, v["targets"])))
        for rule in want.keys() | got.keys():
            if rule in want and rule in got:
                tp += 1
                agree += want[rule] == got[rule]
            elif rule in got:
                fp += 1
            else:
                fn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn), "target_agreement": ratio(agree, tp)}


def ratio(a, b):
    return a / b if b else None


def rle(segmentation, height, width):
    """라벨·추론 결과의 segmentation(polygon, RLE)을 pycocotools RLE로"""
    return cocomask.encode(np.asfortranarray(decode(segmentation, height, width).astype(np.uint8)))


def mappings(labels, results):
    """라벨 파일과 추론 결과 목록으로 프레임별 id 대응"""
    names = {c["id"]: c["name"] for c in labels["categories"]}
    labeled = {}
    for img in labels["images"]:
        labeled[(img["file_name"], 0)] = [
            {"id": a["id"], "class": names[a["category_id"]], "rle": rle(a["segmentation"], img["height"], img["width"])}
            for a in labels["annotations"]
            if a["image_id"] == img["id"]
        ]
    out = {}
    for r in results:
        h, w = r["frame"]["height"], r["frame"]["width"]
        inferred = [{"id": x["id"], "class": x["class"], "rle": rle(x["segmentation"], h, w)} for x in r["instances"]]
        out[key(r["frame"])] = match_instances(labeled.get(key(r["frame"]), []), inferred)
    return out


def load_all(folder):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(folder).glob("*.json"))]


def main(argv=None):
    parser = argparse.ArgumentParser(description="판정 평가")
    parser.add_argument("truths")
    parser.add_argument("reports")
    parser.add_argument("--labels")
    parser.add_argument("--results")
    args = parser.parse_args(argv)
    if bool(args.labels) != bool(args.results):
        parser.error("--labels와 --results는 함께 지정")
    ids = mappings(json.loads(Path(args.labels).read_text(encoding="utf-8")), load_all(args.results)) if args.labels else None
    print(json.dumps(evaluate(load_all(args.truths), load_all(args.reports), ids), ensure_ascii=False))


if __name__ == "__main__":
    main()
