import json

import cv2
import numpy as np
import pytest

from game_qa.oracle.frames import extract, load


def write_video(path, values):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (32, 32))
    for v in values:
        writer.write(np.full((32, 32, 3), v, np.uint8))
    writer.release()


def test_video_and_screenshot_extracted_with_source_index(tmp_path):
    write_video(tmp_path / "play.avi", [0, 60, 120, 180, 240])
    cv2.imwrite(str(tmp_path / "shot.png"), np.zeros((4, 4, 3), np.uint8))
    manifest = extract(tmp_path / "out", [tmp_path / "play.avi", tmp_path / "shot.png"], step=3)

    entries = json.loads(manifest.read_text(encoding="utf-8"))
    assert entries == [
        {"file": "play_000000.png", "source": "play.avi", "index": 0},
        {"file": "play_000003.png", "source": "play.avi", "index": 3},
        {"file": "shot.png", "source": "shot.png", "index": 0},
    ]
    assert all((tmp_path / "out" / e["file"]).exists() for e in entries)
    assert load(manifest)[1] == (tmp_path / "out" / "play_000003.png", "play.avi", 3)


def test_unreadable_video_rejected(tmp_path):
    (tmp_path / "broken.mp4").write_bytes(b"not a video")
    with pytest.raises(ValueError):
        extract(tmp_path / "out", [tmp_path / "broken.mp4"])


def test_default_extracts_all_frames(tmp_path):
    write_video(tmp_path / "play.avi", [0, 0, 0, 0])
    entries = json.loads(extract(tmp_path / "out", [tmp_path / "play.avi"]).read_text(encoding="utf-8"))
    assert [e["index"] for e in entries] == [0, 1, 2, 3]
