import json
import sys
from pathlib import Path

import jsonschema

from report import to_report
from test_validate import PARAMS

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inferlib" / "python_ref"))

from infer import from_labels  # noqa: E402


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
