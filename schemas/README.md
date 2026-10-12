# schemas

구성 요소 간 JSON 형식

| 형식 | 정의 | 예시 | 파이프라인 위치 |
|---|---|---|---|
| 라벨 | [label.schema.json](label.schema.json) | [examples/label.json](examples/label.json) | 구축 루프 ① 라벨링 → ② 데이터셋, 사전 라벨링 |

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
