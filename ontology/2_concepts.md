# 개념 계층

② 개념 계층 정의. [도출 절차](README.md#도출-절차) 5(② 개념 계층)

## 축

| 축 | 구분하는 성질 | 값 |
|---|---|---|
| 역할 | 화면 요소가 무엇인가 | Entity (Character, Object), Structure, Display (HealthDisplay), Panel, Text |
| 배치 | 게임 세계 위치를 따라가는가 | World, ScreenFixed |
| 충돌성 | 캐릭터와 어떻게 충돌하는가 | Solid, OneWay |
| 지지 방식 | 무엇이 붙잡고 있는가 | Grounded, Attached, Free |
| 그리기 층 | 캐릭터보다 앞에 그려지는가 | Foreground |

축 밖의 특수 개념: ScreenBounds (이미지 경계)

## 개념 정의

| 축 | 개념 | 상위 | 정의 | 도입 근거 |
|---|---|---|---|---|
| 역할 | Entity | | 게임 세계 안의 개별 개체 | R-001 (표시의 대상이 캐릭터와 물건 모두) |
| 역할 | Character | Entity | 게임 세계에서 스스로 움직이거나 조작되는 행위 주체 (플레이어가 조작하는 대상, 적, NPC, 소환수 등). 탈것에 탄 경우 탈것 포함. 제외: 배경 그림 속 인물 | R-004 |
| 역할 | Object | Entity | 캐릭터가 아닌 개별 물건 (아이템, 투사체, 장비, 상자·문·가구 등) | R-005 |
| 역할 | Structure | | 게임 세계의 지형·구조물. 제외: 하늘, 원경 | R-004 |
| 역할 | Display | | 정보를 나타내는 표시 (체력, 이름, 점수, 미니맵, 아이콘 등) | R-001 |
| 역할 | HealthDisplay | Display | 체력 표시 | R-003 (같은 종류의 표시 구분) |
| 역할 | Panel | | 텍스트를 담는 상자 (대화창, 메뉴 창, 툴팁, 팝업) | R-010 |
| 역할 | Text | | 글자 덩어리 | R-010 |
| 배치 | World | | 게임 세계 위치를 따라 움직임 | R-001 |
| 배치 | ScreenFixed | | 화면에 고정 | R-001 반례 (화면 고정 보스 체력바) |
| 충돌성 | Solid | | 캐릭터가 밟거나 부딪힘. 제외: 배경 벽, 액체 | R-004 |
| 충돌성 | OneWay | | 아래에서 통과하고 위에서 밟음 | R-004 반례 (통과 가능한 발판) |
| 지지 방식 | Grounded | | 바닥에 놓여 있어야 정상. 제외: 벽·천장 부착물 | R-006 |
| 지지 방식 | Attached | | 다른 개체에 붙어 있음 (손에 든 장비) | R-008 |
| 지지 방식 | Free | | 떠 있거나 움직여도 정상 (아이템, 투사체, 던진 무기) | R-006 반례 (떠서 흔들리는 코인) |
| 그리기 층 | Foreground | | 캐릭터보다 앞에 그려짐. 제외: 캐릭터 뒤에 그려지는 장식 | R-007 반례 (전경 풀숲) |
| 특수 | ScreenBounds | | 이미지 경계 | R-010 |

## 조합 개념과 라벨링 클래스

- 라벨링 클래스는 규칙이 구분해야 하는 축 값의 조합
- 규칙이 구분하지 않는 하위 의미(HUD 요소가 체력인지 점수인지 등)는 칠하지 않고 게임별 매핑에서 지정

| ID | 조합 | 정의 |
|---|---|---|
| 0 | Character | Character |
| 1 | LooseObject | Object ∧ Free |
| 2 | Equipment | Object ∧ Attached |
| 3 | GroundedObject | Object ∧ Grounded |
| 4 | Terrain | Structure ∧ Solid |
| 5 | Platform | Structure ∧ OneWay |
| 6 | ForegroundDecoration | Structure ∧ Foreground |
| 7 | HealthBar | HealthDisplay ∧ World |
| 8 | HUDElement | Display ∧ ScreenFixed |
| 9 | UIPanel | Panel ∧ ScreenFixed |
| 10 | TextLabel | Text ∧ ScreenFixed |

- Text ∧ World(캐릭터를 따라다니는 데미지 숫자 등)는 쓰는 규칙이 없어 라벨링하지 않음
