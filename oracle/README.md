1. 게임 UI 온톨로지
- 그래프 변환, 판정 리포트
- `graph.py`: 추론 결과를 RDF 그래프로 변환 (판정 파이프라인 ④)
- `rules.ttl`: 규칙 SHACL 형상 (SHACL-SPARQL). 파라미터는 검증 시 데이터로 추가
- `validate.py`: pySHACL 검증 (판정 파이프라인 ⑤). 저장소는 Oxigraph
- 설치: `pip install -r oracle/requirements.txt`
- 테스트: `pytest oracle`
