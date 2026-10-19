import json
from pathlib import Path

import pytest
from PIL import Image

import run
from test_report import from_labels, load
from test_validate import PARAMS

FULL = {**PARAMS, "fg_search_radius": 2.0}


def displaced_bar_labels():
    """체력바(annotation 3)를 캐릭터에서 멀리 옮겨 R-001이 나는 라벨"""
    labels = load("examples/label.json")
    bar = next(a for a in labels["annotations"] if a["id"] == 3)
    bar["segmentation"] = [[x + (1000 if k % 2 == 0 else -400) for k, x in enumerate(bar["segmentation"][0])]]
    return labels


@pytest.fixture
def fake_model(monkeypatch):
    """모델 대신 라벨 마스크로 추론 결과를 만듦 (ultralytics 없이 연결만 확인)"""
    labels = displaced_bar_labels()

    def fake_segment(model, image, params, score, source, index):
        (result,) = from_labels(labels, params)
        result["frame"].update(source=source, index=index)
        return result

    monkeypatch.setattr(run.segment, "load", lambda path: None)
    monkeypatch.setattr(run.segment, "segment", fake_segment)


def test_image_to_report_and_visualization(tmp_path, fake_model):
    Image.new("RGB", (1920, 1080)).save(tmp_path / "shot.png")
    reports = run.run("model.onnx", FULL, tmp_path / "out", [tmp_path / "shot.png"])

    assert reports == [{"frame": {"source": "shot.png", "index": 0}, "violations": [{"rule": "R-001", "targets": [3]}]}]
    out = tmp_path / "out"
    assert json.loads((out / "reports" / "shot.json").read_text(encoding="utf-8")) == reports[0]
    assert json.loads((out / "results" / "shot.json").read_text(encoding="utf-8"))["frame"]["source"] == "shot.png"
    assert Image.open(out / "images" / "shot.png").size == (1920, 1080)
    assert (out / "frames" / "frames.json").exists()


def test_missing_inference_param_rejected(tmp_path, fake_model):
    params = {k: v for k, v in FULL.items() if k != "fg_search_radius"}
    with pytest.raises(ValueError):
        run.run("model.onnx", params, tmp_path / "out", [tmp_path / "shot.png"])
