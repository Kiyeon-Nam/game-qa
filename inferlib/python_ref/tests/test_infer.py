import json
from pathlib import Path

import jsonschema

from infer import from_labels

SCHEMAS = Path(__file__).resolve().parents[3] / "schemas"
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
