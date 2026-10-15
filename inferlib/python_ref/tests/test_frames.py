import json

import cv2
import numpy as np
import pytest

from frames import extract, select
from segment import inputs


def frames_of(values):
    """밝기 값 목록을 (index, 단색 BGR 이미지) 목록으로"""
    return [(k, np.full((8, 8, 3), v, np.uint8)) for k, v in enumerate(values)]


def test_default_keeps_all_frames():
    assert [k for k, _ in select(frames_of([10] * 5))] == [0, 1, 2, 3, 4]


def test_change_detection_skips_repeated_screens():
    values = [0, 0, 0, 255, 255, 0]
    assert [k for k, _ in select(frames_of(values), min_change=0.5)] == [0, 3, 5]


def test_slow_change_selected_by_accumulated_difference():
    """프레임마다 0.04씩 바뀌면 직전 프레임 기준으로는 안 잡히지만 마지막 선택 프레임 기준으로 누적"""
    values = [round(255 * 0.04 * k) for k in range(6)]
    assert [k for k, _ in select(frames_of(values), min_change=0.1)] == [0, 3]


def test_step_limits_compared_frames():
    assert [k for k, _ in select(frames_of(range(0, 250, 25)), step=3)] == [0, 3, 6, 9]


def write_video(path, values):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (32, 32))
    for v in values:
        writer.write(np.full((32, 32, 3), v, np.uint8))
    writer.release()


def test_video_and_screenshot_extracted_with_source_index(tmp_path):
    write_video(tmp_path / "play.avi", [0, 0, 0, 255, 255])
    cv2.imwrite(str(tmp_path / "shot.png"), np.zeros((4, 4, 3), np.uint8))
    manifest = extract(tmp_path / "out", [tmp_path / "play.avi", tmp_path / "shot.png"], min_change=0.5)

    entries = json.loads(manifest.read_text(encoding="utf-8"))
    assert entries == [
        {"file": "play_000000.png", "source": "play.avi", "index": 0},
        {"file": "play_000003.png", "source": "play.avi", "index": 3},
        {"file": "shot.png", "source": "shot.png", "index": 0},
    ]
    assert all((tmp_path / "out" / e["file"]).exists() for e in entries)
    assert inputs([manifest])[1] == (tmp_path / "out" / "play_000003.png", "play.avi", 3)


def test_image_input_uses_file_name(tmp_path):
    assert inputs([tmp_path / "a.png"]) == [(tmp_path / "a.png", "a.png", 0)]


def test_unreadable_video_rejected(tmp_path):
    (tmp_path / "broken.mp4").write_bytes(b"not a video")
    with pytest.raises(ValueError):
        extract(tmp_path / "out", [tmp_path / "broken.mp4"])
