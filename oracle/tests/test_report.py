import json
from pathlib import Path

import jsonschema
import numpy as np

from game_qa.inferlib.infer import from_labels, infer_frame
from game_qa.oracle.report import to_report
from game_qa.oracle.validate import missing_measurements
from test_validate import PARAMS

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def test_label_to_report_end_to_end():
    """라벨 → python_ref 추론 결과 → 판정 리포트"""
    (result,) = from_labels(load("examples/label.json"), {**PARAMS, "fg_search_radius": 2.0})
    report = to_report(result, PARAMS)
    jsonschema.validate(report, load("report.schema.json"))
    assert report["frame"] == {"source": "example_001.png", "index": 0}
    assert report["violations"] == []


def test_label_with_displaced_health_bar():
    """체력바(annotation 3)를 캐릭터에서 멀리 옮기면 R-001"""
    labels = load("examples/label.json")
    bar = next(a for a in labels["annotations"] if a["id"] == 3)
    bar["segmentation"] = [[x + (1000 if k % 2 == 0 else -400) for k, x in enumerate(bar["segmentation"][0])]]
    (result,) = from_labels(labels, {**PARAMS, "fg_search_radius": 2.0})
    assert to_report(result, PARAMS)["violations"] == [{"rule": "R-001", "targets": [3]}]


def test_python_ref_output_has_all_measurements_rules_need():
    """모든 라벨링 클래스가 있는 프레임에서 python_ref 출력에 측정값 누락이 없음"""
    names = [c["name"] for c in load("examples/label.json")["categories"]]
    instances = []
    for k, cls in enumerate(names):
        mask = np.zeros((40, 40), bool)
        mask[2 * k : 2 * k + 2, 2 * k : 2 * k + 2] = True
        instances.append({"id": k + 1, "class": cls, "score": 1.0, "mask": mask})
    frame = {"source": "all.png", "index": 0, "width": 40, "height": 40}
    result = infer_frame(frame, instances + [{**instances[7], "id": 99}, {**instances[8], "id": 98}], {**PARAMS, "fg_search_radius": 2.0})
    assert missing_measurements(result) == []
