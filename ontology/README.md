# 게임 UI 온톨로지

- 버전: v0
- 단일 화면으로 판별 가능한 화면 요소 간 관계 오류를 규칙으로 정의하고, 규칙에서 개념·관계를 도출

## 문서 구성

| 문서 | 내용 |
|---|---|
| [1_bug_types.md](1_bug_types.md) | 버그 범주 분류, 버그 유형 채택·제외, 버그 → 규칙 대응 |
| [2_rules.md](2_rules.md) | 규칙 요약, 규칙별 판정 방식·반례·임계값 초안 |
| [3_concepts.md](3_concepts.md) | 개념 계층, 라벨링 클래스 |
| [4_relations.md](4_relations.md) | 관계 정의, 후처리·스키마 요구사항 |
| [labeling_guide_v0.md](labeling_guide_v0.md) | 클래스 목록과 라벨링 기준. 3_concepts.md의 라벨링 클래스에서 도출 |
| [truelove2021_relational_bug_cases.csv](truelove2021_relational_bug_cases.csv) | 데이터셋에서 관련 범주(Information, UI, Bounds, Collision, Persistence, Position, Graphics) 중 2D 게임 전체 사례와 관계형 키워드(health bar, clip, sink, overlap, off-screen, float, behind 등) 포함 사례를 추린 983건 (2D 게임 349건을 위로 정렬). 근거 사례를 더 찾을 때 사용. |
