import json

import numpy as np
import pytest
from PIL import Image

from report import to_report
from test_report import load, from_labels
from test_validate import PARAMS
from visualize import VIOLATION, class_colors, decode, main, render


def displaced_bar_frame():
    """체력바(annotation 3)를 캐릭터에서 멀리 옮겨 R-001이 나는 프레임"""
    labels = load("examples/label.json")
    bar = next(a for a in labels["annotations"] if a["id"] == 3)
    bar["segmentation"] = [[x + (1000 if k % 2 == 0 else -400) for k, x in enumerate(bar["segmentation"][0])]]
    (result,) = from_labels(labels, {**PARAMS, "fg_search_radius": 2.0})
    return result, to_report(result, PARAMS)


def test_all_labeling_classes_have_distinct_colors():
    names = [c["name"] for c in load("examples/label.json")["categories"]]
    colors = class_colors()
    assert set(names) <= set(colors)
    assert len({colors[n] for n in names}) == len(names)


def test_masks_tinted_and_violation_boxed():
    result, report = displaced_bar_frame()
    assert report["violations"] == [{"rule": "R-001", "targets": [3]}]
    image = Image.new("RGB", (result["frame"]["width"], result["frame"]["height"]))
    out = np.asarray(render(image, result, report))

    for x in result["instances"]:
        mask = decode(x["segmentation"])
        ys, xs = np.nonzero(mask)
        inside = out[ys[len(ys) // 2], xs[len(xs) // 2]]
        assert inside.tolist() != [0, 0, 0]
    bar = next(x for x in result["instances"] if x["id"] == 3)
    ys, xs = np.nonzero(decode(bar["segmentation"]))
    assert out[ys.max() + 2, xs.min() - 2].tolist() == list(VIOLATION)


def test_no_violation_leaves_no_box():
    (result,) = from_labels(load("examples/label.json"), {**PARAMS, "fg_search_radius": 2.0})
    report = to_report(result, PARAMS)
    image = Image.new("RGB", (result["frame"]["width"], result["frame"]["height"]))
    out = np.asarray(render(image, result, report))
    assert not (out == VIOLATION).all(axis=-1).any()


def test_frame_mismatch_rejected():
    result, report = displaced_bar_frame()
    with pytest.raises(ValueError):
        render(Image.new("RGB", (10, 10)), result, report)
    image = Image.new("RGB", (result["frame"]["width"], result["frame"]["height"]))
    with pytest.raises(ValueError):
        render(image, result, {**report, "frame": {"source": "other.png", "index": 0}})


def test_cli_writes_image(tmp_path):
    result, report = displaced_bar_frame()
    Image.new("RGB", (result["frame"]["width"], result["frame"]["height"])).save(tmp_path / "frame.png")
    (tmp_path / "result.json").write_text(json.dumps(result), encoding="utf-8")
    (tmp_path / "report.json").write_text(json.dumps(report), encoding="utf-8")
    main(tmp_path / "frame.png", tmp_path / "result.json", tmp_path / "report.json", tmp_path / "out.png")
    assert Image.open(tmp_path / "out.png").size == (result["frame"]["width"], result["frame"]["height"])
