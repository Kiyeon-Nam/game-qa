"""학습 → ONNX 동작 확인 (성능 무관). ultralytics가 없으면 건너뜀. 사전학습 가중치를 내려받음"""

from pathlib import Path

import numpy as np
import pytest

from game_qa.training.convert import convert

ultralytics = pytest.importorskip("ultralytics")
from game_qa.training.train import train  # noqa: E402

CONFIGS = Path(__file__).resolve().parents[1] / "configs"
SIZE = 64


def synthetic_labels(folder, n=4):
    """사각형 두 클래스(0, 1)가 있는 이미지 n장"""
    import cv2

    rng = np.random.default_rng(0)
    images, annotations = [], []
    for k in range(n):
        name = f"synthetic_{k}.png"
        canvas = np.zeros((SIZE, SIZE, 3), np.uint8)
        for cls in (0, 1):
            x, y = rng.integers(4, SIZE - 24, 2)
            canvas[y : y + 16, x : x + 16] = (255, 0, 0) if cls == 0 else (0, 255, 0)
            box = [int(x), int(y), int(x) + 16, int(y) + 16]
            annotations.append({
                "id": len(annotations) + 1, "image_id": k, "category_id": cls, "iscrowd": 0, "area": 256,
                "bbox": [box[0], box[1], 16, 16],
                "segmentation": [[box[0], box[1], box[2], box[1], box[2], box[3], box[0], box[3]]],
            })
        cv2.imwrite(str(folder / name), canvas)
        images.append({"id": k, "file_name": name, "width": SIZE, "height": SIZE})
    return {"images": images, "annotations": annotations, "relations": [],
            "categories": [{"id": 0, "name": "A"}, {"id": 1, "name": "B"}]}


@pytest.mark.parametrize("config", ["yolo11n-seg.yaml", "yolo26n-seg.yaml"])
def test_train_and_export_onnx(tmp_path, config):
    data = convert(tmp_path, tmp_path / "dataset", [synthetic_labels(tmp_path)])
    onnx = train(CONFIGS / config, data, tmp_path / "runs", epochs=1, imgsz=SIZE, batch=2, device="cpu", workers=0, plots=False)
    assert onnx.suffix == ".onnx" and onnx.exists()
