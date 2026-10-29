"""인스턴스 마스크에서 추론 결과(schemas/inference.schema.json) 생성

라벨 파일로 실행: python -m game_qa.inferlib.infer <라벨.json> <파라미터.json> <출력 폴더>
"""

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

from game_qa.inferlib import measurements, relations
from game_qa.inferlib.masks import decode, encode
from game_qa.ontology.game_ui import has

PARAMS = ("search_radius", "fg_search_radius", "support_gap_max")
SCREEN = "ScreenBounds"


def infer_frame(frame, instances, params):
    """frame: source, index, width, height
    instances: id, class, score, mask(bool 배열) 목록
    params: PARAMS 값
    빈 마스크 인스턴스는 계산과 출력에서 제외"""
    instances = [x for x in instances if x["mask"].any()]
    shape = (frame["height"], frame["width"])

    def with_concepts(*concepts):
        return [x for x in instances if has(x["class"], *concepts)]

    def of_class(*classes):
        return [x for x in instances if x["class"] in classes]

    def union(xs):
        return np.logical_or.reduce([x["mask"] for x in xs]) if xs else np.zeros(shape, bool)

    values, rels = [], []

    def value(name, args, v):
        values.append({"name": name, "args": [a if a == SCREEN else a["id"] for a in args], "value": float(v)})

    def rel(type_, subject, obj):
        rels.append({"type": type_, "subject": subject["id"], "object": obj if obj == SCREEN else obj["id"]})

    characters = of_class("Character")
    foreground = union(of_class("ForegroundDecoration"))
    screen = np.ones(shape, bool)

    # 월드 표시와 개체: distance, foreground_coverage, represents
    world, entities = with_concepts("Display", "World"), with_concepts("Entity")
    dist = [[measurements.distance(i["mask"], e["mask"]) for e in entities] for i in world]
    for i, row in zip(world, dist):
        for e, d in zip(entities, row):
            value("distance", [i, e], d)
        value("foreground_coverage", [i], measurements.foreground_coverage_display(i["mask"], foreground, params["fg_search_radius"]))
    for a, b in relations.represents(dist, params["search_radius"]):
        rel("represents", world[a], entities[b])

    # 개체와 지형: overlap_ratio
    terrain = union(of_class("Terrain"))
    for a in of_class("Character", "LooseObject"):
        value("overlap_ratio", [a], measurements.overlap_ratio(a["mask"], terrain))

    # 고정 오브젝트: support_gap, foreground_coverage
    support = union(of_class("Terrain", "Platform"))
    for o in of_class("GroundedObject"):
        value("support_gap", [o], measurements.support_gap(o["mask"], support))
        value("foreground_coverage", [o], measurements.foreground_coverage_object(o["mask"], foreground, params["support_gap_max"]))

    # 장비와 캐릭터: edge_distance, attachedTo
    for q in of_class("Equipment"):
        gaps = [measurements.edge_distance(q["mask"], c["mask"]) for c in characters]
        for c, g in zip(characters, gaps):
            value("edge_distance", [q, c], g)
        k = relations.nearest(gaps)
        if k is not None:
            rel("attachedTo", q, characters[k])

    # HUD 요소 사이: mutual_overlap
    for a, b in combinations(of_class("HUDElement"), 2):
        value("mutual_overlap", [a, b], measurements.mutual_overlap(a["mask"], b["mask"]))

    # 텍스트와 패널·화면: contain_ratio, belongsTo, touches
    panels = of_class("UIPanel")
    for x in of_class("TextLabel"):
        ratios = [measurements.contain_ratio(p["mask"], x["mask"]) for p in panels]
        for p, v in zip(panels, ratios):
            value("contain_ratio", [p, x], v)
            if relations.touches(x["mask"], p["mask"]):
                rel("touches", x, p)
        if relations.touches(x["mask"], screen):
            rel("touches", x, SCREEN)
        k = relations.largest_positive(ratios)
        if k is not None:
            rel("belongsTo", x, panels[k])

    # 표시와 화면 경계: touches
    for i in with_concepts("Display"):
        if relations.touches(i["mask"], screen):
            rel("touches", i, SCREEN)

    return {
        "frame": frame,
        "instances": [{"id": x["id"], "class": x["class"], "score": x["score"], "segmentation": encode(x["mask"])} for x in instances],
        "relations": rels,
        "measurements": values,
    }


def from_labels(labels, params):
    """라벨 파일(schemas/label.schema.json)의 이미지마다 추론 결과 생성. score는 1"""
    names = {c["id"]: c["name"] for c in labels["categories"]}
    for img in labels["images"]:
        h, w = img["height"], img["width"]
        instances = [
            {"id": a["id"], "class": names[a["category_id"]], "score": 1.0, "mask": decode(a["segmentation"], h, w)}
            for a in labels["annotations"]
            if a["image_id"] == img["id"]
        ]
        frame = {"source": img["file_name"], "index": 0, "width": w, "height": h}
        yield infer_frame(frame, instances, params)


def main(label_path, params_path, out_dir):
    labels = json.loads(Path(label_path).read_text(encoding="utf-8"))
    params = json.loads(Path(params_path).read_text(encoding="utf-8"))
    missing = [k for k in PARAMS if k not in params]
    if missing:
        sys.exit(f"파라미터 누락: {', '.join(missing)}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for result in from_labels(labels, params):
        path = out / (Path(result["frame"]["source"]).stem + ".json")
        path.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
