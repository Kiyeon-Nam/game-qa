import json
import sys
from pathlib import Path

import jsonschema
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from from_labelme import convert  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def shape(label, points, shape_type="polygon", group_id=None):
    return {"label": label, "points": points, "group_id": group_id, "shape_type": shape_type, "flags": {}, "description": ""}


def labelme(image, shapes, w=100, h=50):
    return {"version": "7.8.1", "flags": {}, "shapes": shapes, "imagePath": image, "imageData": None, "imageHeight": h, "imageWidth": w}


SQUARE = [[10, 10], [20, 10], [20, 20], [10, 20]]


def test_polygon_and_rectangle_converted():
    lm = labelme("..\\frames\\corgi_001.png", [shape("Character", SQUARE), shape("UIPanel", [[0, 0], [40, 10]], "rectangle")])
    out = convert([("corgi_001.json", lm)])
    jsonschema.validate(out, json.loads((ROOT / "schemas" / "label.schema.json").read_text(encoding="utf-8")))
    assert out["images"] == [{"id": 0, "file_name": "corgi_001.png", "width": 100, "height": 50}]
    assert [a["category_id"] for a in out["annotations"]] == [0, 9]
    assert out["annotations"][1]["segmentation"] == [[0, 0, 40, 0, 40, 10, 0, 10]]
    assert out["annotations"][1]["bbox"] == [0, 0, 40, 10] and out["annotations"][1]["area"] == 400
    assert [c["name"] for c in out["categories"]][:2] == ["Character", "LooseObject"] and out["relations"] == []


def test_same_group_merged_into_one_instance():
    far = [[x + 50, y] for x, y in SQUARE]
    lm = labelme("a.png", [shape("Character", SQUARE, group_id=1), shape("Character", far, group_id=1), shape("Character", SQUARE)])
    anns = convert([("a.json", lm)])["annotations"]
    assert [len(a["segmentation"]) for a in anns] == [2, 1]


def test_unknown_label_rejected():
    with pytest.raises(ValueError):
        convert([("a.json", labelme("a.png", [shape("Hero", SQUARE)]))])


def test_unsupported_shape_rejected():
    with pytest.raises(ValueError):
        convert([("a.json", labelme("a.png", [shape("Character", [[1, 1]], "point")]))])


def test_converted_label_feeds_training_converter(tmp_path):
    sys.path.insert(0, str(ROOT / "training"))
    from convert import convert as to_yolo

    out = convert([("a.json", labelme("a.png", [shape("Terrain", SQUARE)]))])
    (tmp_path / "a.png").write_bytes(b"")
    to_yolo(tmp_path, tmp_path / "ds", [out])
    assert (tmp_path / "ds" / "labels" / "train" / "a.txt").read_text(encoding="utf-8").startswith("4 ")
