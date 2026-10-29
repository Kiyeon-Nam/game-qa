"""판정 파이프라인 ②: ONNX 세그멘테이션 모델로 이미지를 추론해 추론 결과(schemas/inference.schema.json) 생성

- 모델 실행: Ultralytics (내부 ONNX Runtime). YOLO11·YOLO26 출력 차이도 Ultralytics가 처리
- 모델 클래스 이름은 라벨링 클래스 이름이어야 함 (학습 data.yaml의 names)
- 마스크는 원본 이미지 크기로 복원 후 infer_frame에 전달
- 프레임: source·index를 받지 않으면 이미지 파일 이름과 0

실행: python -m game_qa.inferlib.segment <모델.onnx> <파라미터.json> <출력 폴더> <이미지 ...> [--score 0.25]
  --score: 점수 임계값. 기본값은 Ultralytics 기본값
"""

import argparse
import json
import sys
from pathlib import Path

from game_qa.inferlib.infer import PARAMS, infer_frame
from game_qa.ontology.game_ui import class_ids


def load(model_path):
    from ultralytics import YOLO  # 학습 환경 의존성. 다른 함수는 없이 사용 가능

    model = YOLO(str(model_path), task="segment")
    unknown = sorted(set(model.names.values()) - class_ids().keys())
    if unknown:
        raise ValueError(f"라벨링 클래스가 아닌 모델 클래스: {', '.join(unknown)}")
    return model


def instances(result):
    """Ultralytics 결과 하나를 id, class, score, mask 목록으로"""
    if result.masks is None:
        return []
    masks = result.masks.data.cpu().numpy() > 0.5
    classes = result.boxes.cls.int().tolist()
    scores = result.boxes.conf.tolist()
    return [
        {"id": k + 1, "class": result.names[c], "score": round(s, 4), "mask": m}
        for k, (c, s, m) in enumerate(zip(classes, scores, masks))
    ]


def segment(model, image_path, params, score=0.25, source=None, index=0):
    (result,) = model.predict(str(image_path), conf=score, retina_masks=True, verbose=False)
    height, width = result.orig_shape
    frame = {"source": source or Path(image_path).name, "index": index, "width": width, "height": height}
    return infer_frame(frame, instances(result), params)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model")
    parser.add_argument("params")
    parser.add_argument("out_dir")
    parser.add_argument("images", nargs="+")
    parser.add_argument("--score", type=float, default=0.25)
    args = parser.parse_args()
    params = json.loads(Path(args.params).read_text(encoding="utf-8"))
    missing = [k for k in PARAMS if k not in params]
    if missing:
        sys.exit(f"파라미터 누락: {', '.join(missing)}")
    model = load(args.model)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for path in map(Path, args.images):
        result = segment(model, path, params, args.score)
        (out / f"{path.stem}.json").write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
