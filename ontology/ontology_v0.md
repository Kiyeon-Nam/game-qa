# 게임 UI 온톨로지 v0: 버그 유형과 규칙

> **담당**: A 이서윤 (온톨로지·검증)
> **출처**: Truelove et al., "We'll Fix It in Post", ICSE 2021 — 표 II 분류 체계 + 공개 데이터셋(`github.com/truelova/ICSE_2021_UpdateNotes`, 버그 수정 12,122건)
> **선정 조건**: ① 단일 화면으로 판별 가능 ② 화면 요소 간 관계 오류 ③ 2D 플랫포머에서 발생 가능
> **규칙 작성 원칙**: 상황별 조건이 아니라 "화면 요소들이 **항상** 만족해야 하는 관계"로 쓴다. 규칙마다 정상인데 위반처럼 보이는 반례를 찾고, 반례는 **개념 분리** 또는 **규칙 조건 축소**로 처리한다.
> **임계값**: 모두 초안(?)이다. 11월 1주 규칙 동결 전에 정상 프레임의 측정값 분포를 보고 보정한다. 거리·간격은 해상도에 영향받지 않도록 대상 크기나 화면 크기에 대한 비율로 정의한다.
> **데이터 참고**: 데이터셋 30개 게임 중 2D 게임은 Terraria(511건)와 Brawlhalla(75건)뿐이라, 이 두 게임을 우선 근거로 쓰고 나머지 게임 사례는 2D 플랫포머 상황으로 바꿔 해석함

## 목차

1. 버그 범주 분류
2. 버그 유형 후보 (채택 10 / 제외 4)
3. 버그 → 규칙 대응
4. 규칙 요약
5. 규칙별 상세
6. 개념 계층 (표 3)
7. 관계 정의 (표 4)
8. 다른 담당자에게 넘길 것
9. 부록

---

## 1. 버그 범주 분류 (Truelove 표 II, 20개 범주)

| 범주 | 정의 요약 | 전체 건수 (순위) | 2D 게임 건수 | 단일 화면 | 관계 | 판단 |
|---|---|---|---|---|---|---|
| Information | 게임 정보가 플레이어에게 제대로 전달되지 않음 | 1,748 (1) | 62 | O | O (일부) | 부분 채택 (지시 UI 관련만) |
| Game Graphics | 시각 요소가 잘못 렌더링됨 | 1,583 (2) | 100 | O | △ | 부분 채택 (레이어 순서 오류만, 나머지는 GLIB 영역) |
| Action | 행동 가능/불가능 오류 | 1,164 (3) | 39 | X | — | 제외 (입력 필요) |
| User Interface | UI 요소의 모양·위치·동작 오류 | 997 (4) | 26 | O | O | 채택 |
| Triggered Event | 이벤트 연쇄 오류 | 830 (5) | 26 | X | — | 제외 (시간 필요) |
| Value | 변수 값이 틀림 | 781 (6) | 36 | △ | X | 제외 (정답 값 필요) |
| Position of Object | 객체 위치·방향이 시간에 따라 틀림 | 763 (7) | 79 | △ | O | 부분 채택 (정적 상태로 드러나는 것만) |
| Crash | 강제 종료 | 580 (8) | 22 | X | — | 제외 |
| Object Persistence | 객체가 게임 세계에 제대로 들어오거나 나가지 않음 | 548 (9) | 67 | △ | O | 부분 채택 (잔류 UI만, 대부분은 월드 생성 문제) |
| Interaction Between Object Properties | 객체 속성 간 상호작용 오류 | 539 (10) | 15 | X | — | 제외 |
| Collision of Objects | 객체 접촉 시 잘못 동작 | 449 (11) | 13 | O | O | 채택 |
| Context State | 객체 상태 전이 오류 | 375 (12) | 14 | X | — | 제외 |
| Audio | 소리 오류 | 344 (13) | 19 | X | — | 제외 |
| Implementation Response | 하드웨어·성능 문제 | 343 (14) | 23 | X | — | 제외 |
| Artificial Intelligence | NPC 행동 오류 | 327 (15) | 14 | X | — | 제외 |
| Bounds | 객체가 허용 공간 밖에 있음 | 231 (16) | 2 | △ | O | 병합 (Collision of Objects로 처리) |
| Event Occurrence | 이벤트 발생 빈도·순서 오류 | 200 (17) | 13 | X | — | 제외 |
| Exploit | 의도치 않은 이득 | 129 (18) | 12 | X | — | 제외 |
| Interrupted Event | 행동이 부당하게 중단됨 | 98 (19) | 2 | X | — | 제외 |
| Camera | 카메라 문제 | 93 (20) | 2 | △ | X | 제외 |

> 수행계획서의 "UI 오류도 상위권(4위)" 기술은 데이터셋 집계(997건, 4위)와 일치함.

---

## 2. 버그 유형 후보 (14개: 채택 10 / 제외 4)

### 2-1. 채택

| ID | 버그 유형 | 화면에서 어떻게 보이나 (2D 플랫포머) | 논문 범주 | 단일 화면 | 관계 오류 | 데이터셋 근거 사례 |
|---|---|---|---|---|---|---|
| **B01** | 대상 없는 지시 UI | 적이 사라졌는데 체력바·이름표만 허공에 남아 있음 | Information, Object Persistence | O | O (지시 UI ↔ 대상) | Warframe: *"resource crate names lingering after being destroyed"* |
| **B02** | 지시 UI 위치 이탈 | 체력바·이름표·조준 표시가 대상에서 멀리 떨어져 표시됨 | User Interface, Information | O | O (지시 UI ↔ 대상 거리) | Terraria: *"team nameplates being in the wrong position"*, *"lock-on icon would at an inverted position in reverse gravity"* / Path of Exile: *"location of animated weapons' health bar to sometimes be incorrect"* |
| **B03** | 지시 UI 대응 오류 | 체력바 하나가 두 적 사이에 떠 있음, 한 대상에 체력바가 둘 | Information, User Interface | O | O (지시 UI ↔ 대상 1:1) | Terraria: *"two different worm enemies ... would show a single health bar in the space between them"* / Warframe: *"ally kuva lich name/health bar overriding enemy kuva lich ui"* |
| **B04** | 캐릭터 지형 파묻힘 | 캐릭터 몸 일부가 바닥·벽 타일 안으로 들어가 있음 | Collision of Objects, Position of Object, Bounds | O | O (캐릭터 ↔ 지형 겹침) | Terraria: *"goblins would get stuck in doors and sink into the floor"*, *"large zombies would slightly clip into the ground"*, *"tortoise-type enemies would be pushed down into the ground"* |
| **B05** | 아이템·투사체 지형 박힘 | 아이템이나 투사체가 블록 내부에 박혀 있음 | Collision of Objects | O | O (아이템 ↔ 지형 겹침) | Terraria: *"falling stars would ... end up embedded in the dirt"*, *"yoyos could get stuck in blocks"*, *"lightning sentries ... would sink into the ground"* |
| **B06** | HUD 요소 간 겹침 | 미니맵·체력·점수 등 HUD 요소가 서로 덮음 | User Interface | O | O (HUD ↔ HUD 겹침) | Terraria: *"minimap and other ui elements to overlap"*, *"slight overlap between the pvp button and dye slots"* / 전체 데이터셋에서 "overlap" 포함 122건 중 UI 범주 80건 |
| **B07** | 텍스트 영역 이탈 | 텍스트가 상자나 화면 밖으로 넘치거나 잘림 | User Interface | O | O (텍스트 ⊂ 컨테이너/화면) | Terraria: *"cut off the text in an ugly way"* / Warframe: *"research names going off screen"* / "off-screen·cut off·overflow" 포함 48건 중 UI 범주 25건 |

**설계 메모**
- B01~B03은 체력바, 이름표, 조준 표시를 모두 **"지시 UI"라는 상위 개념**으로 묶으면 규칙 하나를 상위 개념에 걸어 하위 개념 전체에 적용할 수 있음. 온톨로지 계층 사용 근거로 쓰기 좋은 사례.
- B04와 B05는 같은 관계(객체 ↔ 지형 겹침)라서 규칙을 상위 개념(월드 개체)에 하나로 걸 수 있는지 규칙 작성 단계에서 확인.
- B01과 B02의 경계는 "대상까지의 거리 임계값"으로 구분됨 (후보가 아예 없으면 B01, 있지만 멀면 B02).

### 2-2. 채택 (적용 조건 있음)

| ID | 버그 유형 | 화면에서 어떻게 보이나 | 논문 범주 | 단일 화면 | 관계 오류 | 데이터셋 근거 사례 | 적용 조건 |
|---|---|---|---|---|---|---|---|
| **B08** | 고정 오브젝트 부유 | 상자·문·가구 같은 고정 배치물이 지면에서 떠 있음 | Position of Object | △ | O (고정물 ↔ 지면 접촉) | Terraria: *"falling blocks floating in the air"*, pianos *"looked like they were floating"*, tiles *"drawing a few pixels too low"* | **지면 고정 개념에만 적용**. 코인·아이템은 원래 떠 있는 경우가 많고, 캐릭터는 점프와 구분 불가 → 개념 계층에 '지면 고정 오브젝트'를 별도 개념으로 둠 |
| **B09** | 레이어 순서 오류 | 적·캐릭터가 문이나 지형 뒤에 그려져 가려짐 | Game Graphics | O | O (캐릭터 ↔ 지형 가림) | Terraria: *"angry tumblers would visually draw behind doors and actuated blocks"*, pond would *"appear in front of"* pillars / Path of Exile: characters *"render behind track tiles"* | 가시 마스크만으로는 "가려짐"과 "파묻힘(B04)"이 비슷하게 보임 → 가림 측정 방법을 공간 관계 정의서(C)에 반영 필요 |
| **B10** | 장비 스프라이트 분리 | 무기·장비가 캐릭터 손에서 떨어져 떠 있음 | Position of Object | O | O (장비 ↔ 캐릭터 부착) | Terraria: *"betsy's wrath would hover outside of the player's hand"*, *"keybrand wasn't actually in your hand"*, backpacks *"drew at incorrect heights"* | 장비를 별도 라벨링 클래스로 추가 → 클래스 목록 v0에 반영, 라벨링 가이드에 "손에 든 장비는 캐릭터와 분리해 칠함" 명시 |

### 2-3. 제외 (범위 설명·향후 과제용으로 보존)

| ID | 버그 유형 | 화면에서 어떻게 보이나 | 논문 범주 | 제외 이유 | 데이터셋 근거 사례 |
|---|---|---|---|---|---|
| **B11** | 캐릭터 공중 정지 | 캐릭터가 발판 없이 공중에 떠 있음 | Position of Object | 단일 프레임으로 점프·낙하와 구분 불가 → 연속 프레임 필요 (3순위 확장 과제) | Black Desert: *"npc ... was floating in the air"* |
| **B12** | 맵 경계 이탈 | 캐릭터가 맵 바깥으로 떨어짐 | Bounds | 대부분 화면에 보이지 않음. 보이는 경우는 B04로 처리 | Terraria: *"tax collector fell out of the bottom of the map"* |
| **B13** | 닫힌 UI 잔류 | 인벤토리를 닫았는데 드래그하던 아이콘이 화면에 남음 | User Interface, Object Persistence | "인벤토리가 닫혔다"는 직전 상태 정보가 필요 | Rust: *"item icon staying on screen if inventory is closed while dragging"* |
| **B14** | 표시 값 오류 | 획득한 돈과 화면에 표시된 금액이 다름 | Value, Information | 실제 게임 내부 값(정답)이 필요하고 OCR이 필요 | Terraria: *"money displayed on screen was incorrect"* |

---

## 3. 버그 → 규칙 대응

| 버그 | 버그 유형 | 규칙 ID |
|---|---|---|
| B01 | 대상 없는 지시 UI | R-IND-01 |
| B02 | 지시 UI 위치 이탈 | R-IND-02 |
| B03 | 지시 UI 대응 오류 | R-IND-03 |
| B04 | 캐릭터 지형 파묻힘 | R-PHY-01 |
| B05 | 아이템·투사체 지형 박힘 | R-PHY-02 |
| B06 | HUD 요소 간 겹침 | R-UI-01 |
| B07 | 텍스트 영역 이탈 | R-UI-02 |
| B08 | 고정 오브젝트 부유 | R-PHY-03 |
| B09 | 레이어 순서 오류 | R-RND-01 |
| B10 | 장비 스프라이트 분리 | R-ATT-01 |
| B11~B14 | 제외 | — |

---

## 4. 규칙 요약

| 규칙 ID | 버그 | 규칙 (항상 성립해야 하는 관계) | 대상 개념 | 관계 |
|---|---|---|---|---|
| R-IND-01 | B01 | 월드 지시 UI는 나타내는 대상을 **최소 1개** 가진다 | WorldIndicator → WorldEntity | represents |
| R-IND-02 | B02 | 월드 지시 UI는 대상과 **가까이**(대상 크기 기준 거리 이내) 있다 | WorldIndicator, WorldEntity | represents, near |
| R-IND-03 | B03 | 월드 지시 UI는 대상을 **최대 1개** 나타내고, 한 대상은 같은 종류의 지시 UI를 **최대 1개** 가진다 | WorldIndicator, WorldEntity | represents |
| R-PHY-01 | B04 | 캐릭터는 지형과 일정 비율 이상 **겹치지 않는다** | Character, Terrain | overlaps |
| R-PHY-02 | B05 | 아이템·투사체는 지형 **내부에 포함되지 않는다** | LooseObject (Item, Projectile), Terrain | overlaps |
| R-PHY-03 | B08 | 바닥 고정 오브젝트는 아래쪽이 지형 또는 플랫폼과 **접촉한다** | GroundedObject, Terrain, Platform | supportedBy |
| R-RND-01 | B09 | 캐릭터는 지형에 **가려지지 않는다** (지형은 항상 캐릭터 뒤 레이어) | Character, Terrain | occludes |
| R-ATT-01 | B10 | 장비는 그것을 든 캐릭터와 **접촉한다** | Equipment, Character | attachedTo |
| R-UI-01 | B06 | HUD 요소끼리는 **부분적으로 겹치지 않는다** (완전 포함은 허용) | HUDElement | overlaps, contains |
| R-UI-02 | B07 | 텍스트는 자신이 속한 UI 패널과 화면 **안에 완전히 포함된다** | TextLabel, UIPanel, Screen | contains |

---

## 5. 규칙별 상세

### R-IND-01 · 대상 없는 지시 UI (B01)

- **규칙**: 월드 공간의 지시 UI(체력바, 이름표, 조준 표시)는 나타내는 대상 개체를 최소 1개 가진다.
- **판정 방식**: 추론 시 `represents`는 "지시 UI에서 탐색 반경 안에 있는 가장 가까운 대상"으로 연결한다. 탐색 반경 안에 대상 후보가 하나도 없으면 위반.
- **필요 측정값 (C)**: 지시 UI와 각 WorldEntity 사이 거리(지시 UI 하단 중심 ↔ 대상 bbox 상단 중심), 대상 bbox 높이
- **임계값 초안**: 탐색 반경 = 대상 후보 bbox 높이 × 2.0 (?)

| 반례 (정상인데 위반처럼 보임) | 처리 |
|---|---|
| 화면 상단에 고정된 보스 체력바, HUD의 플레이어 체력 | **개념 분리**: 화면 고정 체력 표시는 `HUDElement`로 두고, 대상은 게임 매핑에서 선언. 이 규칙은 `WorldIndicator`에만 적용 |
| 대상이 화면 밖에 있고 체력바만 화면 가장자리에 걸침 | **조건 축소**: 지시 UI가 화면 경계에 닿아 있으면 판정 제외 |
| 대상이 전경 장식(풀숲 등)에 완전히 가려져 검출 안 됨 | **조건 축소**: 탐색 반경 안이 `ForegroundDecoration`으로 덮여 있으면 판정 보류 |
| 대상 사망 직후 체력바가 사라지는 연출 중인 프레임 | 단일 프레임 범위의 한계로 인정. 리포트에 저신뢰 표시 (연속 프레임은 3순위 확장 과제) |

### R-IND-02 · 지시 UI 위치 이탈 (B02)

- **규칙**: 월드 지시 UI는 자신이 나타내는 대상 가까이에 있다.
- **판정 방식**: R-IND-01로 연결된 대상과의 거리가 부착 거리 초과(탐색 반경 이내)면 위반. 탐색 반경 밖이면 R-IND-01 위반으로 처리되어 둘이 겹치지 않는다.
- **필요 측정값 (C)**: R-IND-01과 같음 + 상대 위치(위·아래·좌·우)
- **임계값 초안**: 부착 거리 = 대상 bbox 높이 × 0.5 (?)

| 반례 | 처리 |
|---|---|
| 큰 보스는 체력바가 몸에서 멀리 떠 있어도 정상 | 거리를 **대상 크기에 비례**하게 정의해서 해결 |
| 이름표를 의도적으로 높이 띄우는 게임 | **게임별 파라미터**: 부착 거리 배수를 게임 매핑에서 덮어쓸 수 있게 함 |
| 지시 UI가 대상 아래쪽에 붙는 게임 | 상대 위치는 판정에 쓰지 않고 거리만 사용 (상대 위치는 리포트 근거로만 출력) |

### R-IND-03 · 지시 UI 대응 오류 (B03)

- **규칙**: 월드 지시 UI는 대상을 최대 1개 나타내고, 한 대상은 같은 종류의 지시 UI를 최대 1개 가진다.
- **판정 방식**: 지시 UI와 대상을 거리 기반 **1:1 할당**(헝가리안 매칭 등)으로 연결한 뒤, 할당되지 못한 지시 UI가 두 대상의 중간(두 대상까지 거리가 비슷)에 있으면 위반 / 한 대상에 같은 종류 지시 UI가 2개 이상 부착 거리 안에 있으면 위반.
- **필요 측정값 (C)**: 지시 UI × 대상 전체 거리 행렬
- **임계값 초안**: "중간에 있음" = 가장 가까운 두 대상까지 거리 비 ≥ 0.8 (?)

| 반례 | 처리 |
|---|---|
| 플레이어 머리 위에 이름표와 체력바가 같이 있음 | "같은 종류"로 한정: `HealthBar`와 `Nameplate`는 다른 개념이므로 위반 아님 |
| 적 여러 마리가 겹쳐 있어 체력바들이 붙어 있음 | 가장 가까운 대상 연결이 아니라 **1:1 할당**을 쓰면 정상으로 처리됨 |
| 여러 마디로 된 적(벌레형)이 체력바 하나를 공유하는 게 정상인 게임 | 여러 인스턴스가 한 개체인 경우는 라벨링에서 **한 인스턴스로 칠함** (라벨링 가이드 반영) |

### R-PHY-01 · 캐릭터 지형 파묻힘 (B04)

- **규칙**: 캐릭터는 지형과 일정 비율 이상 겹치지 않는다.
- **주의: 측정 문제**: 세그멘테이션은 **보이는 부분만** 마스크로 내기 때문에, 캐릭터가 지형 위에 그려지면 지형 마스크에 캐릭터 모양의 구멍이 생길 뿐 두 마스크는 겹치지 않는다. 따라서 **지형의 가려진 부분을 추정한 마스크**가 필요하다.
  - 방법 A (C, 후처리): 지형 마스크의 구멍을 메워 가려진 지형 추정 (모폴로지 closing, 타일 격자 보간)
  - 방법 B (B, 라벨링): 지형을 캐릭터에 가려진 부분까지 포함해 칠하고 모델이 학습하도록 함
  - 방법 A를 먼저 시도하고, 정확도가 부족하면 B를 검토
- **필요 측정값 (C)**: `overlap_ratio = |캐릭터 ∩ 추정 지형| / |캐릭터|`
- **임계값 초안**: ≤ 0.15 (?)

| 반례 | 처리 |
|---|---|
| 캐릭터가 바닥에 서 있을 때 발끝이 1~2px 겹침 | 비율 임계값으로 흡수 |
| 캐릭터가 배경 벽(뒤쪽 장식 벽) 앞에 있음 | **개념 분리**: 충돌하는 블록만 `Terrain`, 배경 벽은 `Background`. 라벨링 가이드에 명시 |
| 통과 가능한 발판(아래에서 뚫고 올라가는 플랫폼)을 지나는 중 | **개념 분리**: `Platform`을 `Terrain`과 별도 개념으로 두고 이 규칙에서 제외 |
| 물·용암 같은 액체 안에 들어가 있음 | 액체는 `Terrain`이 아님 (라벨링하지 않거나 `Liquid`로 분리) |
| 땅속에서 튀어나오는 연출의 적 | 해당 적 유형은 게임 매핑에서 규칙 비활성 |

### R-PHY-02 · 아이템·투사체 지형 박힘 (B05)

- **규칙**: 아이템과 투사체는 지형 내부에 포함되지 않는다.
- **측정 문제**: R-PHY-01과 같음 (추정 지형 마스크 사용)
- **필요 측정값 (C)**: `overlap_ratio = |아이템 ∩ 추정 지형| / |아이템|`
- **임계값 초안**: ≤ 0.3 (?) (아이템은 작아서 경계 오차 비중이 큼)

| 반례 | 처리 |
|---|---|
| 아이템이 블록 위에 놓여 있음 | 접촉은 겹침이 아니므로 위반 아님 |
| 화살이 벽에 꽂히는 연출 | 해당 투사체 유형은 게임 매핑에서 규칙 비활성 |
| 아이템이 배경 벽 앞에 떠 있음 | R-PHY-01과 같이 `Background` 분리로 해결 |

### R-PHY-03 · 고정 오브젝트 부유 (B08)

- **규칙**: 바닥 고정 오브젝트(상자, 문, 가구 등)는 아래쪽이 지형 또는 플랫폼과 접촉한다.
- **필요 측정값 (C)**: 오브젝트 하단 경계와 그 바로 아래 지형/플랫폼 상단 사이의 수직 간격
- **임계값 초안**: 간격 ≤ 오브젝트 높이 × 0.1 (?)

| 반례 | 처리 |
|---|---|
| 코인·드롭 아이템은 원래 떠서 흔들림 | **개념 분리**: `Item`과 `GroundedObject`는 다른 개념. 이 규칙은 `GroundedObject`에만 적용 |
| 벽걸이 횃불, 천장 샹들리에 | **개념 분리**: 바닥 고정만 이 규칙의 대상. 벽·천장 부착물은 `GroundedObject`에 넣지 않음 |
| 얇은 발판 위에 놓인 상자 | 지지 대상에 `Platform` 포함 |
| 오브젝트 아래가 전경 장식에 가려짐 | 아래 영역이 `ForegroundDecoration`으로 덮이면 판정 보류 |

### R-RND-01 · 레이어 순서 오류 (B09)

- **규칙**: 캐릭터는 지형에 가려지지 않는다. (2D 플랫포머에서 충돌 지형은 항상 캐릭터보다 뒤에 그려진다.)
- **주의: 측정 문제 (가장 어려움)**: 가려진 캐릭터는 보이는 부분만 검출되므로, "원래 있어야 할 부분이 지형에 잘렸다"를 추정해야 한다.
  - 후보 측정: 캐릭터 마스크 경계 중 지형과 맞닿은 경계의 비율 + 캐릭터 가시 면적이 같은 클래스의 평소 크기보다 작은 정도
  - R-PHY-01과의 구분: **파묻힘(B04)은 캐릭터가 지형 위에 그려진 것**(추정 지형과 캐릭터가 겹침), **레이어 오류(B09)는 지형이 캐릭터 위에 그려진 것**(캐릭터가 지형 경계에서 잘림)
  - 측정 방식은 C와 확정 필요. 10월 2주 공간 관계 정의서에 반영
- **필요 측정값 (C)**: 지형 접촉 경계 비율, 캐릭터 가시 면적 / 기대 면적
- **임계값 초안**: 접촉 경계 비율 ≥ 0.3 이면서 가시 면적 비 ≤ 0.7 (?)

| 반례 | 처리 |
|---|---|
| 의도된 전경 레이어(전경 풀숲, 기둥) 뒤를 지나감 | **개념 분리**: `ForegroundDecoration`은 `Terrain`이 아님. 라벨링 가이드에 명시 |
| 문을 통과하는 연출 | 문은 `GroundedObject`로 분류해 `Terrain`에서 제외 |
| 캐릭터가 웅크린 자세라 원래 작게 보임 | 기대 면적은 클래스 평균이 아니라 **같은 인스턴스의 bbox 비율**로 보정. 오탐이 많으면 경계 비율만 사용 |

### R-ATT-01 · 장비 분리 (B10)

- **규칙**: 장비(들고 있는 무기·도구)는 그것을 든 캐릭터와 접촉한다.
- **필요 측정값 (C)**: 장비 마스크와 가장 가까운 캐릭터 마스크 사이의 최소 경계 거리
- **임계값 초안**: ≤ 캐릭터 bbox 높이 × 0.05 (?)

| 반례 | 처리 |
|---|---|
| 던진 무기, 날아가는 부메랑 | **개념 분리**: 손을 떠난 것은 `Projectile`(라벨링 클래스는 `LooseObject`). 라벨링 시 "손에 붙어 있으면 장비, 떨어지면 투사체"로 구분 |
| 바닥에 떨어진 무기 | `Item`으로 라벨링 |
| 휘두르는 동작에서 무기 일부가 잔상 효과로 분리돼 보임 | 잔상·이펙트는 라벨링하지 않음 (라벨링 가이드 반영) |

### R-UI-01 · HUD 요소 간 겹침 (B06)

- **규칙**: HUD 요소끼리는 부분적으로 겹치지 않는다. 한 요소가 다른 요소 안에 **완전히 포함**되는 것은 허용한다.
- **필요 측정값 (C)**: 두 HUD 요소의 겹침 비율 `|A∩B| / min(|A|,|B|)`
- **임계값 초안**: 0.02 < 겹침 비율 < 0.95 이면 위반 (0.95 이상은 포함으로 보고 허용) (?)
- **측정 메모**: HUD도 보이는 마스크만 나오므로 bbox 기준 겹침을 함께 사용 (HUD는 대부분 사각형이라 bbox 오차가 작음)

| 반례 | 처리 |
|---|---|
| 체력바 위의 숫자, 아이콘 위의 수량 숫자 | 완전 포함이므로 허용 |
| 툴팁·팝업이 HUD 위에 뜸 | **개념 분리**: `Popup`은 `UIPanel`의 하위 개념이며 `HUDElement`가 아님. 이 규칙에서 제외 |
| 장식 테두리끼리 맞닿음 | 하한 임계값(0.02)으로 흡수 |

### R-UI-02 · 텍스트 영역 이탈 (B07)

- **규칙**: 텍스트는 자신이 속한 UI 패널 안에, 그리고 화면 안에 완전히 포함된다.
- **필요 측정값 (C)**: `|텍스트 ∩ 패널| / |텍스트|`, 텍스트 bbox와 화면 경계 사이 거리, 텍스트가 패널 경계에 닿는지 여부
- **임계값 초안**: 포함 비율 ≥ 0.98, 화면 경계와 거리 > 0 (?)
- **"잘림" 판정**: 텍스트가 패널 경계에서 잘리면 보이는 마스크는 패널 안에 있어 포함 비율이 정상으로 나온다. 그래서 **텍스트 마스크가 패널 경계선에 닿아 있으면 위반**으로 함께 본다.

| 반례 | 처리 |
|---|---|
| 말줄임(…) 처리된 긴 텍스트 | 패널 안에 있고 경계에 닿지 않으므로 정상 |
| 패널 없이 화면에 직접 뜨는 텍스트 (데미지 숫자 등) | 소속 패널이 없으면 화면 포함만 검사 |
| 화면 밖에서 미끄러져 들어오는 연출 텍스트 | 단일 프레임 한계. 화면 경계에 닿은 텍스트는 저신뢰 표시 |
| 데미지 숫자가 캐릭터를 따라 화면 가장자리에서 잘림 | 데미지 숫자는 `WorldText`로 분리하고 라벨링하지 않으므로 검사 대상에서 빠짐 |

---

## 6. 개념 계층 (표 3)

### 6-1. 라벨링 클래스를 정하는 원칙

1. **규칙이 구분을 요구하는 가장 상위 수준에서 라벨링한다.** 예를 들어 아이템과 투사체는 어떤 규칙도 둘을 구분하지 않으므로 상위 개념 `LooseObject` 하나로 칠한다. 개념은 온톨로지에 남겨 두고, 나중에 구분이 필요해지면 그때 클래스를 나눈다.
2. **규칙에서 제외만 하면 되는 개념은 칠하지 않는다.** 배경 벽, 액체, 데미지 숫자는 칠하지 않으면 자동으로 지형·텍스트가 아니게 되므로 클래스가 필요 없다.
3. **게임마다 역할이 다른 화면 요소는 역할이 아닌 형태로 칠한다.** HUD의 하트 아이콘이 체력인지 목숨인지는 게임마다 다르므로, 라벨은 `HUDElement`로 칠하고 역할은 게임 매핑에서 정한다.

이 원칙에 따라 아래 계층의 개념 중 라벨링 클래스는 11개다.

### 6-2. 개념 계층

| 개념 | 상위 개념 | 설명 | 라벨링 | 사용 규칙 |
|---|---|---|---|---|
| ScreenElement | — | 화면에 보이는 모든 요소의 최상위 | 추상 | — |
| WorldElement | ScreenElement | 게임 세계 좌표에 존재하는 요소 | 추상 | — |
| WorldEntity | WorldElement | 개별 개체 | 추상 | R-IND-01~03 (대상) |
| Character | WorldEntity | 플레이어, 적, NPC. 움직이는 생명체 | **클래스 0** | R-PHY-01, R-RND-01, R-ATT-01 |
| LooseObject | WorldEntity | 고정되지 않은 작은 개체 | **클래스 1** | R-PHY-02 |
| Item | LooseObject | 줍는 아이템, 코인, 드롭 | (LooseObject로 칠함) | R-PHY-02 |
| Projectile | LooseObject | 날아가는 투사체, 던진 무기 | (LooseObject로 칠함) | R-PHY-02 |
| Equipment | WorldEntity | 캐릭터가 손에 든 무기·도구 | **클래스 2** | R-ATT-01 |
| GroundedObject | WorldEntity | 바닥에 놓이는 고정물 (상자, 문, 가구) | **클래스 3** | R-PHY-03 |
| WorldStructure | WorldElement | 게임 세계의 구조물 | 추상 | — |
| Terrain | WorldStructure | 충돌하는 고체 블록 (바닥, 벽, 천장) | **클래스 4** | R-PHY-01~03, R-RND-01 |
| Ground / Wall / Ceiling | Terrain | 지형의 부위 | 칠하지 않음 (공간 관계로 구분) | — |
| Platform | WorldStructure | 아래에서 통과 가능한 얇은 발판 | **클래스 5** | R-PHY-01 (제외), R-PHY-03 (지지) |
| ForegroundDecoration | WorldStructure | 캐릭터 앞에 그려지는 장식 (전경 풀숲, 기둥) | **클래스 6** | R-IND-01, R-PHY-03, R-RND-01 (판정 보류·제외) |
| Background | WorldStructure | 하늘, 원경, 배경 벽 | 칠하지 않음 | R-PHY-01, 02 (제외) |
| Liquid | WorldStructure | 물, 용암 | 칠하지 않음 | R-PHY-01 (제외) |
| UIElement | ScreenElement | 화면에 그려지는 UI | 추상 | — |
| WorldUI | UIElement | 게임 세계 위치를 따라다니는 UI | 추상 | — |
| WorldIndicator | WorldUI | 특정 개체를 가리키는 UI | 추상 | R-IND-01~03 |
| HealthBar | WorldIndicator | 개체 머리 위 체력바 | **클래스 7** | R-IND-01~03 |
| Nameplate | WorldIndicator | 개체 이름표 | v0 칠하지 않음 (대상 게임에 있으면 추가) | R-IND-01~03 |
| TargetMarker | WorldIndicator | 조준·잠금 표시 | v0 칠하지 않음 (대상 게임에 있으면 추가) | R-IND-01~03 |
| WorldText | WorldUI | 데미지 숫자 등 개체를 따라다니는 텍스트 | 칠하지 않음 | R-UI-02 (제외) |
| ScreenUI | UIElement | 화면에 고정된 UI | 추상 | — |
| HUDElement | ScreenUI | 체력, 점수, 미니맵, 아이콘 등 HUD 구성 요소 | **클래스 8** | R-UI-01 |
| HUDHealth / ScoreDisplay / Minimap 등 | HUDElement | HUD 요소의 역할 | 칠하지 않음 (게임 매핑으로 지정) | represents (매핑 선언) |
| UIPanel | ScreenUI | 텍스트를 담는 상자 (대화창, 메뉴 창) | **클래스 9** | R-UI-02 |
| Popup | UIPanel | 툴팁, 알림창 | (UIPanel로 칠함) | R-UI-01 (제외) |
| TextLabel | ScreenUI | 화면 고정 UI 안의 글자 | **클래스 10** | R-UI-02 |
| Screen | — | 이미지 경계 자체 | 칠하지 않음 (이미지 크기로 계산) | R-UI-02 |

### 6-3. 계층 구조

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

### 6-4. 계층에서 확인할 것 (OWL 작성 시)

- R-IND-01~03은 `WorldIndicator`에 건다. 그러면 Nameplate, TargetMarker를 나중에 클래스로 추가해도 규칙을 다시 쓰지 않는다. 온톨로지 효과 검증(11월 4주)의 예시로 쓸 수 있다.
- R-PHY-02는 `LooseObject`에 건다. 하위 개념인 Item과 Projectile에 자동 적용된다.
- `Terrain`과 `Platform`은 형제 개념이다. R-PHY-01은 `Terrain`에만 걸리므로 발판 통과는 위반이 아니고, R-PHY-03의 지지 대상은 두 개념을 모두 허용한다.
- `Popup`이 `UIPanel` 아래, `HUDElement` 밖에 있으므로 R-UI-01이 팝업에 적용되지 않는다.

---

## 7. 관계 정의 (표 4)

| 관계 | 정의역 → 치역 | 정의 | 사용 규칙 | 얻는 방법 |
|---|---|---|---|---|
| represents | WorldIndicator → WorldEntity, HUDElement → WorldEntity | UI가 그 개체의 상태를 나타냄 | R-IND-01~03 | 라벨링 태깅(정답) / 추론 시 거리 기반 1:1 할당 / HUD는 게임 매핑에서 선언 |
| near | WorldIndicator → WorldEntity | 지시 UI 하단 중심과 대상 bbox 상단 중심 사이 거리 / 대상 bbox 높이 | R-IND-01, 02, 03 | C 계산 |
| overlaps | WorldEntity → Terrain, HUDElement → HUDElement | area(A∩B) / area(A) (지형은 가려진 부분을 추정한 마스크 사용). HUD끼리는 area(A∩B) / min(area(A), area(B)) | R-PHY-01, 02, R-UI-01 | C 계산 |
| contains | UIPanel → TextLabel, Screen → TextLabel, HUDElement → HUDElement | area(A∩B) / area(B) (B가 A 안에 들어간 비율) + B가 A 경계선에 닿는지 | R-UI-01, 02 | C 계산 |
| supportedBy | GroundedObject → Terrain, Platform | 오브젝트 하단과 바로 아래 지형·발판 상단 사이 수직 간격 / 오브젝트 높이 | R-PHY-03 | C 계산 |
| occludes | Terrain → Character | 캐릭터 경계 중 지형과 맞닿은 비율, 캐릭터 가시 면적 / 기대 면적 | R-RND-01 | C 계산 (측정 방식 확정 필요) |
| attachedTo | Equipment → Character | 장비 마스크와 가장 가까운 캐릭터 마스크 사이 최소 경계 거리 / 캐릭터 bbox 높이 | R-ATT-01 | 라벨링 태깅(정답) / C 계산 |

라벨링 도구에서 사람이 태깅해야 하는 관계는 `represents`(HealthBar → Character)와 `attachedTo`(Equipment → Character) 두 개다. 나머지는 모두 마스크에서 계산한다.

---

## 8. 다른 담당자에게 넘길 것

**→ C (공간 관계 정의서·JSON 스키마)**
- 거리 계열 측정값은 모두 **대상 bbox 높이로 정규화**한 값도 함께 출력
- 지형 마스크의 **가려진 부분 추정**(구멍 메우기) 후처리 필요 (R-PHY-01, 02)
- 가림 측정 방식(R-RND-01) 확정 필요: 지형 접촉 경계 비율, 가시 면적 비
- 지시 UI × 대상의 **1:1 할당 결과**와 거리 행렬 출력 (R-IND-03)
- 텍스트 마스크가 패널 경계선에 닿는지 여부 (R-UI-02)
- JSON의 `class` 값은 6장 기준 라벨링 클래스 이름 11개를 그대로 사용 (Character, LooseObject, Equipment, GroundedObject, Terrain, Platform, ForegroundDecoration, HealthBar, HUDElement, UIPanel, TextLabel)

**→ B (클래스 목록·라벨링 가이드)**
- `labeling_guide_v0.md` 전달 (클래스 11개, 클래스별 포함·제외 기준, 관계 태깅 2종)

---

## 9. 부록

`truelove2021_relational_bug_cases.csv`: 데이터셋에서 관련 범주(Information, UI, Bounds, Collision, Persistence, Position, Graphics) 중 2D 게임 전체 사례와 관계형 키워드(health bar, clip, sink, overlap, off-screen, float, behind 등) 포함 사례를 추린 983건 (2D 게임 349건을 위로 정렬). 근거 사례를 더 찾을 때 사용.

`labeling_guide_v0.md`: 클래스 목록 v0와 라벨링 가이드 (B 및 라벨링 참여자 전달용). 6장 개념 계층의 "라벨링 클래스" 열에서 나온 문서.
