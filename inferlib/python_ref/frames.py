"""판정 파이프라인 입력·①: 플레이 녹화에서 판정 대상 프레임 추출

- 선별 기준: 화면 변화 감지. 마지막으로 고른 프레임과의 차이가 min_change 이상인 프레임만 선택
  - 판정은 프레임 단위라 같은 화면이 이어지면 판정 결과도 같음 (중복 제거)
  - 모든 프레임을 비교하므로 짧게 나타나는 화면도 선택됨 (일정 간격은 간격 사이 화면을 놓침)
  - 직전 프레임이 아니라 마지막으로 고른 프레임과 비교해, 천천히 바뀌는 화면도 누적 차이로 선택
- 차이: 회색조 픽셀 절대 차이 평균 / 255 (0~1)
- step: 처리량 상한이 필요할 때 step 프레임마다 하나만 비교 대상으로 둠
- 기본값 min_change 0, step 1은 모든 프레임. min_change 값은 녹화로 결정
- 스크린샷은 그대로 통과 (index 0)
- 출력: 프레임 이미지와 frames.json (file, source, index). source·index는 추론 결과 frame과 같음

실행: python frames.py <출력 폴더> <영상·이미지 ...> [--min-change 0] [--step 1]
"""

import argparse
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

VIDEO = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


def change(a, b):
    """회색조 프레임 두 장의 차이 (0~1)"""
    return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean() / 255)


def select(frames, min_change=0.0, step=1):
    """frames: (index, BGR 이미지) 순회. 선택된 (index, 이미지) 생성"""
    last = None
    for index, image in frames:
        if index % step:
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if last is None or change(gray, last) >= min_change:
            last = gray
            yield index, image


def read(video):
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise ValueError(f"영상을 열 수 없음: {video}")
    index = 0
    while True:
        ok, image = capture.read()
        if not ok:
            break
        yield index, image
        index += 1
    capture.release()


def extract(out_dir, paths, min_change=0.0, step=1):
    """frames.json 경로 반환"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for path in map(Path, paths):
        if path.suffix.lower() in VIDEO:
            for index, image in select(read(path), min_change, step):
                name = f"{path.stem}_{index:06d}.png"
                cv2.imwrite(str(out / name), image)
                entries.append({"file": name, "source": path.name, "index": index})
        else:
            shutil.copy2(path, out / path.name)
            entries.append({"file": path.name, "source": path.name, "index": 0})
    manifest = out / "frames.json"
    manifest.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out_dir")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--min-change", type=float, default=0.0)
    parser.add_argument("--step", type=int, default=1)
    args = parser.parse_args()
    print(extract(args.out_dir, args.paths, args.min_change, args.step))


if __name__ == "__main__":
    main()
