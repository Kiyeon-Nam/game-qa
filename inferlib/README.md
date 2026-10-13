4. C++ 추론 라이브러리

python_ref/ : 후처리 Python 구현 (정답지)
- 설치: `pip install -r python_ref/requirements.txt`
- 라벨로 추론 결과 생성: `python python_ref/infer.py <라벨.json> <파라미터.json> <출력 폴더>`
  - 파라미터: search_radius, fg_search_radius, support_gap_max (게임별 매핑 적용 값)
- 테스트: `pytest python_ref`
