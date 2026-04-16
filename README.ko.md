# skill-doctor

스킬·UP 진단 엔진. **8대 병리 × 4원인 = 32셀 매트릭스** 기반.

## 무엇을 하는가

스킬 1개 또는 UP 문서를 스캔하여 다음을 보고:
- **32셀 매트릭스** 점수 (각 셀 = 병리 × 원인)
- **레드플래그 Top 3** + 근거
- **트리아지 처방** (P0 / P1 / P2) → skill-builder 핸드오프

## 8대 병리

1. 느림(Latency)
2. 부정확(Inaccuracy)
3. 불통(Opacity)
4. 취약(Fragility)
5. 비대(Bloat)
6. 고립(Isolation)
7. 진화불능(Rigidity)
8. 무자각(Meta-Blindness)

UP 모드: ⑤~⑧ ×3 가중치 자동 적용.

## 3 모드

| 모드 | 용도 |
|---|---|
| 진단(Diagnose) | 대상 1개 → 전체 32셀 리포트 |
| 처방(Prescribe) | 트리아지 + skill-builder 핸드오프 |
| 모니터(Monitor) | 전체 스킬 생태계 스캔 → 대시보드 |

## 설치

`skill-doctor.skill` 파일을 Cowork 스킬 폴더에 설치.

## 트리거

`스킬닥터`, `skill doctor`, `스킬진단`, `UP진단`, `스킬검진`, `스킬감사`, `32셀매트릭스`, `8대병리`.

---

English README: [README.md](./README.md)
