"""인스턴스 마스크에서 추론 결과(schemas/inference.schema.json) 생성

라벨 파일로 실행: python infer.py <라벨.json> <파라미터.json> <출력 폴더>
"""

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

import measurements as m
import relations as r
from concepts import has
from masks import decode, encode

PARAMS = ("search_radius", "fg_search_radius", "support_gap_max")
SCREEN = "ScreenBounds"


def infer_frame(frame, instances, params):
    """frame: source, index, width, height
    instances: id, class, score, mask(bool 배열) 목록
    params: PARAMS의 값 (게임별 매핑 적용 값)"""
    def by(*concepts):
        return [x for x in instances if has(x["class"], *concepts)]

    def of(cls):
        return [x for x in instances if x["class"] == cls]

    def union(xs):
        masks = [x["mask"] for x in xs]
        return np.logical_or.reduce(masks) if masks else np.zeros((frame["height"], frame["width"]), bool)

    displays, world, entities = by("Display"), by("Display", "World"), by("Entity")
    characters, terrains, grounded = of("Character"), of("Terrain"), of("GroundedObject")
    equipment, huds, panels, texts = of("Equipment"), of("HUDElement"), of("UIPanel"), of("TextLabel")
    foreground = union(of("ForegroundDecoration"))
    support = union(terrains + of("Platform"))
    screen = np.ones((frame["height"], frame["width"]), bool)

    out, rel = [], []

    def add(name, args, value):
        out.append({"name": name, "args": args, "value": round(float(value), 6)})

    dist = [[m.distance(i["mask"], e["mask"]) for e in entities] for i in world]
    for a, i in enumerate(world):
        for b, e in enumerate(entities):
            add("distance", [i["id"], e["id"]], dist[a][b])
        add("foreground_coverage", [i["id"]], m.foreground_coverage_display(i["mask"], foreground, params["fg_search_radius"]))
    for a, b in r.represents(dist, params["search_radius"]):
        rel.append({"type": "represents", "subject": world[a]["id"], "object": entities[b]["id"]})

    for a in characters + of("LooseObject"):
        for t in terrains:
            add("overlap_ratio", [a["id"], t["id"]], m.overlap_ratio(a["mask"], t["mask"]))
    for c in characters:
        for t in terrains:
            add("contact_boundary_ratio", [c["id"], t["id"]], m.contact_boundary_ratio(c["mask"], t["mask"]))

    for o in grounded:
        add("support_gap", [o["id"]], m.support_gap(o["mask"], support))
        add("foreground_coverage", [o["id"]], m.foreground_coverage_object(o["mask"], foreground, params["support_gap_max"]))

    for q in equipment:
        gaps = [m.edge_distance(q["mask"], c["mask"]) for c in characters]
        for c, g in zip(characters, gaps):
            add("edge_distance", [q["id"], c["id"]], g)
        k = r.nearest(gaps)
        if k is not None:
            rel.append({"type": "attachedTo", "subject": q["id"], "object": characters[k]["id"]})

    for a, b in combinations(huds, 2):
        add("mutual_overlap", [a["id"], b["id"]], m.mutual_overlap(a["mask"], b["mask"]))

    for x in texts:
        ratios = [m.contain_ratio(p["mask"], x["mask"]) for p in panels]
        for p, v in zip(panels, ratios):
            add("contain_ratio", [p["id"], x["id"]], v)
            if r.touches(x["mask"], p["mask"]):
                rel.append({"type": "touches", "subject": x["id"], "object": p["id"]})
        add("contain_ratio", [SCREEN, x["id"]], m.contain_ratio(screen, x["mask"]))
        k = r.largest_positive(ratios)
        if k is not None:
            rel.append({"type": "belongsTo", "subject": x["id"], "object": panels[k]["id"]})

    for i in displays:
        if r.touches(i["mask"], screen):
            rel.append({"type": "touches", "subject": i["id"], "object": SCREEN})

    return {
        "frame": frame,
        "instances": [{"id": x["id"], "class": x["class"], "score": x["score"], "segmentation": encode(x["mask"])} for x in instances],
        "relations": rel,
        "measurements": out,
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
        path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
