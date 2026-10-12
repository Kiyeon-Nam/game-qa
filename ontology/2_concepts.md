# 개념 계층 (표 3)

## 라벨링 클래스를 정하는 원칙

1. **규칙이 구분을 요구하는 가장 상위 수준에서 라벨링한다.** 예를 들어 아이템과 투사체는 어떤 규칙도 둘을 구분하지 않으므로 상위 개념 `LooseObject` 하나로 칠한다. 개념은 온톨로지에 남겨 두고, 나중에 구분이 필요해지면 그때 클래스를 나눈다.
2. **규칙에서 제외만 하면 되는 개념은 칠하지 않는다.** 배경 벽, 액체, 데미지 숫자는 칠하지 않으면 자동으로 지형·텍스트가 아니게 되므로 클래스가 필요 없다.
3. **게임마다 역할이 다른 화면 요소는 역할이 아닌 형태로 칠한다.** HUD의 하트 아이콘이 체력인지 목숨인지는 게임마다 다르므로, 라벨은 `HUDElement`로 칠하고 역할은 게임 매핑에서 정한다.

이 원칙에 따라 아래 계층의 개념 중 라벨링 클래스는 11개다.

## 개념 계층

| 개념 | 상위 개념 | 설명 | 라벨링 | 사용 규칙 |
|---|---|---|---|---|
| ScreenElement | — | 화면에 보이는 모든 요소의 최상위 | 추상 | — |
| WorldElement | ScreenElement | 게임 세계 좌표에 존재하는 요소 | 추상 | — |
| WorldEntity | WorldElement | 개별 개체 | 추상 | R-001~R-003 (대상) |
| Character | WorldEntity | 플레이어, 적, NPC. 움직이는 생명체 | **클래스 0** | R-004, R-007, R-008 |
| LooseObject | WorldEntity | 고정되지 않은 작은 개체 | **클래스 1** | R-005 |
| Item | LooseObject | 줍는 아이템, 코인, 드롭 | (LooseObject로 칠함) | R-005 |
| Projectile | LooseObject | 날아가는 투사체, 던진 무기 | (LooseObject로 칠함) | R-005 |
| Equipment | WorldEntity | 캐릭터가 손에 든 무기·도구 | **클래스 2** | R-008 |
| GroundedObject | WorldEntity | 바닥에 놓이는 고정물 (상자, 문, 가구) | **클래스 3** | R-006 |
| WorldStructure | WorldElement | 게임 세계의 구조물 | 추상 | — |
| Terrain | WorldStructure | 충돌하는 고체 블록 (바닥, 벽, 천장) | **클래스 4** | R-004~R-006, R-007 |
| Ground / Wall / Ceiling | Terrain | 지형의 부위 | 칠하지 않음 (공간 관계로 구분) | — |
| Platform | WorldStructure | 아래에서 통과 가능한 얇은 발판 | **클래스 5** | R-004 (제외), R-006 (지지) |
| ForegroundDecoration | WorldStructure | 캐릭터 앞에 그려지는 장식 (전경 풀숲, 기둥) | **클래스 6** | R-001, R-006, R-007 (판정 보류·제외) |
| Background | WorldStructure | 하늘, 원경, 배경 벽 | 칠하지 않음 | R-004, R-005 (제외) |
| Liquid | WorldStructure | 물, 용암 | 칠하지 않음 | R-004 (제외) |
| UIElement | ScreenElement | 화면에 그려지는 UI | 추상 | — |
| WorldUI | UIElement | 게임 세계 위치를 따라다니는 UI | 추상 | — |
| WorldIndicator | WorldUI | 특정 개체를 가리키는 UI | 추상 | R-001~R-003 |
| HealthBar | WorldIndicator | 개체 머리 위 체력바 | **클래스 7** | R-001~R-003 |
| Nameplate | WorldIndicator | 개체 이름표 | v0 칠하지 않음 (대상 게임에 있으면 추가) | R-001~R-003 |
| TargetMarker | WorldIndicator | 조준·잠금 표시 | v0 칠하지 않음 (대상 게임에 있으면 추가) | R-001~R-003 |
| WorldText | WorldUI | 데미지 숫자 등 개체를 따라다니는 텍스트 | 칠하지 않음 | R-010 (제외) |
| ScreenUI | UIElement | 화면에 고정된 UI | 추상 | — |
| HUDElement | ScreenUI | 체력, 점수, 미니맵, 아이콘 등 HUD 구성 요소 | **클래스 8** | R-009 |
| HUDHealth / ScoreDisplay / Minimap 등 | HUDElement | HUD 요소의 역할 | 칠하지 않음 (게임 매핑으로 지정) | represents (매핑 선언) |
| UIPanel | ScreenUI | 텍스트를 담는 상자 (대화창, 메뉴 창) | **클래스 9** | R-010 |
| Popup | UIPanel | 툴팁, 알림창 | (UIPanel로 칠함) | R-009 (제외) |
| TextLabel | ScreenUI | 화면 고정 UI 안의 글자 | **클래스 10** | R-010 |
| Screen | — | 이미지 경계 자체 | 칠하지 않음 (이미지 크기로 계산) | R-010 |

## 계층 구조

```
ScreenElement
├─ WorldElement
│  ├─ WorldEntity
│  │  ├─ Character            [0]
│  │  ├─ LooseObject          [1]
│  │  │  ├─ Item
│  │  │  └─ Projectile
│  │  ├─ Equipment            [2]
│  │  └─ GroundedObject       [3]
│  └─ WorldStructure
│     ├─ Terrain              [4]
│     │  └─ Ground / Wall / Ceiling
│     ├─ Platform             [5]
│     ├─ ForegroundDecoration [6]
│     ├─ Background
│     └─ Liquid
└─ UIElement
   ├─ WorldUI
   │  ├─ WorldIndicator
   │  │  ├─ HealthBar         [7]
   │  │  ├─ Nameplate
   │  │  └─ TargetMarker
   │  └─ WorldText
   └─ ScreenUI
      ├─ HUDElement           [8]
      │  └─ HUDHealth / ScoreDisplay / Minimap ...
      ├─ UIPanel              [9]
      │  └─ Popup
      └─ TextLabel            [10]

Screen (이미지 경계)
[n] = 라벨링 클래스 ID
```

## 계층에서 확인할 것 (OWL 작성 시)

- R-001~R-003은 `WorldIndicator`에 건다. 그러면 Nameplate, TargetMarker를 나중에 클래스로 추가해도 규칙을 다시 쓰지 않는다. 온톨로지 효과 검증(11월 4주)의 예시로 쓸 수 있다.
- R-005는 `LooseObject`에 건다. 하위 개념인 Item과 Projectile에 자동 적용된다.
- `Terrain`과 `Platform`은 형제 개념이다. R-004은 `Terrain`에만 걸리므로 발판 통과는 위반이 아니고, R-006의 지지 대상은 두 개념을 모두 허용한다.
- `Popup`이 `UIPanel` 아래, `HUDElement` 밖에 있으므로 R-009이 팝업에 적용되지 않는다.

## 도입 근거 메모

- 지시 UI (WorldIndicator): 체력바, 이름표, 조준 표시를 하나의 상위 개념으로 묶어 R-001~R-003을 상위 개념에 한 번만 검. 온톨로지 계층 사용 근거 사례
- 월드 개체 상위 개념: R-004, R-005가 같은 관계(객체 ↔ 지형 겹침)라 상위 개념 하나에 규칙을 걸 수 있는지 확인 필요
- 지면 고정 오브젝트 (GroundedObject): 코인·아이템은 원래 떠 있는 경우가 많고 캐릭터는 점프와 구분 불가하여, R-006을 적용할 별도 개념으로 분리
- 장비 (Equipment): R-008을 위해 별도 라벨링 클래스로 추가. 라벨링 가이드에 "손에 든 장비는 캐릭터와 분리해 칠함" 명시
