# 데이터

데이터셋에 사용하는 게임과 데이터 구성

## 대상 게임

| 게임 | 코드 라이선스 | 에셋 라이선스 | 소스 공개 | 역할 |
|---|---|---|---|---|
| [Corgi Engine](https://assetstore.unity.com/packages/templates/systems/corgi-engine-2d-2-5d-platformer-26617) 데모 | Unity Asset Store EULA | Unity Asset Store EULA | 구매자만 | 학습용, 버그 주입용 |
| [SuperTux](https://github.com/SuperTux/supertux) | GPL-3.0 | CC-BY-SA 등 (파일별) | 공개 | 학습용 |
| [Open Surge](https://github.com/alemart/opensurge) | GPL-3.0 | CC-BY, CC0 등 (파일별) | 공개 | 학습용 |
| [Godot 2D Platformer Demo](https://github.com/godotengine/godot-demo-projects/tree/master/2d/platformer) | MIT | MIT | 공개 | 신규 적용용 후보 |
| [Unity 2D Game Kit](https://assetstore.unity.com/packages/slug/107098) | Unity Asset Store EULA | Unity Asset Store EULA | 공개 | 신규 적용용 후보 |

- 학습용: 세그멘테이션 학습 데이터
- 버그 주입용: 소스를 수정해 버그를 넣은 평가 데이터
- 신규 적용용: 학습·임계값 조정에 쓰지 않고 신규 게임 적용 효과 측정에 사용

## 폴더 구성

```
data/
└── labels/   라벨 (COCO instance segmentation + relations)
```
