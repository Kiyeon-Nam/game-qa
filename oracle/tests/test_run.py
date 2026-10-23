import json

import pytest
from PIL import Image

from game_qa.oracle import run
from test_report import from_labels, load
from test_validate import PARAMS

FULL = {**PARAMS, "fg_search_radius": 2.0}
SIZE = 64


def box(x0, y0, x1, y1):
    return [[x0, y0, x1, y0, x1, y1, x0, y1]]


def far_bar_labels():
    """64×64 화면. 캐릭터에서 멀리 떨어진 체력바 (R-001)"""
    labels = load("examples/label.json")
    shapes = [(0, box(8, 40, 16, 56)), (7, box(48, 4, 60, 7))]
    labels["images"] = [{"id": 1, "file_name": "shot.png", "width": SIZE, "height": SIZE}]
    labels["annotations"] = [
        {"id": k + 1, "image_id": 1, "category_id": c, "segmentation": s, "bbox": [0, 0, 1, 1], "area": 1, "iscrowd": 0}
        for k, (c, s) in enumerate(shapes)
    ]
    labels["relations"] = []
    return labels


@pytest.fixture
def fake_model(monkeypatch):
    """모델 대신 라벨 마스크로 추론 결과를 만듦 (ultralytics 없이 연결만 확인). 불러온 모델 경로 기록"""
    loaded = []

    def fake_segment(model, image, params, score, source, index):
        (result,) = from_labels(far_bar_labels(), params)
        result["frame"].update(source=source, index=index)
        return result

    monkeypatch.setattr(run.segment, "load", loaded.append)
    monkeypatch.setattr(run.segment, "segment", fake_segment)
    return loaded


def test_image_to_report_and_visualization(tmp_path, fake_model):
    Image.new("RGB", (SIZE, SIZE)).save(tmp_path / "shot.png")
    reports = run.run("model.onnx", FULL, tmp_path / "out", [tmp_path / "shot.png"])

    assert reports == [{"frame": {"source": "shot.png", "index": 0}, "violations": [{"rule": "R-001", "targets": [2]}]}]
    out = tmp_path / "out"
    assert json.loads((out / "reports" / "shot.json").read_text(encoding="utf-8")) == reports[0]
    assert json.loads((out / "results" / "shot.json").read_text(encoding="utf-8"))["frame"]["source"] == "shot.png"
    assert Image.open(out / "images" / "shot.png").size == (SIZE, SIZE)
    assert (out / "frames" / "frames.json").exists()


@pytest.mark.parametrize("dropped", ["fg_search_radius", "attach_distance"])
def test_missing_param_rejected_before_running(tmp_path, fake_model, dropped):
    """추론·규칙 파라미터 모두 모델을 열기 전에 검사"""
    params = {k: v for k, v in FULL.items() if k != dropped}
    with pytest.raises(ValueError):
        run.run("model.onnx", params, tmp_path / "out", [tmp_path / "shot.png"])
    assert fake_model == [] and not (tmp_path / "out").exists()


def test_duplicate_input_names_rejected(tmp_path, fake_model):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    with pytest.raises(ValueError):
        run.run("model.onnx", FULL, tmp_path / "out", [tmp_path / "a" / "shot.png", tmp_path / "b" / "shot.png"])
    assert not (tmp_path / "out").exists()
