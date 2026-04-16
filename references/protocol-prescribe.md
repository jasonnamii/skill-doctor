# Protocol: 처방 모드 (Prescribe)

진단 결과 → 수정 우선순위 + 구체적 액션 도출 → skill-builder 위임.

---

## 실행 순서

```
진단 리포트 로드 → 트리아지 → 액션 구체화 → 처방전 발행 → skill-builder 핸드오프
```

### 1. 진단 리포트 로드

```bash
# 최근 진단 리포트 탐색
ls -lt /sessions/{session}/mnt/outputs/*_diagnosis_*.md | head -3
```

**입력:**
- 최근 진단 리포트 (scan_result.json 또는 .md)
- 없으면 진단 모드 먼저 실행

### 2. 트리아지 (긴급 × 중요)

| 축 | 판정 기준 |
|----|----------|
| 긴급 | 🔴 FAIL 셀, 스킬 발동 차단 수준 |
| 중요 | 영향 범위 (발동 빈도 × 영향도) |

**4사분면 배치:**

```
     긴급↑
      │
  P1  │  P0    ← P0: 즉시 (긴급+중요)
──────┼──────
  P3  │  P2    ← P1: 단기 (긴급+덜중요)
      │         ← P2: 중장기 (덜긴급+중요)
     중요→     ← P3: 보류 (둘 다 낮음)
```

**우선순위 결정 규칙:**
- 🔴 + 발동 차단 = **P0** (24시간 내)
- 🔴 + 성능 저하 = **P1** (1주일 내)
- 🟠 + 영향 큼 = **P1**
- 🟠 + 영향 작음 = **P2** (1개월 내)
- 기타 = **P3** (백로그)

### 3. 액션 구체화

각 FAIL/WARN 셀마다 **구체적 수정 액션** 도출:

| 셀 | 문제 유형 | 표준 처방 액션 |
|----|----------|--------------|
| 1-1 흐름단절 | 순차 강요 | 병렬 허용 구간 명시, 허브스포크 재설계 |
| 2-1 오발동 | 일반 키워드 | P1에서 일반 키워드 제거, 도메인 특화로 교체 |
| 2-2 미발동 | 트리거 부족 | P1 5개 확보, P2 한/영 병기, P3 영어 용어 추가 |
| 3-1 스텔스 실패 | 내부 라벨 노출 | 응답 예시에서 내부 용어 제거, UP STEALTH 준수 |
| 3-3 피드백 부재 | Gotchas 빈약 | Gotchas 3행+ 추가, 실패 패턴·대응 병기 |
| 4-2 엣지케이스 | 입력 검증 없음 | PREFLIGHT 추가, 빈 입력·null 처리 |
| 5-1 토큰 폭식 | >10KB | references/ 분리, 허브 5KB 목표 |
| 5-2 로딩 비효율 | 본문에 상세 | 스포크로 이동, 포인터(→) 추가 |
| 6-1 cascade 단절 | NOT 라우팅 없음 | NOT에 `→대체스킬` 추가 |
| 6-2 트리거 충돌 | P1 겹침 | NOT 라우팅 추가 또는 P1 차별화 |
| 7-2 본질 유실 | 절대규칙 없음 | "절대 규칙" 섹션 추가, 5개 이내 |
| 7-3 테스트 부재 | evals/ 없음 | evals/ + 샘플 케이스 3개 |
| 8-1 자기진단 불가 | validate 없음 | scripts/validate.py 또는 self-check 단계 |

### 4. 처방전 발행

**포맷:**

```markdown
# 💊 skill-doctor 처방전

**대상:** {skill-name}
**진단 리포트:** {report-path}
**처방일:** 2026-04-17

## 트리아지 결과

| 우선순위 | 항목 수 | 예상 공수 |
|---------|--------|----------|
| P0 (즉시) | 2 | 35분 |
| P1 (단기) | 3 | 2시간 |
| P2 (중장기) | 2 | 3시간 |

## P0 처방 (즉시 실행)

### 1. [⑤-1 토큰폭식] SKILL.md 분리
- **현재:** 12.3KB (목표의 2.5배)
- **액션:**
  1. "실행 흐름" 섹션 → `references/execution-flow.md`로 이동
  2. "Gotchas" 섹션은 허브에 유지 (빠른 참조)
  3. 허브에 포인터 추가: `상세: → references/execution-flow.md`
- **예상 크기:** 4.8KB (목표 달성)
- **공수:** 30분
- **위임:** skill-builder 발동 → 경미/중간 경로

### 2. [②-2 미발동] P1 키워드 확장
- **현재:** 4개 (ruby, 러비, 러셀, 비트겐슈타인)
- **액션:** 다음 키워드 추가
  - 논리분해, decomposition, atomic analysis
- **최종:** 7개
- **공수:** 5분
- **위임:** skill-builder 발동 → 경미 경로

## P1 처방 (1주 내)

...

## 🔜 skill-builder 핸드오프

다음 명령으로 수정 착수:
```
"skill-builder 발동: {skill-name} P0 처방 실행"
```

handoff.json 생성:
- target: {skill-name}
- priority: P0
- actions: [액션 목록]
```

### 5. skill-builder 핸드오프

**handoff.json 생성:**

```json
{
  "source": "skill-doctor",
  "target_skill": "{skill-name}",
  "diagnosis_date": "2026-04-17",
  "priority": "P0",
  "actions": [
    {
      "cell": "5-1",
      "type": "split_references",
      "description": "SKILL.md > references/execution-flow.md 이동",
      "files": ["SKILL.md"]
    },
    {
      "cell": "2-2",
      "type": "trigger_update",
      "description": "P1 키워드 3개 추가",
      "target_field": "description.P1"
    }
  ]
}
```

**저장 경로:** `/sessions/{session}/skill-doctor/handoff-{timestamp}.json`

사용자가 "실행"·"착수" 시 skill-builder 발동.

---

## 처방 원칙

1. **최소 침습:** 32셀 모두 고치려 하지 말 것. P0·P1만 1차 수정.
2. **근거 명시:** 진단 리포트의 증거를 반드시 인용.
3. **공수 추정:** 각 액션에 예상 시간 (5분·30분·1시간·반나절 단위).
4. **롤백 경로:** 각 액션에 "실패 시 복원" 방법 병기.
5. **skill-builder 위임:** skill-doctor는 처방만, 실제 수정은 skill-builder 게이트키퍼.

---

## Gotchas

- **처방이 수정을 직접 수행 = FAIL.** 반드시 skill-builder 위임
- **P0 처방 3개+ = 너무 많음.** 1-2개로 압축
- **공수 추정 누락** = 사용자 판단 불가. 반드시 병기
- **handoff.json 없이 핸드오프** = skill-builder가 맥락 유실
