import copy
import json
import sys
from pathlib import Path

import jsonschema
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from from_label_studio import config, convert  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXPORT = json.loads((Path(__file__).parent / "label_studio_export.json").read_text(encoding="utf-8"))


def tasks():
    """Label Studio 1.23.2에서 내보낸 작업 (필요한 필드만)"""
    return copy.deepcopy(EXPORT)


def result(ts):
    return ts[0]["annotations"][0]["result"]


def test_real_export_converted():
    out = convert(tasks())
    jsonschema.validate(out, json.loads((ROOT / "schemas" / "label.schema.json").read_text(encoding="utf-8")))
    assert out["images"] == [{"id": 0, "file_name": "corgi_001.png", "width": 200, "height": 100}]
    assert [(a["category_id"], len(a["segmentation"])) for a in out["annotations"]] == [(0, 2), (2, 1), (7, 1), (9, 1), (10, 1)]
    assert out["annotations"][1]["segmentation"] == [[40, 40, 55, 40, 55, 45, 40, 45]]
    assert out["relations"] == [{"type": "represents", "subject": 3, "object": 1}, {"type": "attachedTo", "subject": 2, "object": 1}]


def test_bidirectional_relation_rejected():
    ts = tasks()
    next(r for r in result(ts) if r["type"] == "relation")["direction"] = "bi"
    with pytest.raises(ValueError):
        convert(ts)


def test_relation_without_name_rejected():
    ts = tasks()
    next(r for r in result(ts) if r["type"] == "relation")["labels"] = []
    with pytest.raises(ValueError):
        convert(ts)


def test_same_instance_across_classes_rejected():
    ts = tasks()
    same = next(r for r in result(ts) if r.get("labels") == ["sameInstance"])
    same["from_id"] = next(r["id"] for r in result(ts) if r.get("value", {}).get("polygonlabels") == ["Equipment"])
    with pytest.raises(ValueError):
        convert(ts)


def test_multiple_annotations_rejected():
    ts = tasks()
    ts[0]["annotations"].append(ts[0]["annotations"][0])
    with pytest.raises(ValueError):
        convert(ts)


def test_unannotated_task_skipped_and_local_file_name():
    ts = tasks()
    ts.append({"id": 99, "data": {"image": "/data/upload/2/x.png"}, "file_upload": "x.png", "annotations": []})
    ts[0]["file_upload"] = None
    ts[0]["data"]["image"] = "/data/local-files/?d=frames%2Fcorgi_002.png"
    assert [i["file_name"] for i in convert(ts)["images"]] == ["corgi_002.png"]


def test_config_lists_all_labeling_classes():
    names = [c["name"] for c in json.loads((ROOT / "schemas" / "examples" / "label.json").read_text(encoding="utf-8"))["categories"]]
    xml = config()
    assert all(f'<Label value="{n}"/>' in xml for n in names)
    assert '<Relation value="represents"/>' in xml and '<Relation value="sameInstance"/>' in xml


def test_converted_label_feeds_training_converter(tmp_path):
    sys.path.insert(0, str(ROOT / "training"))
    from convert import convert as to_yolo

    (tmp_path / "corgi_001.png").write_bytes(b"")
    to_yolo(tmp_path, tmp_path / "ds", [convert(tasks())])
    lines = (tmp_path / "ds" / "labels" / "train" / "corgi_001.txt").read_text(encoding="utf-8").splitlines()
    assert [line.split()[0] for line in lines] == ["0", "2", "7", "9", "10"]


def test_reversed_relation_rejected():
    """attachedTo를 Character → Equipment로 그으면 에러"""
    ts = tasks()
    attached = next(r for r in result(ts) if r.get("labels") == ["attachedTo"])
    attached["direction"] = "left"
    with pytest.raises(ValueError):
        convert(ts)
