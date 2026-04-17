# Protocol: 진단 모드 (Diagnose)

스킬 1개 또는 UP → 32셀 매트릭스 검진 → 진단 리포트.

---

## 실행 순서

```
PREFLIGHT → 대상 확정 → Python 스캐너 → 수동 보완 → 리포트 생성
```

### 1. PREFLIGHT

```bash
TARGET={대상 경로}
echo "=== 대상 존재 ===" && ls -la $TARGET/SKILL.md
echo "=== 파일 목록 ===" && find $TARGET -type f -name "*.md" | head -20
echo "=== SKILL.md 크기 ===" && wc -c $TARGET/SKILL.md
```

**체크:**
- SKILL.md 존재 여부 (UP이면 UP 본체 파일 경로)
- references/ 디렉토리 존재 여부
- scripts/ 디렉토리 존재 여부

**실패 시:** STOP + 경로 확인 요청.

### 2. 대상 확정

| 대상 유형 | 경로 예시 |
|----------|----------|
| 일반 스킬 | `/sessions/{session}/mnt/.claude/skills/{skill-name}/` |
| UP 본체 | `~/.claude/CLAUDE.md` 또는 UP_manager가 지시한 경로 |
| 전체 스캔 | `/sessions/{session}/mnt/.claude/skills/` (→ 모니터 모드로 라우팅) |

**UP 대상이면** → `references/up-specific-rules.md` 자동 로드.

### 3. Python 스캐너 실행

```bash
cd /sessions/{session}
python skill-doctor/scripts/skill_scanner.py scan {TARGET} > scan_result.json
```

**출력 포맷:**
```json
{
  "target": "skill-name",
  "mode": "standard" | "up",
  "scan_date": "2026-04-17",
  "cells": {
    "1-1": {"status": "PASS", "evidence": "...", "score": 1.0},
    "1-2": {"status": "WARN", "evidence": "references 3개 동시 로드", "score": 0.5},
    ...
    "8-4": {"status": "FAIL", "evidence": "session-briefing 연계 없음", "score": 0.0}
  },
  "total_score": 72.5,
  "grade": "ORANGE"
}
```

### 4. 수동 보완

Python 스캐너가 놓치는 3가지:
1. **의도이탈 (2-3)**: description 동사 vs 본문 동사 — 의미 비교 필요
2. **UP 불화 (6-3)**: UP INVARIANT 준수 여부 — 문맥 해석
3. **본질 유실 (7-2)**: "절대 규칙"이 정말 본질인지 — 판단

**보완 절차:**
- SKILL.md 전체 Read
- 위 3셀만 수동 판정
- scan_result.json에 수동 결과 병합

### 5. 리포트 생성

```bash
python skill-doctor/scripts/report_generator.py \
  --scan-result scan_result.json \
  --target {skill-name} \
  --out /sessions/{session}/mnt/outputs/{skill-name}_diagnosis_{date}.md
```

**리포트 섹션:**
1. **헤더**: 대상·버전·일시·총점·등급
2. **8×4 매트릭스**: 이모지 시각화
3. **레드플래그 Top3**: 🔴 셀 중 영향도 순 3개
4. **트리아지**: 긴급×중요 2축 배치
5. **처방 우선순위**: P0(즉시)·P1(단기)·P2(중장기)
6. **처방 모드 위임**: "처방해줘" 발동 시 `protocol-prescribe.md`로 이관

### 6. 리포트 저장 + 공유

```bash
cp {report}.md /sessions/{session}/mnt/outputs/
```

사용자에게 `computer://` 링크로 공유.

---

## 출력 예시

```markdown
# 🩺 skill-doctor 진단 리포트

**대상:** ruby-skill
**모드:** standard
**일시:** 2026-04-17
**총점:** 🟠 74/100

## 8×4 매트릭스

|   | 원인1 | 원인2 | 원인3 | 원인4 |
|---|------|------|------|------|
| ① 느림     | 🟢 | 🟢 | 🟠 | 🟢 |
| ② 부정확   | 🟢 | 🔴 | 🟢 | 🟠 |
| ③ 불통     | 🟢 | 🟠 | 🟢 | 🟢 |
| ④ 취약     | 🟢 | 🟢 | 🟠 | 🟢 |
| ⑤ 비대     | 🔴 | 🟠 | 🟢 | 🟢 |
| ⑥ 고립     | 🟢 | 🟢 | 🟢 | 🟢 |
| ⑦ 진화불능 | 🟠 | 🟢 | 🔴 | 🟢 |
| ⑧ 무자각   | 🔴 | 🟠 | 🟠 | 🟢 |

## 🔴 레드플래그 Top3

1. **[⑤비대-토큰폭식]** SKILL.md 12.3KB — 목표 5KB의 2.5배. references/ 분리 필요.
   - 증거: `wc -c ruby-skill/SKILL.md` → 12,587 bytes
2. **[②부정확-미발동]** P1 키워드 4개 (최소 5개 미달)
   - 증거: frontmatter.description의 P1 카운트
3. **[⑦진화불능-테스트부재]** evals/ 없음, 자체 점검 프로토콜 부재
   - 증거: `ls ruby-skill/evals/` → No such directory

## 💊 처방 우선순위

| 순위 | 병리·원인 | 액션 | 턴 | R | RegR |
|------|---------|------|----|----|------|
| P0 | ⑤-1 토큰폭식 | SKILL.md → references/ 분리 | 2~3 | L | M |
| P0 | ②-2 미발동 | P1에 키워드 2개 추가 | 1 | L | L |
| P1 | ⑦-3 테스트부재 | evals/ 디렉토리 + 샘플 케이스 | 2 | L | L |

*턴=Claude 대화 턴, R=롤백비용(L/M/H), RegR=회귀리스크(L/M/H). 단위 정의: `references/protocol-prescribe.md` §LLM 비용 추정 가이드.*

## 🔜 다음 단계

"처방해줘" 발동 시 각 항목의 구체적 수정안 도출 (skill-builder에 위임).
```

---

## Gotchas

- 스캐너만으로 100% 판정 불가 — 수동 보완 3셀 필수
- 대상 경로 오타 → PREFLIGHT에서 조기 차단
- UP 진단 시 일반 가중치 사용 = FAIL. 반드시 `up-specific-rules.md` 로드
- 리포트 저장 안 하고 본문만 출력 = 사용자가 보관 불가
