import copy
import json
from pathlib import Path

import numpy as np
import pytest
from pycocotools import mask as cocomask

from game_qa.inferlib.infer import from_labels
from game_qa.inferlib.masks import encode
from game_qa.oracle.evaluate import evaluate, main, mappings, match_instances, rle
from game_qa.oracle.report import to_report
from test_validate import PARAMS

ROOT = Path(__file__).resolve().parents[2]


def report(source, *violations):
    return {"frame": {"source": source, "index": 0}, "violations": [{"rule": r, "targets": list(t)} for r, t in violations]}


def test_detection_and_target_agreement():
    truths = [report("a.png", ("R-001", [1]), ("R-002", [3, 4])), report("b.png")]
    reports = [report("a.png", ("R-001", [1]), ("R-002", [3, 5])), report("b.png", ("R-004", [2]))]
    assert evaluate(truths, reports) == {"tp": 2, "fp": 1, "fn": 0, "precision": 2 / 3, "recall": 1.0, "target_agreement": 0.5}


def test_missed_rule_and_unordered_targets():
    truths = [report("a.png", ("R-003", [3, 1, 2]), ("R-008", [5, 6]))]
    reports = [report("a.png", ("R-003", [3, 2, 1]))]
    assert evaluate(truths, reports) == {"tp": 1, "fp": 0, "fn": 1, "precision": 1.0, "recall": 0.5, "target_agreement": 1.0}


def test_frame_without_report_raises():
    with pytest.raises(ValueError):
        evaluate([report("a.png")], [])


def square(x, y, size=10, shape=(40, 40)):
    mask = np.zeros(shape, bool)
    mask[y : y + size, x : x + size] = True
    return {"size": list(shape), "counts": encode(mask)["counts"].encode("ascii")}


def test_match_instances_by_class_and_iou():
    labeled = [{"id": 1, "class": "Character", "rle": square(0, 0)}, {"id": 2, "class": "Character", "rle": square(20, 20)}]
    inferred = [
        {"id": 7, "class": "Character", "rle": square(21, 20)},  # 2와 IoU 0.82
        {"id": 8, "class": "Character", "rle": square(5, 5)},  # 1과 IoU 0.14 (기준 미만)
        {"id": 9, "class": "HealthBar", "rle": square(0, 0)},  # 클래스가 다름
    ]
    assert match_instances(labeled, inferred) == {7: 2}


def test_rle_accepts_label_formats():
    """polygon, 비압축 RLE, 압축 RLE가 같은 마스크"""
    mask = np.zeros((40, 40), bool)
    mask[0:10, 0:10] = True
    polygon = [[0, 0, 10, 0, 10, 10, 0, 10]]
    uncompressed = {"size": [40, 40], "counts": [0] + [10, 30] * 9 + [10, 30 + 1200]}  # 열 우선: 앞 10열마다 1 10개, 0 30개
    for seg in (polygon, uncompressed, encode(mask)):
        assert cocomask.area(rle(seg, 40, 40)) == 100


def test_model_ids_mapped_to_label_ids(tmp_path):
    """라벨로 만든 추론 결과의 id를 바꿔도 마스크로 대응해 같은 평가"""
    labels = json.loads((ROOT / "schemas" / "examples" / "label.json").read_text(encoding="utf-8"))
    bar = next(a for a in labels["annotations"] if a["id"] == 3)
    bar["segmentation"] = [[x + (1000 if k % 2 == 0 else -400) for k, x in enumerate(bar["segmentation"][0])]]
    (result,) = from_labels(labels, {**PARAMS, "fg_search_radius": 2.0})
    truth = to_report(result, PARAMS)
    assert truth["violations"] == [{"rule": "R-001", "targets": [3]}]

    shifted = copy.deepcopy(result)
    for x in shifted["instances"]:
        x["id"] += 100
    model_report = copy.deepcopy(truth)
    model_report["violations"][0]["targets"] = [103]
    ids = mappings(labels, [shifted])
    assert evaluate([truth], [model_report], ids)["target_agreement"] == 1.0
    assert evaluate([truth], [model_report])["target_agreement"] == 0.0

    for name, items in (("truths", [truth]), ("reports", [model_report]), ("results", [shifted])):
        (tmp_path / name).mkdir()
        for k, item in enumerate(items):
            (tmp_path / name / f"{k}.json").write_text(json.dumps(item), encoding="utf-8")
    (tmp_path / "labels.json").write_text(json.dumps(labels), encoding="utf-8")
    main([str(tmp_path / "truths"), str(tmp_path / "reports"), "--labels", str(tmp_path / "labels.json"), "--results", str(tmp_path / "results")])
