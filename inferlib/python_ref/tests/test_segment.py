import json
import sys
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import numpy as np
import pytest

from segment import instances, segment

ROOT = Path(__file__).resolve().parents[3]
PARAMS = {"search_radius": 2.0, "fg_search_radius": 2.0, "support_gap_max": 0.1}


class Tensor:
    """Ultralytics 결과의 torch 텐서 대역"""

    def __init__(self, value):
        self.value = np.asarray(value)

    def cpu(self):
        return self

    def numpy(self):
        return self.value

    def int(self):
        return Tensor(self.value.astype(int))

    def tolist(self):
        return self.value.tolist()


def fake_result(masks, classes, scores):
    names = {0: "Character", 4: "Terrain"}
    return SimpleNamespace(
        names=names,
        masks=None if masks is None else SimpleNamespace(data=Tensor(masks)),
        boxes=SimpleNamespace(cls=Tensor(classes), conf=Tensor(scores)),
    )


def test_result_converted_to_instances():
    masks = np.zeros((2, 8, 8), np.float32)
    masks[0, 1:3, 1:3] = 0.9
    masks[1, 5:, :] = 0.7
    xs = instances(fake_result(masks, [0.0, 4.0], [0.91234, 0.5]))
    assert [(x["id"], x["class"], x["score"]) for x in xs] == [(1, "Character", 0.9123), (2, "Terrain", 0.5)]
    assert xs[0]["mask"].dtype == bool and xs[0]["mask"].sum() == 4


def test_no_detection_gives_no_instances():
    assert instances(fake_result(None, [], [])) == []


class FakeModel:
    def predict(self, image, **kwargs):
        masks = np.zeros((1, 8, 8), np.float32)
        masks[0, 2:5, 2:5] = 0.9
        return [SimpleNamespace(orig_shape=(8, 8), **vars(fake_result(masks, [0.0], [0.8])))]


def test_frame_defaults_to_image_name():
    result = segment(FakeModel(), Path("shots/a.png"), PARAMS)
    assert result["frame"] == {"source": "a.png", "index": 0, "width": 8, "height": 8}


def test_frame_keeps_given_source_index():
    result = segment(FakeModel(), Path("frames/play_000003.png"), PARAMS, source="play.avi", index=3)
    assert (result["frame"]["source"], result["frame"]["index"]) == ("play.avi", 3)


@pytest.mark.parametrize("config", ["yolo11n-seg.yaml", "yolo26n-seg.yaml"])
def test_image_to_report(tmp_path, config):
    """학습한 ONNX로 이미지 → 추론 결과 → 판정 리포트 (성능 무관). 사전학습 가중치를 내려받음"""
    pytest.importorskip("ultralytics")
    pytest.importorskip("pyshacl")
    import cv2

    sys.path[:0] = [str(ROOT / "training"), str(ROOT / "oracle"), str(ROOT / "oracle" / "tests")]
    from convert import convert
    from train import train
    from report import to_report
    from segment import load, segment
    from test_validate import PARAMS

    labels = json.loads((ROOT / "schemas" / "examples" / "label.json").read_text(encoding="utf-8"))
    images, annotations = [], []
    for k in range(4):
        canvas = np.zeros((64, 64, 3), np.uint8)
        canvas[48:, :] = (90, 60, 30)
        x = 8 + 10 * k
        canvas[32:48, x : x + 8] = (40, 40, 220)
        cv2.imwrite(str(tmp_path / f"s{k}.png"), canvas)
        images.append({"id": k, "file_name": f"s{k}.png", "width": 64, "height": 64})
        for cls, (x0, y0, x1, y1) in ((0, (x, 32, x + 8, 48)), (4, (0, 48, 64, 64))):
            annotations.append({"id": len(annotations) + 1, "image_id": k, "category_id": cls, "iscrowd": 0,
                                "bbox": [x0, y0, x1 - x0, y1 - y0], "area": (x1 - x0) * (y1 - y0),
                                "segmentation": [[x0, y0, x1, y0, x1, y1, x0, y1]]})
    labels = {**labels, "images": images, "annotations": annotations, "relations": []}

    data = convert(tmp_path, tmp_path / "dataset", [labels])
    onnx = train(ROOT / "training" / "configs" / config, data, tmp_path / "runs",
                 epochs=1, imgsz=64, batch=2, device="cpu", workers=0, plots=False, verbose=False)
    result = segment(load(onnx), tmp_path / "s0.png", {**PARAMS, "fg_search_radius": 2.0}, score=0.001)

    jsonschema.validate(result, json.loads((ROOT / "schemas" / "inference.schema.json").read_text(encoding="utf-8")))
    assert result["frame"] == {"source": "s0.png", "index": 0, "width": 64, "height": 64}
    assert result["instances"]
    jsonschema.validate(to_report(result, PARAMS), json.loads((ROOT / "schemas" / "report.schema.json").read_text(encoding="utf-8")))
