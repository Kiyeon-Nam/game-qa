"""엔진 추출 결과(unity/Editor 스크립트 출력 폴더)를 라벨 파일(schemas/label.schema.json)로 조립

- 월드 인스턴스: ID 렌더 픽셀 색 → meta의 인스턴스. meta에 없는 색(혼합된 픽셀)은 배경
- 화면 UI가 가린 월드 픽셀은 제외 (가이드 2-1)
- Terrain: 연결된 덩어리 하나 = 인스턴스, Platform: 조각 하나 = 인스턴스 (가이드 2-2)
- HUDElement·UIPanel: 안쪽 구멍을 채운 전체 영역 (가이드 2-3)
- 가로·세로 4px 미만 조각은 제외 (가이드 2-4). 조각이 모두 빠진 인스턴스와 그 관계는 제외
- 관계: 가이드 6장 표(온톨로지 태깅 관계)의 주체·대상 클래스가 아니면 에러
- 여러 추출 폴더: 이미지는 `<폴더 이름>.png`로 복사, 라벨은 파일 하나로 합침
  - meta.json이 없는 폴더는 그 아래 추출 폴더들 (일괄 추출 출력 루트)
  - 매핑되지 않은 화면 UI(meta의 unmapped)가 있는 폴더는 경고 출력

실행: python -m game_qa.labeling_tool.from_engine <출력 라벨.json> <이미지 폴더> <추출 폴더 ...>
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from pycocotools import mask as cocomask
from scipy import ndimage

from game_qa.ontology.game_ui import class_ids, tagged_relations

SPLIT = ("Terrain", "Platform")
FILLED = ("HUDElement", "UIPanel")
MIN_SIDE = 4


def read_mask(path):
    return np.array(Image.open(path).convert("L")) > 127


def drop_small(mask):
    """가로·세로 MIN_SIDE 미만인 연결 조각 제거"""
    lab, _ = ndimage.label(mask)
    for k, box in enumerate(ndimage.find_objects(lab), start=1):
        if box[0].stop - box[0].start < MIN_SIDE or box[1].stop - box[1].start < MIN_SIDE:
            mask = mask & (lab != k)
    return mask


def compose(folder, file_name=None):
    """추출 폴더 하나 → 이미지 하나짜리 라벨. file_name: 라벨의 이미지 이름 (없으면 meta의 원본 이름)"""
    d = Path(folder)
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    ids = class_ids()
    for x in meta["world"] + meta["ui"]:
        if x["class"] not in ids:
            raise ValueError(f"라벨링 클래스 아님: {x['class']}")

    rgb = np.array(Image.open(d / meta["world_ids"]).convert("RGB")).astype(np.int64)
    packed = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
    world = np.zeros(packed.shape, dtype=np.int64)
    for x in meta["world"]:
        r, g, b = x["color"]
        world[packed == (r << 16) | (g << 8) | b] = x["id"]
    if meta.get("occluder") and (d / meta["occluder"]).exists():
        world[read_mask(d / meta["occluder"])] = 0

    regions = []  # (클래스, 마스크, meta id 또는 None)
    for cls in SPLIT:
        lab, n = ndimage.label(np.isin(world, [x["id"] for x in meta["world"] if x["class"] == cls]))
        regions += [(cls, lab == k, None) for k in range(1, n + 1)]
    regions += [(x["class"], world == x["id"], x["id"]) for x in meta["world"] if x["class"] not in SPLIT]
    for x in meta["ui"]:
        m = read_mask(d / x["mask"])
        regions.append((x["class"], ndimage.binary_fill_holes(m) if x["class"] in FILLED else m, x["id"]))

    annotations, by_meta = [], {}
    for cls, mask, mid in regions:
        mask = drop_small(mask)
        if not mask.any():
            continue
        ys, xs = np.nonzero(mask)
        rle = cocomask.encode(np.asfortranarray(mask.astype(np.uint8)))
        annotations.append({
            "id": len(annotations) + 1, "image_id": 1, "category_id": ids[cls],
            "segmentation": {"size": rle["size"], "counts": rle["counts"].decode("ascii")},
            "bbox": [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
            "area": int(mask.sum()), "iscrowd": 0,
        })
        if mid is not None:
            by_meta[mid] = (annotations[-1]["id"], cls)

    tagged = tagged_relations()
    relations = []
    for r in meta["relations"]:
        if r["subject"] not in by_meta or r["object"] not in by_meta:
            continue
        (s, sc), (o, oc) = by_meta[r["subject"]], by_meta[r["object"]]
        subjects, objects = tagged.get(r["type"], ((), ()))
        if sc not in subjects or oc not in objects:
            raise ValueError(f"가이드 6장에 없는 관계: {sc} -{r['type']}-> {oc}")
        relations.append({"type": r["type"], "subject": s, "object": o})

    return {
        "images": [{"id": 1, "file_name": file_name or meta["image"], "width": meta["width"], "height": meta["height"]}],
        "annotations": annotations,
        "categories": [{"id": i, "name": n} for n, i in sorted(ids.items(), key=lambda kv: kv[1])],
        "relations": relations,
    }


def merge(labels):
    """이미지 하나짜리 라벨들 → 라벨 하나. 이미지·annotation id를 이어서 다시 매김"""
    out = {"images": [], "annotations": [], "categories": labels[0]["categories"] if labels else [], "relations": []}
    for label in labels:
        image_id = len(out["images"]) + 1
        offset = len(out["annotations"])
        out["images"] += [{**img, "id": image_id} for img in label["images"]]
        out["annotations"] += [{**a, "id": a["id"] + offset, "image_id": image_id} for a in label["annotations"]]
        out["relations"] += [{**r, "subject": r["subject"] + offset, "object": r["object"] + offset} for r in label["relations"]]
    return out


def folders(paths):
    """추출 폴더 목록. meta.json이 없는 폴더는 그 아래 추출 폴더들"""
    for p in map(Path, paths):
        if (p / "meta.json").exists():
            yield p
        else:
            yield from sorted(c for c in p.iterdir() if (c / "meta.json").exists())


def main(argv=None):
    parser = argparse.ArgumentParser(description="엔진 추출 결과 → 라벨")
    parser.add_argument("out")
    parser.add_argument("images")
    parser.add_argument("folders", nargs="+")
    args = parser.parse_args(argv)
    images = Path(args.images)
    images.mkdir(parents=True, exist_ok=True)
    labels = []
    for d in folders(args.folders):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        if meta.get("unmapped"):
            print(f"경고: {d.name} 매핑되지 않은 화면 UI {len(meta['unmapped'])}개: {', '.join(meta['unmapped'][:5])}", file=sys.stderr)
        name = f"{d.name}.png"
        shutil.copyfile(d / meta["image"], images / name)
        labels.append(compose(d, name))
    Path(args.out).write_text(json.dumps(merge(labels), ensure_ascii=False), encoding="utf-8")
    print(f"이미지 {len(labels)}, 인스턴스 {sum(len(x['annotations']) for x in labels)}")


if __name__ == "__main__":
    main()
