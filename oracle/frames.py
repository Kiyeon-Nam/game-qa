"""판정 파이프라인 입력·①: 플레이 녹화에서 판정 대상 프레임 추출

- 기본: 모든 프레임. step을 주면 step 프레임마다 하나
- 선별 기준은 미정 (녹화로 결정)
- 스크린샷은 그대로 통과 (index 0)
- 출력: 프레임 이미지와 frames.json (file, source, index). source·index는 추론 결과 frame과 같음

실행: python -m game_qa.oracle.frames <출력 폴더> <영상·이미지 ...> [--step 1]
"""

import argparse
import json
import shutil
from pathlib import Path

import cv2

VIDEO = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


def read(video, step=1):
    """(index, BGR 이미지) 순회. step 프레임마다 하나"""
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise ValueError(f"영상을 열 수 없음: {video}")
    index = 0
    while True:
        ok, image = capture.read()
        if not ok:
            break
        if index % step == 0:
            yield index, image
        index += 1
    capture.release()


def extract(out_dir, paths, step=1):
    """frames.json 경로 반환"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for path in map(Path, paths):
        if path.suffix.lower() in VIDEO:
            for index, image in read(path, step):
                name = f"{path.stem}_{index:06d}.png"
                cv2.imwrite(str(out / name), image)
                entries.append({"file": name, "source": path.name, "index": index})
        else:
            shutil.copy2(path, out / path.name)
            entries.append({"file": path.name, "source": path.name, "index": 0})
    manifest = out / "frames.json"
    manifest.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def load(manifest):
    """frames.json을 (이미지 경로, source, index) 목록으로"""
    manifest = Path(manifest)
    return [(manifest.parent / e["file"], e["source"], e["index"]) for e in json.loads(manifest.read_text(encoding="utf-8"))]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out_dir")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--step", type=int, default=1)
    args = parser.parse_args()
    print(extract(args.out_dir, args.paths, args.step))


if __name__ == "__main__":
    main()
