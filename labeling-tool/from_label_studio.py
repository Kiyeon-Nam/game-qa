"""Label Studio JSON 내보내기를 라벨 파일(schemas/label.schema.json)로 변환

- 프로젝트 설정: `--config` 출력 (온톨로지 라벨링 클래스의 PolygonLabels, 관계)
- 영역: polygonlabels만 사용. 좌표는 이미지 크기 대비 %를 픽셀로 변환
- 관계
  - represents, attachedTo: relations로 변환
  - sameInstance: 이은 영역을 한 인스턴스로 (가이드 2-2 떨어진 조각, 같은 클래스끼리)
  - 종류: 온톨로지 태깅 관계(가이드 6장)의 주체·대상 클래스로 하나로 정해짐. 관계 이름을 고르지 않으면 이것으로 정하고, 고르면 맞는지 검사
  - 방향: right는 from → to, left는 to → from, bi는 에러
- 이미지 이름: 업로드 파일은 Label Studio가 붙인 접두어(8자-) 제거, 그 외는 경로의 파일 이름
- 주석이 없는 작업은 제외, 주석이 여러 개인 작업은 에러

실행: python -m game_qa.labeling_tool.from_label_studio <내보낸 JSON> <출력 라벨.json>
프로젝트 설정 출력: python -m game_qa.labeling_tool.from_label_studio --config
"""

import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, urlparse

from pycocotools import mask as cocomask

from game_qa.ontology.game_ui import class_ids, tagged_relations

SAME = "sameInstance"
UPLOAD_PREFIX = re.compile(r"^[0-9a-f]{8}-")


def config():
    ids = class_ids()
    labels = "".join(f'<Label value="{n}"/>' for n in sorted(ids, key=ids.get))
    relations = "".join(f'<Relation value="{r}"/>' for r in (*tagged_relations(), SAME))
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


def link(r, label):
    """관계 하나를 (관계 종류, 주체 영역 id, 대상 영역 id)로. label: 영역 id → 클래스"""
    a, b = edge(r)
    kinds = [k for k, (subjects, objects) in tagged_relations().items() if label[a] in subjects and label[b] in objects]
    kinds += [SAME] if label[a] == label[b] else []
    named = r.get("labels") or []
    if len(kinds) != 1 or len(named) > 1 or (named and named[0] not in kinds):
        raise ValueError(f"가이드 6장에 없는 관계: {label[a]} -{named}-> {label[b]}")
    return kinds[0], a, b


def edge(r):
    if r["direction"] == "right":
        return r["from_id"], r["to_id"]
    if r["direction"] == "left":
        return r["to_id"], r["from_id"]
    raise ValueError(f"방향이 없는 관계: {r['from_id']} {r['to_id']}")


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

        label = {k: r["value"]["polygonlabels"][0] for k, r in regions.items()}
        links = [link(r, label) for r in result if r["type"] == "relation"]
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
        for kind, a, b in links:
            if kind != SAME:
                relations.append({"type": kind, "subject": ann_id[group[a]], "object": ann_id[group[b]]})
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
