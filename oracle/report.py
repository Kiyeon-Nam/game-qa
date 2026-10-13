"""판정 파이프라인 ⑥: 추론 결과를 검증해 판정 리포트(schemas/report.schema.json) 생성

실행: python report.py <파라미터.json> <출력 폴더> <추론 결과.json ...>
"""

import json
import sys
from pathlib import Path

from validate import violations


def to_report(result, params):
    frame = {"source": result["frame"]["source"], "index": result["frame"]["index"]}
    return {"frame": frame, "violations": [{"rule": rule, "targets": list(targets)} for rule, targets in violations(result, params)]}


def main(params_path, out_dir, *result_paths):
    params = json.loads(Path(params_path).read_text(encoding="utf-8"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for path in map(Path, result_paths):
        report = to_report(json.loads(path.read_text(encoding="utf-8")), params)
        (out / path.name).write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
