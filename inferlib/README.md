# 추론 라이브러리

세그멘테이션 결과 또는 라벨에서 측정값·관계를 계산해 추론 결과(`schemas/inference.schema.json`) 생성 (판정 파이프라인 ②·③)

- `python_ref/`: Python 구현. 판정 파이프라인이 사용하고, C++ 구현의 정답지
- `cpp/`, `bindings/`: C++ 구현, Python 바인딩 (비어 있음)

python_ref/
- `masks.py`: COCO 마스크 변환, bbox, 이웃 픽셀
- `measurements.py`: 측정값 계산
- `relations.py`: 관계 결정
- `infer.py`: 프레임 하나의 추론 결과 생성, 라벨 파일 입력 실행
- `segment.py`: ONNX 세그멘테이션 모델로 이미지 추론 후 추론 결과 생성 (판정 파이프라인 ②)
- 설치: [환경 세팅](../README.md#환경-세팅-방법) 후 `pip install -r inferlib/python_ref/requirements.txt`
- 라벨로 추론 결과 생성: `python -m game_qa.inferlib.infer <라벨.json> <파라미터.json> <출력 폴더>`
  - 파라미터 파일: search_radius, fg_search_radius, support_gap_max 값을 담은 JSON. 값은 `ontology/1_rules/README.md` 임계값 목록 (fg_search_radius는 미정이라 임의 값)
- 이미지로 추론 결과 생성: `python -m game_qa.inferlib.segment <모델.onnx> <파라미터.json> <출력 폴더> <이미지 ...> [--score 0.25]`
  - 추가 설치: `training/README.md`의 학습 환경 (ultralytics)
  - 모델 클래스 이름은 라벨링 클래스 이름이어야 함
- 테스트: `pytest python_ref`
  - 이미지 추론 테스트는 ultralytics가 설치된 경우만 실행
