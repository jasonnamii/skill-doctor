# UP-Specific Diagnostic Rules

UP(User Preferences) 진단 시 추가 적용 규칙. UP은 일반 스킬과 다음 점에서 구조적으로 다름:

1. **상시 로드**: 매 턴 컨텍스트에 주입됨 (스킬은 트리거 시에만)
2. **최상위 규칙**: 모든 스킬이 UP을 우선해야 함 (SKILL_PRECEDENCE)
3. **INVARIANT 존재**: 본질 기능 보호 규칙 (HONORIFIC, OVERWRITE_BAN 등)
4. **버전 진화**: v35.16 등 빠른 반복 — 하위호환이 곧 사용자 경험

→ 8대 병리 중 **⑤ 비대·⑥ 고립·⑦ 진화불능·⑧ 무자각** 가중치 ×3.

---

## UP 진단 활성화 조건

대상 경로가 다음에 해당하면 UP 모드:

- `~/.claude/CLAUDE.md` (사용자 홈)
- `/sessions/{session}/mnt/.claude/skills/up-manager/` (UP 관리 스킬의 관리 대상)
- 파일 내용에 `M1. FRAME`, `M2. FAST_LANE`, `BEDROCK`, `CONFIDENCE` 등 UP 시그니처 포함

---

## UP 특화 체크 (32셀 보완)

### ⑤ 비대 — 가중치 ×3

**상시 로드 특성으로 1KB 증가도 크리티컬.**

| 원인 | UP 판정 기준 |
|------|------------|
| 5-1 토큰 폭식 | UP 전체 크기 >30KB → 🔴 / 20-30KB → 🟠 / ≤20KB → 🟢 |
| 5-2 로딩 비효율 | 티어 분리 없음 → 🔴 / T1/T2/T3 구분 명시 → 🟢 |
| 5-3 맥락 오염 | STEALTH 규칙 부재 또는 위반 → 🔴 |
| 5-4 중복 로딩 | 모듈 간 규칙 중복 → 🟠 |

### ⑥ 고립 — 가중치 ×3

**UP은 모든 스킬의 상위 계층 → 스킬 생태계 충돌 가능성.**

| 원인 | UP 판정 기준 |
|------|------------|
| 6-1 cascade 단절 | 스킬 발동 가이드 부재 → 🟠 (UP은 범용이라 🔴 아님) |
| 6-2 트리거 충돌 | 스킬 P1과 UP 키워드 충돌 (예: "확인") → 🟠 |
| 6-3 UP 불화 | **M7.SKILL_PRECEDENCE 명시 여부** → 없으면 🔴 |
| 6-4 의존 사이클 | UP이 특정 스킬 강제 호출 → 🔴 |

### ⑦ 진화불능 — 가중치 ×3

**UP은 수정 빈도 높음 → 하위호환 필수.**

| 원인 | UP 판정 기준 |
|------|------------|
| 7-1 하위호환 붕괴 | 버전 스트링 (v35.x) → 없으면 🔴 |
| 7-2 본질 유실 | **INVARIANT_GUARD 존재 여부** → 없으면 🔴 |
| 7-3 테스트 부재 | up-manager 스킬과의 QC 연계 → 없으면 🟠 |
| 7-4 버전관리 부재 | CHANGELOG 존재 → 없으면 🔴 |

### ⑧ 무자각 — 가중치 ×3

**UP 자체가 상시 작동 → 자기진단 필수.**

| 원인 | UP 판정 기준 |
|------|------------|
| 8-1 자기진단 불가 | UP_RESET 프로토콜 존재 여부 |
| 8-2 실패 침묵 | FRAME 붕괴·WEIGHT 오판 감지 규칙 |
| 8-3 개선 신호 부재 | 사용자 지적 수용 메커니즘 |
| 8-4 학습 축적 부재 | UP 체크리스트 동기화 언급 |

---

## UP INVARIANT 필수 체크리스트

UP 진단 시 다음 INVARIANT가 보호되는지 확인. 하나라도 누락 → ⑦-2 본질유실 🔴.

| INVARIANT | 설명 | 찾는 위치 |
|-----------|------|----------|
| HONORIFIC | 존댓말 강제 | M3.DENSITY |
| OVERWRITE_BAN | Write 전체 덮어쓰기 금지 | M7.EDIT4 |
| PATTERN_GUARD | 환각 방지 | M5.CONFIDENCE |
| STEALTH | 내부 용어 노출 금지 | M2.FAST_LANE |
| ERROR_CORRECTION | 정정 규칙 | M9 |
| MODE_GATES | 작업계획/핑퐁/리허설 게이트 | M12 |

---

## UP 버전 추적

UP은 v번호로 진화 — 진단 리포트에 버전 기록.

**추출 방법:**
```bash
grep -E "UP v[0-9]+\.[0-9]+" {up-file} | head -1
```

**예상 포맷:** `# UP v35.16 — Core`

### 버전별 진단 이력 누적

```
/sessions/{session}/mnt/outputs/up-monitoring/
├── up-v35.14_diagnosis.md
├── up-v35.15_diagnosis.md
└── up-v35.16_diagnosis.md
```

**트렌드 분석:**
- 버전별 총점 변화
- 수정된 모듈의 영향
- 신규 INVARIANT 도입

---

## UP 처방 시 주의사항

UP 처방은 스킬 처방보다 훨씬 신중해야 함:

1. **수정 = 사용자 경험 즉시 변경** — 모든 스킬에 영향
2. **INVARIANT 유지 필수** — 본질 기능 훼손 금지
3. **up-manager 경유** — 직접 편집 금지, 반드시 up-manager 스킬 발동
4. **버전 범프 필수** — 모든 수정은 v번호 증가
5. **CHANGELOG 기록** — 무엇이 왜 바뀌었는지

**skill-doctor → up-manager 핸드오프:**

```json
{
  "source": "skill-doctor",
  "target": "UP",
  "current_version": "v35.16",
  "proposed_version": "v35.17",
  "changes": [
    {"module": "M2.FAST_LANE", "cell": "8-1", "action": "self-check 프로토콜 추가"}
  ],
  "preserve_invariants": ["HONORIFIC", "OVERWRITE_BAN", "PATTERN_GUARD", "STEALTH"]
}
```

---

## Gotchas

- **UP에 스킬 기준 그대로 적용 = FAIL.** 가중치 ×3 필수
- **INVARIANT 체크 누락** → 본질 기능 훼손 위험. 6개 전부 확인
- **버전 없는 UP 진단** → 트렌드 추적 불가. 최소한 현재 버전 기록
- **UP 직접 수정 지시** → skill-doctor 월권. 반드시 up-manager 위임
