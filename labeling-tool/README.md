# AI 라벨링 도구

- `labeling_guide_v0.md`: 클래스 목록, 라벨링 가이드
- 초기 라벨링: 자체 도구 전까지 Label Studio 사용
  - `from_label_studio.py`: Label Studio JSON 내보내기를 라벨 파일(`schemas/label.schema.json`)로 변환
  - 설치: [환경 세팅](../README.md#환경-세팅-방법) 후 `pip install label-studio`, `pip install -r labeling-tool/requirements.txt`
  - 실행: `label-studio start` 후 브라우저에서 프로젝트 생성
    - 라벨링 설정: `python -m game_qa.labeling_tool.from_label_studio --config` 출력을 붙여넣기
    - 이미지 가져오기, 라벨링 후 JSON 형식으로 내보내기
  - 영역: polygon
    - 겹치는 영역(가이드 2-3)은 안쪽부터 그림. 기존 영역 안을 클릭하면 그 영역이 선택됨
  - 관계: 주체 영역 → 대상 영역 방향으로 연결
    - represents, attachedTo: 가이드 6장
    - sameInstance: 떨어진 조각을 한 인스턴스로 (가이드 2-2)
    - 관계 종류는 고르지 않아도 됨 (주체·대상 클래스로 정해짐)
  - 변환: `python -m game_qa.labeling_tool.from_label_studio <내보낸 JSON> <출력 라벨.json>`
- 엔진 추출: 엔진 접근이 가능한 게임은 Unity 에디터에서 라벨 추출 (결정기록 2026-11-26)
  - `unity/Editor/`: 추출 스크립트. 게임 프로젝트의 `Assets/` 아래에 복사
    - `GameQaCapture.cs`: 한 프레임 안에서 원본 화면, 월드 인스턴스 ID 렌더, 화면 UI 단위 마스크, 관계 출력
    - `CorgiMapping.cs`: Corgi Engine 매핑 (`IMapping` 구현). 다른 게임은 매핑만 새로 작성
    - `CorgiBatch.cs`: 일괄 추출
  - 실행 (플레이 모드)
    - 한 프레임: 메뉴 GameQA > 현재 프레임 추출, 또는 `GameQa.Extract.CorgiCapture.Run(<출력 폴더>)`
    - 일괄: `GameQa.Extract.CorgiBatch.Start(<장면 경로 목록>, <출력 루트>, <장면당 프레임 수>)`. 진행 상황 `CorgiBatch.Status`
      - 장면을 차례로 불러와 레벨 경계 안 빈 공간에 플레이어를 놓고 바닥에 붙인 뒤 추출
      - 정상 화면만: 착지·생존·고체 지형과 비겹침일 때만 추출. 결과와 건너뛴 이유는 `<출력 루트>/batch.json`
      - 체력바가 없는 적에 `MMHealthBar`를 실행 중 부착 (씬 파일은 그대로)
      - 추출 폴더 이름: `<게임>_<장면>_<번호>`
  - 조립: `python -m game_qa.labeling_tool.from_engine <출력 라벨.json> <이미지 폴더> <추출 폴더 또는 일괄 출력 루트 ...>`
    - 이미지는 `<추출 폴더 이름>.png`로 복사, 라벨은 파일 하나
    - 매핑되지 않은 화면 UI가 있는 폴더는 경고
  - 추출 폴더
    - `frame.png`: 원본 화면 (학습 입력)
    - `ids_world.png`: 월드 인스턴스 ID 색. 그리기 순서 그대로라 가려진 부분은 칠해지지 않음 (가이드 2-1)
    - `ui_<n>.png`, `ui_occluder.png`: 화면 UI 단위 마스크, 화면 UI 전체
    - `meta.json`: 인스턴스(id, ID 색, 클래스, 엔진 오브젝트 경로), UI 단위, 관계, 매핑되지 않은 화면 UI(`unmapped`)
  - ID 렌더: 알파 0.5 미만은 버리고 단색. 카메라 효과·MSAA·HDR은 끔. ID 색의 B 채널은 검사값이라 섞인 픽셀은 meta에 없는 색이 되어 배경 처리
    - 칠하지 않는 렌더러는 배경 색으로 그려 뒤를 가림. 뒤가 비치는 효과(매핑의 `SeeThrough`)는 그리지 않음
  - Corgi 매핑 (가이드 기준)

    | 클래스 | 엔진 기준 |
    |---|---|
    | Character | `Character` |
    | Equipment | `Weapon` (캐릭터보다 우선) |
    | LooseObject | `PickableItem`, `ItemPicker` |
    | Terrain | 렌더러 또는 부모의 콜라이더가 플레이어 `CorgiController.PlatformMask` 레이어. 트리거는 `Physics2D.queriesHitTriggers`일 때 포함 (컨트롤러가 레이캐스트로 충돌 판정). 계단 포함 |
    | Platform | 위 중 일방 통과 마스크(OneWay, MovingOneWay, MidHeightOneWay) 레이어 |
    | HealthBar | `MMHealthBar`가 만든 체력바 |
    | HUDElement | `MMProgressBar`, `InventoryDisplay` 단위. 기능 컴포넌트가 없는 묶음은 이름으로 지정 (Retro 데모: 아바타) |
    | TextLabel | `Text` 컴포넌트 하나 |
    | 칠하지 않음 | 라인 렌더러, 조준 표시(`WeaponAim` 레티클), 그 외 렌더러 (배경, 장식, 사다리, 물, 가시 등) |
    | 칠하지 않고 가리지도 않음 | 파티클·트레일 렌더러 (반투명 효과) |

    - 관계: attachedTo는 `Weapon.Owner`, represents는 `MMHealthBar`가 붙은 `Character`
  - 한계
    - 무기 그림이 캐릭터 스프라이트에 합쳐진 경우(Retro 데모 적의 총) Equipment로 분리 불가
    - 캐릭터 아래의 공격 이펙트 스프라이트(예: 칼 궤적)는 보이는 순간 Character로 칠해짐
    - GroundedObject, ForegroundDecoration, UIPanel은 매핑 없음
    - 콜라이더 없는 장식 그림은 겉모습이 아이템·발판이어도 칠하지 않음 (엔진 기준)
- 테스트: `pytest labeling-tool`
