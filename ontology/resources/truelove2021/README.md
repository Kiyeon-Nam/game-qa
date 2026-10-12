# Truelove 2021 업데이트 노트 버그 데이터셋

- 출처: Truelove et al., "We'll Fix It in Post", ICSE 2021. 표 II 분류 체계와 공개 데이터셋(`github.com/truelova/ICSE_2021_UpdateNotes`, 버그 수정 12,122건)
- 자료: `cases.csv`. 원본에서 추출한 983건
  - 열: Bug Fix, Game, Update Date, Update ID, Category, is_2D

## 추출 기준

- 대상 범주: Information, UI, Bounds, Collision, Persistence, Position, Graphics (아래 범주별 분석에서 단일 화면·관계가 모두 O 또는 △인 범주)
- 대상 범주 중 2D 게임 전체 사례와 관계형 키워드(health bar, clip, sink, overlap, off-screen, float, behind 등) 포함 사례
- 2D 게임 349건을 위로 정렬

## 데이터 특성

- 30개 게임 중 2D 게임은 Terraria(511건), Brawlhalla(75건)뿐. 두 게임을 우선 근거로 쓰고, 나머지 게임 사례는 2D 플랫포머 상황으로 바꿔 해석

## 범주별 분석 (표 II, 20개 범주)

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
