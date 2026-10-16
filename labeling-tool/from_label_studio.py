"""Label Studio JSON 내보내기를 라벨 파일(schemas/label.schema.json)로 변환

- 프로젝트 설정: `--config` 출력 (온톨로지 라벨링 클래스의 PolygonLabels, 관계)
- 영역: polygonlabels만 사용. 좌표는 이미지 크기 대비 %를 픽셀로 변환
- 관계
  - represents, attachedTo: relations로 변환
  - sameInstance: 이은 영역을 한 인스턴스로 (가이드 2-2 떨어진 조각, 같은 클래스만)
  - 방향: right는 from → to, left는 to → from, bi는 에러
  - 주체·대상 클래스는 가이드 6장 표대로 검사
- 이미지 이름: 업로드 파일은 Label Studio가 붙인 접두어(8자-) 제거, 그 외는 경로의 파일 이름
- 주석이 없는 작업은 제외, 주석이 여러 개인 작업은 에러

실행: python from_label_studio.py <내보낸 JSON> <출력 라벨.json>
프로젝트 설정 출력: python from_label_studio.py --config
"""

import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, urlparse

from pycocotools import mask as cocomask
from rdflib import Graph, Namespace

ONTOLOGY = Path(__file__).resolve().parents[1] / "ontology" / "game_ui.ttl"
GQ = Namespace("https://github.com/Kiyeon-Nam/game-qa/ontology#")
# 가이드 6장 관계 태깅 표: 관계 → (주체 클래스, 대상 클래스)
RELATIONS = {
    "represents": ({"HealthBar"}, {"Character", "LooseObject", "Equipment", "GroundedObject"}),
    "attachedTo": ({"Equipment"}, {"Character"}),
}
SAME = "sameInstance"
UPLOAD_PREFIX = re.compile(r"^[0-9a-f]{8}-")


def class_ids():
    """라벨링 클래스 이름 → classId"""
    g = Graph().parse(ONTOLOGY)
    return {str(c).removeprefix(str(GQ)): int(i) for c, i in g.subject_objects(GQ.classId)}


def config():
    ids = class_ids()
    labels = "".join(f'<Label value="{n}"/>' for n in sorted(ids, key=ids.get))
    relations = "".join(f'<Relation value="{r}"/>' for r in (*RELATIONS, SAME))
    return (
        '<View>\n  <Image name="image" value="$image"/>\n'
        f'  <PolygonLabels name="label" toName="image">{labels}</PolygonLabels>\n'
        f"  <Relations>{relations}</Relations>\n</View>"
    )


def file_name(task):
    if task.get("file_upload"):
        return UPLOAD_PREFIX.sub("", task["file_upload"])
    image = task["data"]["image"]
    local = parse_qs(urlparse(image).query).get("d")
    return PurePosixPath(local[0] if local else urlparse(image).path).name


def link(r):
    """관계 하나를 (관계 이름, 주체 영역 id, 대상 영역 id)로"""
    if len(r.get("labels") or []) != 1:
        raise ValueError(f"관계 이름이 하나가 아님: {r.get('labels')} {r['from_id']} {r['to_id']}")
    return (r["labels"][0], *edge(r))


def edge(r):
    if r["direction"] == "right":
        return r["from_id"], r["to_id"]
    if r["direction"] == "left":
        return r["to_id"], r["from_id"]
    raise ValueError(f"방향이 없는 관계: {r['labels']} {r['from_id']} {r['to_id']}")


def instances(regions, same):
    """sameInstance로 이은 영역 묶기. 영역 id → 대표 영역 id"""
    root = {k: k for k in regions}

    def find(k):
        while root[k] != k:
            k = root[k]
        return k

    for a, b in same:
        root[find(a)] = find(b)
    return {k: find(k) for k in regions}


def convert(tasks):
    ids = class_ids()
    images, annotations, relations = [], [], []
    for image_id, task in enumerate(t for t in tasks if t["annotations"]):
        if len(task["annotations"]) > 1:
            raise ValueError(f"작업 {task['id']}: 주석이 여러 개")
        name = file_name(task)
        result = task["annotations"][0]["result"]
        regions = {r["id"]: r for r in result if r["type"] == "polygonlabels"}
        if not regions:
            continue
        first = next(iter(regions.values()))
        w, h = first["original_width"], first["original_height"]
        images.append({"id": image_id, "file_name": name, "width": w, "height": h})

        links = [link(r) for r in result if r["type"] == "relation"]
        group = instances(regions, [(a, b) for kind, a, b in links if kind == SAME])
        members = {}
        for k, root in group.items():
            members.setdefault(root, []).append(regions[k])
        ann_id = {}
        for root, parts in members.items():
            labels = {p["value"]["polygonlabels"][0] for p in parts}
            if len(labels) != 1 or not labels <= ids.keys():
                raise ValueError(f"{name}: 인스턴스 클래스 오류 {sorted(labels)}")
            polys = [[v for x, y in p["value"]["points"] for v in (x * w / 100, y * h / 100)] for p in parts]
            rle = cocomask.merge(cocomask.frPyObjects(polys, h, w))
            ann_id[root] = len(annotations) + 1
            annotations.append({
                "id": ann_id[root], "image_id": image_id, "category_id": ids[labels.pop()],
                "segmentation": polys, "bbox": [float(v) for v in cocomask.toBbox(rle)],
                "area": float(cocomask.area(rle)), "iscrowd": 0,
            })
        label = {ann_id[root]: parts[0]["value"]["polygonlabels"][0] for root, parts in members.items()}
        for kind, a, b in links:
            if kind in RELATIONS:
                subject, obj = ann_id[group[a]], ann_id[group[b]]
                if label[subject] not in RELATIONS[kind][0] or label[obj] not in RELATIONS[kind][1]:
                    raise ValueError(f"{name}: 가이드 6장에 없는 관계 {label[subject]} -{kind}-> {label[obj]}")
                relations.append({"type": kind, "subject": subject, "object": obj})
            elif kind != SAME:
                raise ValueError(f"{name}: 알 수 없는 관계 {kind}")
    categories = [{"id": i, "name": n} for n, i in sorted(ids.items(), key=lambda x: x[1])]
    return {"images": images, "annotations": annotations, "categories": categories, "relations": relations}


def main(export_path, out_path):
    tasks = json.loads(Path(export_path).read_text(encoding="utf-8"))
    Path(out_path).write_text(json.dumps(convert(tasks), ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1:] == ["--config"]:
        print(config())
    elif len(sys.argv) == 3:
        main(*sys.argv[1:])
    else:
        sys.exit(__doc__)
