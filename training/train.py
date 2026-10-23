"""세그멘테이션 모델 학습과 ONNX 내보내기

- 설정 파일: Ultralytics 학습 인자 (model 필수). 모델 비교는 설정 파일만 바꿔 같은 data.yaml로 학습
- 출력: <출력 폴더>/<설정 파일 이름>/weights/best.pt, best.onnx

실행: python -m game_qa.training.train <설정.yaml> <data.yaml> <출력 폴더> [인자=값 ...]
"""

import sys
from pathlib import Path

import yaml
from ultralytics import YOLO


def train(config, data, out_dir, **overrides):
    """ONNX 파일 경로 반환"""
    args = {**yaml.safe_load(Path(config).read_text(encoding="utf-8")), **overrides}
    model = YOLO(args.pop("model"))
    model.train(data=str(data), project=str(Path(out_dir).resolve()), name=Path(config).stem, exist_ok=True, **args)
    best = YOLO(model.trainer.best)
    return Path(best.export(format="onnx", imgsz=args.get("imgsz", 640)))


def main(config, data, out_dir, *pairs):
    overrides = {k: yaml.safe_load(v) for k, v in (p.split("=", 1) for p in pairs)}
    print(train(config, data, out_dir, **overrides))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
