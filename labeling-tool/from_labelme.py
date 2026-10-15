"""LabelMe JSON(이미지별)을 라벨 파일(schemas/label.schema.json) 하나로 변환

- shape: polygon, rectangle만 사용. 그 외 형식은 에러
- 클래스: shape label = 라벨링 클래스 이름. category id는 온톨로지 classId
- 같은 label·group_id의 shape는 한 인스턴스 (가이드 2-2 떨어진 조각). group_id가 없으면 shape 하나 = 인스턴스 하나
- relations: 빈 목록
- bbox, area: 폴리곤으로 계산

실행: python from_labelme.py <LabelMe JSON 폴더> <출력 라벨.json>
클래스 목록(LabelMe --labels용): python from_labelme.py --labels
"""

import json
import sys
from pathlib import Path, PureWindowsPath

from pycocotools import mask as cocomask
from rdflib import Graph, Namespace

ONTOLOGY = Path(__file__).resolve().parents[1] / "ontology" / "game_ui.ttl"
GQ = Namespace("https://github.com/Kiyeon-Nam/game-qa/ontology#")


def class_ids():
    """라벨링 클래스 이름 → classId"""
    g = Graph().parse(ONTOLOGY)
    return {str(c).removeprefix(str(GQ)): int(i) for c, i in g.subject_objects(GQ.classId)}


def polygon(shape):
    points = shape["points"]
    if shape["shape_type"] == "rectangle":
        (x0, y0), (x1, y1) = points
        points = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    elif shape["shape_type"] != "polygon":
        raise ValueError(f"지원하지 않는 shape 형식: {shape['shape_type']} ({shape['label']})")
    return [float(v) for p in points for v in p]


def convert(files):
    """files: (파일 이름, LabelMe JSON dict) 목록. 라벨 dict 반환"""
    ids = class_ids()
    images, annotations = [], []
    for image_id, (name, lm) in enumerate(sorted(files, key=lambda f: f[0])):
        h, w = lm["imageHeight"], lm["imageWidth"]
        images.append({"id": image_id, "file_name": PureWindowsPath(lm["imagePath"]).name, "width": w, "height": h})
        groups = {}
        for k, shape in enumerate(lm["shapes"]):
            if shape["label"] not in ids:
                raise ValueError(f"{name}: 라벨링 클래스가 아닌 label {shape['label']}")
            key = (shape["label"], shape["group_id"]) if shape.get("group_id") is not None else (shape["label"], "shape", k)
            groups.setdefault(key, []).append(polygon(shape))
        for (label, *_), polys in groups.items():
            rle = cocomask.merge(cocomask.frPyObjects(polys, h, w))
            annotations.append({
                "id": len(annotations) + 1, "image_id": image_id, "category_id": ids[label],
                "segmentation": polys, "bbox": [float(v) for v in cocomask.toBbox(rle)],
                "area": float(cocomask.area(rle)), "iscrowd": 0,
            })
    categories = [{"id": i, "name": n} for n, i in sorted(ids.items(), key=lambda x: x[1])]
    return {"images": images, "annotations": annotations, "categories": categories, "relations": []}


def main(folder, out_path):
    files = [(p.name, json.loads(p.read_text(encoding="utf-8"))) for p in sorted(Path(folder).glob("*.json"))]
    Path(out_path).write_text(json.dumps(convert(files), ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1:] == ["--labels"]:
        ids = class_ids()
        print(",".join(sorted(ids, key=ids.get)))
    elif len(sys.argv) == 3:
        main(*sys.argv[1:])
    else:
        sys.exit(__doc__)
