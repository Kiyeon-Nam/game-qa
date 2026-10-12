# 관계

③ 관계와 측정값 정의. [도출 절차](README.md#도출-절차) 6(③ 관계)

## 관계

인스턴스 사이의 참·거짓

| 관계 | 정의역 → 치역 | 의미 | 학습 데이터 | 판정 시 결정 근거 |
|---|---|---|---|---|
| represents | Display ∧ World → Entity | 표시가 그 개체의 정보를 나타냄 | 라벨링 태깅 | distance 기준 1:1 대응, search_radius 이내 |
| represents | Display ∧ ScreenFixed → Entity | 표시가 그 개체의 정보를 나타냄 | | 게임별 매핑에서 선언 |
| attachedTo | Equipment → Character | 장비를 든 캐릭터 | 라벨링 태깅 | edge_distance가 가장 작은 캐릭터 |
| belongsTo | TextLabel → UIPanel | 텍스트가 속한 패널 | | contain_ratio가 가장 큰 패널. 겹치는 패널이 없으면 소속 없음 |
| touches | TextLabel → UIPanel, Display → ScreenBounds | 앞의 요소가 뒤의 요소 경계선에 닿음 | | 마스크 경계 접촉 |

## 측정값

마스크에서 계산하는 수치. 규칙은 측정값에 임계값을 적용해 판정

| 측정값 | 대상 | 의미 | 정규화 기준 |
|---|---|---|---|
| distance(i, e) | Display ∧ World, Entity | 표시 하단 중심과 개체 bbox 상단 중심 사이 거리 | 개체 bbox 높이 |
| overlap_ratio(a, t) | Entity, Terrain | 대상 중 지형과 겹치는 면적 비율. 지형은 다른 요소에 가려진 부분까지 추정한 영역 | 대상 면적 |
| mutual_overlap(a, b) | HUDElement, HUDElement | 두 요소가 겹치는 면적 | 작은 요소 면적 |
| contain_ratio(p, x) | UIPanel 또는 ScreenBounds, TextLabel | 텍스트 중 p 안에 있는 면적 비율 | 텍스트 면적 |
| support_gap(o) | GroundedObject | 오브젝트 하단과 바로 아래 Terrain 또는 Platform 상단 사이 수직 간격 | 오브젝트 높이 |
| contact_boundary_ratio(c, t) | Character, Terrain | 캐릭터 경계 중 지형과 맞닿은 부분의 비율 | 캐릭터 경계 길이 |
| visible_area_ratio(c) | Character | 캐릭터의 보이는 면적 | 같은 인스턴스 bbox로 추정한 기대 면적 |
| edge_distance(q, c) | Equipment, Character | 두 마스크 경계 사이 최소 거리 | 캐릭터 bbox 높이 |
| foreground_coverage(r) | 영역 | 영역 중 ForegroundDecoration이 덮는 비율 | 영역 면적 |
