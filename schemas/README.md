# schemas

구성 요소 간 JSON 형식

| 형식 | 정의 | 예시 | 파이프라인 위치 |
|---|---|---|---|
| 라벨 | [label.schema.json](label.schema.json) | [examples/label.json](examples/label.json) | 구축 루프 ① 라벨링 → ② 데이터셋, 사전 라벨링 |
| 추론 결과 | [inference.schema.json](inference.schema.json) | [examples/inference.json](examples/inference.json) | 판정 파이프라인 ③ 후처리·공간 관계 계산 → ④ 그래프 변환 |

## 라벨

[COCO instance segmentation](https://cocodataset.org/#format-data) 형식에 `relations` 추가. 명시하지 않은 내용은 COCO 표준

| 항목 | 내용 |
|---|---|
| `images` | 이미지 파일 목록 |
| `annotations` | 인스턴스(칠한 영역 하나) 목록. 이미지, 클래스, 마스크 |
| `categories` | 클래스 목록. id·name은 [라벨링 클래스](../ontology/2_concepts.md#조합-개념과-라벨링-클래스)의 ID·이름 |
| `relations` | 인스턴스 사이 관계 목록. 라벨링할 때 사람이 지정하는 관계(represents, attachedTo)만 포함 |

- 인스턴스끼리 겹칠 수 있음 (UI 안의 UI)
- 관계의 `subject`, `object`는 같은 이미지 안의 annotation id. 연결 가능한 클래스는 [관계 정의](../ontology/3_relations.md#관계) 참고 (예: attachedTo는 Equipment → Character)

## 추론 결과

프레임 하나의 인식 결과와 관계·측정값. 임계값 비교는 하지 않음

| 항목 | 내용 |
|---|---|
| `frame` | 입력 파일과 프레임 번호, 이미지 크기 |
| `instances` | 인스턴스 목록. 클래스, 모델 신뢰도, 마스크(COCO RLE) |
| `relations` | [관계](../ontology/3_relations.md#관계) 목록. 게임별 매핑에서 선언하는 관계는 제외 |
| `measurements` | [측정값](../ontology/3_relations.md#측정값) 목록. `args`는 측정값 정의의 인자 순서 |

- `class`: [라벨링 클래스](../ontology/2_concepts.md#조합-개념과-라벨링-클래스) 이름
- `score`: 오판이 인식 오류인지 규칙 문제인지 구분하는 데 사용
- `ScreenBounds`: 인스턴스 id 대신 문자열 `"ScreenBounds"`로 참조
- 측정값은 규칙이 쓰는 클래스 조합의 모든 쌍에 대해 출력. 빠진 쌍을 0으로 간주하지 않음
