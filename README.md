# game-qa

딥러닝 세그멘테이션과 온톨로지를 결합한 게임 QA 자동 판정 시스템

2D 플랫포머 게임 화면을 세그멘테이션해서 화면 요소와 요소 사이의 관계를 뽑고, 온톨로지 규칙으로 버그 여부를 판정한다.

## 판정 파이프라인

```
입력(플레이 녹화/스크린샷)
 → ① 프레임 추출
 → ② 세그멘테이션          training/, inferlib/
 → ③ 후처리·공간 관계 계산  inferlib/
 → ④ 그래프 변환           oracle/
 → ⑤ 규칙 검증             oracle/ + ontology/
 → ⑥ 리포트 생성           oracle/
```

구성 요소 사이에 주고받는 JSON 형식은 `schemas/`에 정의한다.

## 폴더 구조

```
game-qa/
├── docs/               설계 문서
│   ├── ontology_v0.md                         온톨로지 v0: 버그 유형, 규칙, 개념 계층, 관계 정의
│   ├── labeling_guide_v0.md                   클래스 목록 v0, 라벨링 가이드
│   └── truelove2021_relational_bug_cases.csv  규칙 근거로 쓴 버그 사례 (Truelove et al., ICSE 2021)
├── ontology/           게임 UI 온톨로지: 개념, 관계, 규칙 정의
├── oracle/             판정기: 그래프 변환, 규칙 검증, 판정 리포트
├── training/           세그멘테이션 모델과 학습 파이프라인
├── labeling-tool/      AI 라벨링 도구
├── inferlib/           C++ 추론 라이브러리
│   ├── cpp/            C++ 구현
│   ├── python_ref/     후처리 Python 구현 (C++ 구현의 정답지)
│   └── bindings/       Python 바인딩
├── schemas/            구성 요소 간 JSON 형식
└── data/               데이터셋
    └── labels/         라벨 (COCO instance segmentation + relations)
```

## 규칙

- **데이터**: `data/` 아래의 이미지·영상 원본은 커밋하지 않는다(`.gitignore`). 라벨 JSON과 게임별 `notes.md`만 커밋한다.
- **모델 가중치**: `*.pt`, `*.onnx` 같은 가중치와 학습 로그(`runs/`, `wandb/`)도 커밋하지 않는다.
- **브랜치**: `main`에 직접 push할 수 없다. `feat/`, `docs/`, `chore/` 같은 브랜치에서 작업하고 PR로 머지한다.
