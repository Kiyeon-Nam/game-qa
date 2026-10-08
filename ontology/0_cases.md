# 버그 유형

> **출처**: Truelove et al., "We'll Fix It in Post", ICSE 2021 — 표 II 분류 체계 + 공개 데이터셋(`github.com/truelova/ICSE_2021_UpdateNotes`, 버그 수정 12,122건)
> **선정 조건**: ① 단일 화면으로 판별 가능 ② 화면 요소 간 관계 오류 ③ 2D 플랫포머에서 발생 가능
> **사례 자료**: `resources/truelove2021_relational_bug_cases.csv`. 데이터셋에서 관련 범주(Information, UI, Bounds, Collision, Persistence, Position, Graphics) 중 2D 게임 전체 사례와 관계형 키워드(health bar, clip, sink, overlap, off-screen, float, behind 등) 포함 사례를 추린 983건 (2D 게임 349건을 위로 정렬)
> **데이터 참고**: 데이터셋 30개 게임 중 2D 게임은 Terraria(511건)와 Brawlhalla(75건)뿐이라, 이 두 게임을 우선 근거로 쓰고 나머지 게임 사례는 2D 플랫포머 상황으로 바꿔 해석함

## 버그 범주 분류 (Truelove 표 II, 20개 범주)

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

## 버그 유형 후보 (14개: 채택 10 / 제외 4)

### 채택

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

### 채택 (적용 조건 있음)

| ID | 버그 유형 | 화면에서 어떻게 보이나 | 논문 범주 | 단일 화면 | 관계 오류 | 데이터셋 근거 사례 | 적용 조건 |
|---|---|---|---|---|---|---|---|
| **B08** | 고정 오브젝트 부유 | 상자·문·가구 같은 고정 배치물이 지면에서 떠 있음 | Position of Object | △ | O (고정물 ↔ 지면 접촉) | Terraria: *"falling blocks floating in the air"*, pianos *"looked like they were floating"*, tiles *"drawing a few pixels too low"* | **지면 고정 개념에만 적용**. 코인·아이템은 원래 떠 있는 경우가 많고, 캐릭터는 점프와 구분 불가 → 개념 계층에 '지면 고정 오브젝트'를 별도 개념으로 둠 |
| **B09** | 레이어 순서 오류 | 적·캐릭터가 문이나 지형 뒤에 그려져 가려짐 | Game Graphics | O | O (캐릭터 ↔ 지형 가림) | Terraria: *"angry tumblers would visually draw behind doors and actuated blocks"*, pond would *"appear in front of"* pillars / Path of Exile: characters *"render behind track tiles"* | 가시 마스크만으로는 "가려짐"과 "파묻힘(B04)"이 비슷하게 보임 → 가림 측정 방법을 공간 관계 정의서에 반영 필요 |
| **B10** | 장비 스프라이트 분리 | 무기·장비가 캐릭터 손에서 떨어져 떠 있음 | Position of Object | O | O (장비 ↔ 캐릭터 부착) | Terraria: *"betsy's wrath would hover outside of the player's hand"*, *"keybrand wasn't actually in your hand"*, backpacks *"drew at incorrect heights"* | 장비를 별도 라벨링 클래스로 추가 → 클래스 목록 v0에 반영, 라벨링 가이드에 "손에 든 장비는 캐릭터와 분리해 칠함" 명시 |

### 제외 (범위 설명·향후 과제용으로 보존)

| ID | 버그 유형 | 화면에서 어떻게 보이나 | 논문 범주 | 제외 이유 | 데이터셋 근거 사례 |
|---|---|---|---|---|---|
| **B11** | 캐릭터 공중 정지 | 캐릭터가 발판 없이 공중에 떠 있음 | Position of Object | 단일 프레임으로 점프·낙하와 구분 불가 → 연속 프레임 필요 (3순위 확장 과제) | Black Desert: *"npc ... was floating in the air"* |
| **B12** | 맵 경계 이탈 | 캐릭터가 맵 바깥으로 떨어짐 | Bounds | 대부분 화면에 보이지 않음. 보이는 경우는 B04로 처리 | Terraria: *"tax collector fell out of the bottom of the map"* |
| **B13** | 닫힌 UI 잔류 | 인벤토리를 닫았는데 드래그하던 아이콘이 화면에 남음 | User Interface, Object Persistence | "인벤토리가 닫혔다"는 직전 상태 정보가 필요 | Rust: *"item icon staying on screen if inventory is closed while dragging"* |
| **B14** | 표시 값 오류 | 획득한 돈과 화면에 표시된 금액이 다름 | Value, Information | 실제 게임 내부 값(정답)이 필요하고 OCR이 필요 | Terraria: *"money displayed on screen was incorrect"* |

---

## 버그 → 규칙 대응

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
