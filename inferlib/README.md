4. C++ 추론 라이브러리

python_ref/ : 후처리 Python 구현 (정답지)
- `concepts.py`: 라벨링 클래스별 개념
- `masks.py`: COCO 마스크 변환, bbox, 경계 픽셀
- `measurements.py`: 측정값 계산
- `relations.py`: 관계 결정
- `infer.py`: 프레임 하나의 추론 결과 생성, 라벨 파일 입력 실행
- 설치: `pip install -r python_ref/requirements.txt`
- 라벨로 추론 결과 생성: `python python_ref/infer.py <라벨.json> <파라미터.json> <출력 폴더>`
  - 파라미터 파일: search_radius, fg_search_radius, support_gap_max 값을 담은 JSON. 값은 `ontology/1_rules/README.md` 임계값 목록
- 테스트: `pytest python_ref`
