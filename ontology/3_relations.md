# 관계

③ 관계와 측정값 정의. [도출 절차](README.md#도출-절차) 6(③ 관계)

## 관계

인스턴스 사이의 참·거짓

| 관계 | 정의역 → 치역 | 의미 | 학습 데이터 | 판정 시 결정 근거 |
|---|---|---|---|---|
| represents | Display ∧ World → Entity | 표시가 그 개체의 정보를 나타냄 | 라벨링 태깅 | distance ≤ search_radius인 쌍 중, 대응한 쌍의 distance 합 + 대응하지 못한 표시 수 × search_radius가 최소인 1:1 대응 |
| represents | Display ∧ ScreenFixed → Entity | 표시가 그 개체의 정보를 나타냄 | | 게임별 매핑에서 선언 |
| attachedTo | Equipment → Character | 장비를 든 캐릭터 | 라벨링 태깅 | edge_distance가 가장 작은 캐릭터 |
| belongsTo | TextLabel → UIPanel | 텍스트가 속한 패널 | | contain_ratio가 가장 큰 패널. 겹치는 패널이 없으면 소속 없음 |
| touches | TextLabel → UIPanel 또는 ScreenBounds, Display → ScreenBounds | 앞의 요소가 뒤의 요소 경계선에 닿음 | | 마스크 경계 접촉 |

## 측정값

마스크에서 계산하는 수치. 규칙은 측정값에 임계값을 적용해 판정

| 측정값 | 대상 | 의미 | 정규화 기준 |
|---|---|---|---|
| distance(i, e) | Display ∧ World, Entity | 표시 하단 중심과 개체 bbox 상단 중심 사이 거리 | 개체 bbox 높이 |
| overlap_ratio(a) | Entity | 대상 중 추정 지형과 겹치는 면적 비율. 추정 지형: 모든 Terrain + 대상의 행·열마다 연속 구간의 바로 바깥 양쪽 픽셀(4-이웃)이 모두 Terrain인 구간 | 대상 면적 |
| mutual_overlap(a, b) | HUDElement, HUDElement | 두 요소가 겹치는 면적 | 작은 요소 면적 |
| contain_ratio(p, x) | UIPanel, TextLabel | 텍스트 중 p 안에 있는 면적 비율 | 텍스트 면적 |
| support_gap(o) | GroundedObject | 오브젝트 하단과 바로 아래 Terrain 또는 Platform 상단 사이 수직 간격. 화면 안에 없으면 화면 하단까지 간격(실제 간격의 하한) | 오브젝트 높이 |
| edge_distance(q, c) | Equipment, Character | 두 마스크 경계 사이 최소 거리 | 캐릭터 bbox 높이 |
| foreground_coverage(i) | Display ∧ World | i 하단 중심에서 반지름 fg_search_radius인 원 중 ForegroundDecoration이 덮는 비율 | 원 중 화면 안 면적 |
| foreground_coverage(o) | GroundedObject | o 바로 아래, 너비 o bbox 너비·높이 support_gap_max인 사각형 중 ForegroundDecoration이 덮는 비율 | 사각형 중 화면 안 면적. 높이는 o bbox 높이 기준 |
