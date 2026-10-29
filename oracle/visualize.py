"""판정 결과 시각화: 원본 이미지 위에 인스턴스 마스크와 위반 대상 표시

- 마스크: 라벨링 클래스별 색 (온톨로지 classId 순서로 팔레트 지정)
- 위반 대상: 테두리 상자와 규칙 ID. ScreenBounds 대상은 표시하지 않음

실행: python -m game_qa.oracle.visualize <원본 이미지> <추론 결과.json> <리포트.json> <출력 이미지>
"""

import json
import sys
from functools import cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pycocotools import mask as cocomask

from game_qa.ontology.game_ui import class_ids

PALETTE = [
    (31, 119, 180), (255, 127, 14), (44, 160, 44), (148, 103, 189), (140, 86, 75), (227, 119, 194),
    (127, 127, 127), (188, 189, 34), (23, 190, 207), (174, 199, 232), (255, 187, 120), (152, 223, 138),
]
VIOLATION = (214, 39, 40)
ALPHA = 0.45


@cache
def class_colors():
    return {c: PALETTE[i % len(PALETTE)] for c, i in class_ids().items()}


def decode(segmentation):
    rle = segmentation
    if isinstance(rle["counts"], list):
        rle = cocomask.frPyObjects(rle, *rle["size"])
    elif isinstance(rle["counts"], str):
        rle = {"size": rle["size"], "counts": rle["counts"].encode("ascii")}
    return cocomask.decode(rle).astype(bool)


def render(image, result, report):
    """image: PIL 이미지. 마스크와 위반 대상을 그린 새 RGB 이미지 반환"""
    frame = result["frame"]
    if image.size != (frame["width"], frame["height"]):
        raise ValueError(f"이미지 크기 {image.size}와 추론 결과 크기 {(frame['width'], frame['height'])} 불일치")
    if (report["frame"]["source"], report["frame"]["index"]) != (frame["source"], frame["index"]):
        raise ValueError(f"리포트 프레임 {report['frame']}과 추론 결과 프레임 불일치")

    pixels = np.asarray(image.convert("RGB"), dtype=float)
    masks = {x["id"]: decode(x["segmentation"]) for x in result["instances"]}
    for x in result["instances"]:
        pixels[masks[x["id"]]] = (1 - ALPHA) * pixels[masks[x["id"]]] + ALPHA * np.array(class_colors()[x["class"]])
    out = Image.fromarray(pixels.round().astype(np.uint8))

    rules = {}
    for v in report["violations"]:
        for t in v["targets"]:
            if t != "ScreenBounds":
                rules.setdefault(t, []).append(v["rule"])
    draw = ImageDraw.Draw(out)
    width = max(2, out.height // 300)
    font = ImageFont.load_default(size=max(12, out.height // 40))
    for t, names in rules.items():
        ys, xs = np.nonzero(masks[t])
        box = (int(xs.min()) - width, int(ys.min()) - width, int(xs.max()) + width, int(ys.max()) + width)
        draw.rectangle(box, outline=VIOLATION, width=width)
        text = ", ".join(sorted(set(names)))
        anchor = "lb" if draw.textbbox(box[:2], text, font=font, anchor="lb")[1] >= 0 else "lt"
        draw.rectangle(draw.textbbox(box[:2], text, font=font, anchor=anchor), fill=VIOLATION)
        draw.text(box[:2], text, fill=(255, 255, 255), font=font, anchor=anchor)
    return out


def main(image_path, result_path, report_path, out_path):
    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    render(Image.open(image_path), result, report).save(out_path)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
