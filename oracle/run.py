"""판정 파이프라인 전체 실행: 영상·이미지 → 프레임 추출 → 세그멘테이션 → 판정 리포트 → 시각화

- 출력 폴더
  - frames/: 프레임 이미지, frames.json
  - results/: 추론 결과
  - reports/: 판정 리포트
  - images/: 시각화 이미지
- 파라미터 파일: 추론(inferlib/python_ref)과 규칙이 읽는 값을 함께 담은 JSON. 빠진 값은 실행 전에 에러
- 입력 파일 이름(확장자 제외)은 겹치지 않아야 함 (출력 파일 이름)
- 세그멘테이션 실행에 학습 환경 필요 (training/README.md)

실행: python -m game_qa.oracle.run <모델.onnx> <파라미터.json> <출력 폴더> <영상·이미지 ...> [--step 1] [--score 0.25]
"""

import argparse
import json
from pathlib import Path

from PIL import Image
from game_qa.inferlib import segment
from game_qa.inferlib.infer import PARAMS
from game_qa.oracle import frames
from game_qa.oracle.report import to_report
from game_qa.oracle.validate import required_params
from game_qa.oracle.visualize import render


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def run(model_path, params, out_dir, paths, step=1, score=0.25):
    """프레임별 판정 리포트 목록 반환"""
    missing = (set(PARAMS) | required_params()) - params.keys()
    if missing:
        raise ValueError(f"파라미터 누락: {', '.join(sorted(missing))}")
    stems = [Path(p).stem for p in paths]
    if len(set(stems)) != len(stems):
        raise ValueError(f"입력 파일 이름 중복: {stems}")
    model = segment.load(model_path)
    out = Path(out_dir)
    manifest = frames.extract(out / "frames", paths, step)
    for name in ("results", "reports", "images"):
        (out / name).mkdir(parents=True, exist_ok=True)
    reports = []
    for image, source, index in frames.load(manifest):
        result = segment.segment(model, image, params, score, source, index)
        report = to_report(result, params)
        write(out / "results" / f"{image.stem}.json", result)
        write(out / "reports" / f"{image.stem}.json", report)
        with Image.open(image) as frame:
            render(frame, result, report).save(out / "images" / f"{image.stem}.png")
        reports.append(report)
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model")
    parser.add_argument("params")
    parser.add_argument("out_dir")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--score", type=float, default=0.25)
    args = parser.parse_args()
    params = json.loads(Path(args.params).read_text(encoding="utf-8"))
    for report in run(args.model, params, args.out_dir, args.paths, args.step, args.score):
        print(report["frame"]["source"], report["frame"]["index"], [v["rule"] for v in report["violations"]])


if __name__ == "__main__":
    main()
