import json
from pathlib import Path

import jsonschema
import numpy as np
import pytest
from PIL import Image
from pycocotools import mask as cocomask

from game_qa.labeling_tool.from_engine import compose, main

ROOT = Path(__file__).resolve().parents[2]
H, W = 40, 60


def color(i):
    return [i, 0, i * 97 % 251 + 1]


def write(folder, world, ui=(), relations=(), occluder=None):
    """world: (id, class, 마스크 목록) 목록. ui: (id, class, 마스크) 목록"""
    rgb = np.zeros((H, W, 3), np.uint8)
    entries = []
    for i, cls, masks in world:
        for m in masks:
            rgb[m] = color(i)
        entries.append({"id": i, "color": color(i), "class": cls, "engine": f"e{i}"})
    Image.fromarray(rgb).save(folder / "ids.png")
    Image.fromarray(np.zeros((H, W, 3), np.uint8)).save(folder / "frame.png")
    ui_entries = []
    for i, cls, m in ui:
        Image.fromarray(m.astype(np.uint8) * 255).save(folder / f"ui_{i}.png")
        ui_entries.append({"id": i, "mask": f"ui_{i}.png", "class": cls, "engine": f"u{i}"})
    meta = {"image": "frame.png", "world_ids": "ids.png", "occluder": "", "width": W, "height": H,
            "world": entries, "ui": ui_entries, "relations": [dict(zip(("type", "subject", "object"), r)) for r in relations]}
    if occluder is not None:
        Image.fromarray(occluder.astype(np.uint8) * 255).save(folder / "occ.png")
        meta["occluder"] = "occ.png"
    (folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return folder


def box(x0, y0, x1, y1):
    m = np.zeros((H, W), bool)
    m[y0:y1, x0:x1] = True
    return m


def decode(a):
    return cocomask.decode({"size": a["segmentation"]["size"], "counts": a["segmentation"]["counts"].encode()}).astype(bool)


def names(label):
    by_id = {c["id"]: c["name"] for c in label["categories"]}
    return [by_id[a["category_id"]] for a in label["annotations"]]


def test_schema_and_relations(tmp_path):
    out = compose(write(tmp_path, [(1, "Character", [box(10, 10, 20, 30)]), (2, "Equipment", [box(20, 20, 30, 25)]),
                                   (3, "HealthBar", [box(10, 5, 20, 9)])],
                        relations=[("attachedTo", 2, 1), ("represents", 3, 1)]))
    jsonschema.validate(out, json.loads((ROOT / "schemas" / "label.schema.json").read_text(encoding="utf-8")))
    assert names(out) == ["Character", "Equipment", "HealthBar"]
    assert out["relations"] == [{"type": "attachedTo", "subject": 2, "object": 1}, {"type": "represents", "subject": 3, "object": 1}]


def test_terrain_split_by_connected_region(tmp_path):
    """가이드 2-2: 엔진 오브젝트가 달라도 이어진 지형은 하나, 떨어진 지형은 별도"""
    out = compose(write(tmp_path, [(1, "Terrain", [box(0, 30, 20, 40)]), (2, "Terrain", [box(20, 30, 30, 40), box(40, 30, 60, 40)])]))
    assert sorted(a["area"] for a in out["annotations"]) == [200, 300]


def test_mixed_pixels_ignored(tmp_path):
    """meta에 없는 색(가장자리 혼합)은 배경. R·G가 다른 인스턴스 id와 같아도 검사 채널이 달라 배경"""
    folder = write(tmp_path, [(10, "Character", [box(10, 10, 20, 20)]), (5, "Character", [box(40, 10, 50, 20)])])
    rgb = np.array(Image.open(folder / "ids.png"))
    rgb[10:20, 6:10] = (np.array(color(10)) + 1) // 2  # id 10과 배경의 혼합 → R·G가 id 5. 4px 제외에 걸리지 않는 폭
    Image.fromarray(rgb).save(folder / "ids.png")
    assert [a["area"] for a in compose(folder)["annotations"]] == [100, 100]


def test_small_fragments_dropped(tmp_path):
    """가이드 2-4: 4px 미만 조각만 제외, 같은 인스턴스의 큰 조각은 유지. 다 빠지면 관계도 제외"""
    out = compose(write(tmp_path, [(1, "Character", [box(10, 10, 20, 20), box(40, 10, 41, 30)]), (2, "HealthBar", [box(30, 5, 50, 7)])],
                        relations=[("represents", 2, 1)]))
    assert names(out) == ["Character"]
    assert out["annotations"][0]["area"] == 100
    assert out["relations"] == []


def test_ui_occludes_world_and_outer_ui_filled(tmp_path):
    """가이드 2-1: UI가 가린 월드 픽셀 제외. 2-3: 바깥 UI는 구멍을 채운 전체 영역, 글자는 그대로"""
    ring = box(0, 0, 20, 20) & ~box(4, 4, 16, 16)
    text = box(6, 6, 14, 14) & ~box(9, 9, 11, 11)
    out = compose(write(tmp_path, [(1, "Terrain", [box(0, 0, 60, 40)])], ui=[(2, "HUDElement", ring), (3, "TextLabel", text)],
                        occluder=ring | text))
    by = {}
    for n, a in zip(names(out), out["annotations"]):
        by.setdefault(n, []).append(a)
    # 테두리 안쪽으로 보이는 지형은 바깥 지형과 끊겨 별도 덩어리. 글자 구멍(2×2)으로 보이는 지형은 4px 미만이라 제외
    assert len(by["Terrain"]) == 2
    assert sum(a["area"] for a in by["Terrain"]) == H * W - ring.sum() - text.sum() - 4
    assert [a["area"] for a in by["HUDElement"]] == [400]
    assert (decode(by["TextLabel"][0]) == text).all()


def test_relation_outside_guide_rejected(tmp_path):
    folder = write(tmp_path, [(1, "Character", [box(10, 10, 20, 20)]), (2, "LooseObject", [box(30, 10, 40, 20)])],
                   relations=[("attachedTo", 2, 1)])
    with pytest.raises(ValueError):
        compose(folder)


def test_unknown_class_rejected(tmp_path):
    with pytest.raises(ValueError):
        compose(write(tmp_path, [(1, "Spike", [box(10, 10, 20, 20)])]))


def test_batch_folders_merged(tmp_path, capsys):
    """일괄 추출 루트 → 이미지 폴더 이름으로 복사, 이미지·annotation id 이어서, 관계도 따라 이동. 매핑 누락은 경고"""
    root = tmp_path / "batch"
    a, b = root / "corgi_A_00", root / "corgi_B_00"
    a.mkdir(parents=True)
    b.mkdir()
    write(a, [(1, "Character", [box(10, 10, 20, 20)])])
    write(b, [(1, "Character", [box(10, 10, 20, 30)]), (2, "Equipment", [box(20, 20, 30, 25)])], relations=[("attachedTo", 2, 1)])
    meta = json.loads((b / "meta.json").read_text(encoding="utf-8"))
    meta["unmapped"] = ["Canvas/Logo"]
    (b / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    out, images = tmp_path / "label.json", tmp_path / "images"
    main([str(out), str(images), str(root)])
    label = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(label, json.loads((ROOT / "schemas" / "label.schema.json").read_text(encoding="utf-8")))
    assert [(i["id"], i["file_name"]) for i in label["images"]] == [(1, "corgi_A_00.png"), (2, "corgi_B_00.png")]
    assert sorted(p.name for p in images.iterdir()) == ["corgi_A_00.png", "corgi_B_00.png"]
    assert [(x["id"], x["image_id"]) for x in label["annotations"]] == [(1, 1), (2, 2), (3, 2)]
    assert label["relations"] == [{"type": "attachedTo", "subject": 3, "object": 2}]
    assert "corgi_B_00" in capsys.readouterr().err
