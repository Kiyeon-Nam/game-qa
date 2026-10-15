import json
from pathlib import Path

import numpy as np
import pytest
import yaml
from pycocotools import mask as cocomask

from convert import convert, merge, polygons, split

ROOT = Path(__file__).resolve().parents[2]


def example_labels():
    return json.loads((ROOT / "schemas" / "examples" / "label.json").read_text(encoding="utf-8"))


def touch_images(folder, labels):
    for img in labels["images"]:
        (folder / img["file_name"]).write_bytes(b"")


def read_lines(path):
    return [line.split() for line in path.read_text(encoding="utf-8").splitlines()]


def test_example_label_converted(tmp_path):
    labels = example_labels()
    touch_images(tmp_path, labels)
    data = yaml.safe_load(convert(tmp_path, tmp_path / "out", [labels]).read_text(encoding="utf-8"))
    assert data["names"] == {c["id"]: c["name"] for c in labels["categories"]}

    lines = read_lines(tmp_path / "out" / "labels" / "train" / "example_001.txt")
    assert [int(line[0]) for line in lines] == [a["category_id"] for a in labels["annotations"]]
    img = labels["images"][0]
    first = labels["annotations"][0]["segmentation"][0]
    expected = np.asarray(first, float).reshape(-1, 2) / [img["width"], img["height"]]
    assert np.allclose(np.asarray(lines[0][1:], float).reshape(-1, 2), expected, atol=1e-6)


def test_rle_becomes_outline():
    mask = np.zeros((20, 30), np.uint8)
    mask[5:10, 4:12] = 1
    rle = cocomask.encode(np.asfortranarray(mask))
    rle["counts"] = rle["counts"].decode("ascii")
    (poly,) = polygons(rle, 20, 30)
    assert poly[:, 0].min() == 4 and poly[:, 0].max() == 11
    assert poly[:, 1].min() == 5 and poly[:, 1].max() == 9


def test_merge_keeps_all_vertices_in_one_polygon():
    a = np.array([[0, 0], [2, 0], [2, 2], [0, 2]], float)
    b = a + 10
    merged = merge([a, b])
    assert {tuple(p) for p in merged} == {tuple(p) for p in np.concatenate([a, b])}
    assert len(merged) == len(a) + len(b) + 2


def test_split_is_deterministic_and_disjoint():
    names = [f"img_{k:02}.png" for k in range(10)]
    train, val = split(names, 0.2, seed=0)
    assert (train, val) == split(list(reversed(names)), 0.2, seed=0)
    assert train.isdisjoint(val) and train | val == set(names) and len(val) == 2


def test_single_image_used_for_both():
    assert split(["a.png"], 0.2, 0) == ({"a.png"}, {"a.png"})


def test_mismatched_categories_rejected(tmp_path):
    a, b = example_labels(), example_labels()
    b["images"][0]["file_name"] = "other.png"
    b["categories"][0]["name"] = "Hero"
    with pytest.raises(ValueError):
        convert(tmp_path, tmp_path / "out", [a, b])
