# 관계 정의 (표 4)

| 관계 | 정의역 → 치역 | 정의 | 사용 규칙 | 얻는 방법 |
|---|---|---|---|---|
| represents | WorldIndicator → WorldEntity, HUDElement → WorldEntity | UI가 그 개체의 상태를 나타냄 | R-IND-01~03 | 라벨링 태깅(정답) / 추론 시 거리 기반 1:1 할당 / HUD는 게임 매핑에서 선언 |
| near | WorldIndicator → WorldEntity | 지시 UI 하단 중심과 대상 bbox 상단 중심 사이 거리 / 대상 bbox 높이 | R-IND-01, 02, 03 | 후처리 계산 |
| overlaps | WorldEntity → Terrain, HUDElement → HUDElement | area(A∩B) / area(A) (지형은 가려진 부분을 추정한 마스크 사용). HUD끼리는 area(A∩B) / min(area(A), area(B)) | R-PHY-01, 02, R-UI-01 | 후처리 계산 |
| contains | UIPanel → TextLabel, Screen → TextLabel, HUDElement → HUDElement | area(A∩B) / area(B) (B가 A 안에 들어간 비율) + B가 A 경계선에 닿는지 | R-UI-01, 02 | 후처리 계산 |
| supportedBy | GroundedObject → Terrain, Platform | 오브젝트 하단과 바로 아래 지형·발판 상단 사이 수직 간격 / 오브젝트 높이 | R-PHY-03 | 후처리 계산 |
| occludes | Terrain → Character | 캐릭터 경계 중 지형과 맞닿은 비율, 캐릭터 가시 면적 / 기대 면적 | R-RND-01 | 후처리 계산 (측정 방식 확정 필요) |
| attachedTo | Equipment → Character | 장비 마스크와 가장 가까운 캐릭터 마스크 사이 최소 경계 거리 / 캐릭터 bbox 높이 | R-ATT-01 | 라벨링 태깅(정답) / 후처리 계산 |

라벨링 도구에서 사람이 태깅해야 하는 관계는 `represents`(HealthBar → Character)와 `attachedTo`(Equipment → Character) 두 개다. 나머지는 모두 마스크에서 계산한다.

---

## 후처리·스키마 요구사항

- 거리 계열 측정값은 모두 **대상 bbox 높이로 정규화**한 값도 함께 출력
- 지형 마스크의 **가려진 부분 추정**(구멍 메우기) 후처리 필요 (R-PHY-01, 02)
- 가림 측정 방식(R-RND-01) 확정 필요: 지형 접촉 경계 비율, 가시 면적 비
- 지시 UI × 대상의 **1:1 할당 결과**와 거리 행렬 출력 (R-IND-03)
- 텍스트 마스크가 패널 경계선에 닿는지 여부 (R-UI-02)
- JSON의 `class` 값은 `2_concepts.md` 기준 라벨링 클래스 이름 11개를 그대로 사용 (Character, LooseObject, Equipment, GroundedObject, Terrain, Platform, ForegroundDecoration, HealthBar, HUDElement, UIPanel, TextLabel)
