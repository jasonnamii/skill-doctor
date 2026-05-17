# 9-rules-audit.md — skill-doctor 9룰 갭 진단 체크리스트

41셀 매트릭스의 9룰 축. 32셀(8병리×4원인)과 별도로 측정.

## 7강제룰 (FAIL 처리)

| # | 룰 | grep 패턴 | FAIL 기준 | WARN 기준 |
|---|---|---|---|---|
| 1 | Skill Boundaries | `^## (Skill )?Boundaries` | 섹션 누락 | 섹션 있으나 "안 하는 것" 빠짐 |
| 2 | When to Use | `^## When to Use\|언제 (쓰\|발동)` | 섹션 누락 | P2 동사만 있고 시나리오 ≤1 |
| 3 | Prerequisites | `^## Prerequisites\|시작 전 체크` | 섹션 누락 | 표 없이 자연어만 |
| 4 | Output Path | `^## Output Path\|산출물.*경로` | 누락 | 추상 표현만 (".md로") |
| 5 | Reference Index | references/ 존재 AND `^## Reference Index` | references/ 있는데 표 없음 | 표 있으나 "언제" 컬럼 없음 |
| 6 | Next Phase | `^## Next Phase\|다음엔 →\|이어지는` | 누락 | 추천 ≤1개 |
| 7 | Failure Modes/Gotchas | `^## (Failure Modes\|Gotchas)\|함정` | 누락 | 항목 ≤3개 |

## 2선택룰 (WARN/INFO)

| # | 룰 | 체크 | WARN | INFO |
|---|---|---|---|---|
| 8 | description 첫문장 평문 | description.split('.')[0]에 압축어(N층·N도메인·N모드 등) | 압축어만 | 평문 OK |
| 9 | metadata 블록 | `^metadata:` + `author:` + `version:` | metadata 있으나 키 누락 | 전체 누락 |

## 점수 가중

- 7강제룰: 각 10점 × 7 = 70점
- 2선택룰: 각 5점 × 2 = 10점
- 32셀 비중과 합산: 9룰 80점 × 0.3 + 32셀 점수 × 0.7

## 처방 우선순위

9룰 FAIL → 32셀 FAIL 순. 9룰은 구성 결함이라 32셀 처방 전 먼저 해결해야 32셀 처방이 정확해짐.

handoff.json 슬롯:
```json
{
  "target": "skill-name",
  "nine_rules_gaps": ["Boundaries", "Prerequisites"],
  "cell_gaps": ["[3-1] 스텔스실패"],
  "priority": "nine_rules_first"
}
```
