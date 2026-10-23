import json
from pathlib import Path

import jsonschema
import numpy as np
import pytest

from game_qa.inferlib.infer import from_labels, infer_frame
from game_qa.inferlib.masks import decode

SCHEMAS = Path(__file__).resolve().parents[3] / "schemas"
# fg_search_radius는 임계값 목록에서 미정. 임의 값
PARAMS = {"search_radius": 2.0, "fg_search_radius": 2.0, "support_gap_max": 0.1}


def load(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_label_example_produces_valid_inference_result():
    results = list(from_labels(load("examples/label.json"), PARAMS))
    assert len(results) == 1
    jsonschema.validate(results[0], load("inference.schema.json"))
    rel = {(x["type"], x["subject"], x["object"]) for x in results[0]["relations"]}
    assert ("represents", 3, 1) in rel
    assert ("attachedTo", 2, 1) in rel


def test_empty_mask_instance_is_dropped():
    frame = {"source": "x.png", "index": 0, "width": 4, "height": 4}
    empty = {"id": 1, "class": "HUDElement", "score": 0.5, "mask": np.zeros((4, 4), bool)}
    full = {"id": 2, "class": "HUDElement", "score": 0.5, "mask": np.ones((4, 4), bool)}
    result = infer_frame(frame, [empty, full], PARAMS)
    assert [x["id"] for x in result["instances"]] == [2]
    assert result["measurements"] == []


def test_rle_size_mismatch_raises():
    with pytest.raises(ValueError):
        decode({"size": [2, 2], "counts": [4]}, 4, 4)
