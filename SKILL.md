---
name: skill-doctor
version: 2.1.0
license: Proprietary. LICENSE.txt has complete terms
description: |
  스킬·UP 8대 병리(느림·부정확·불통·취약·비대·고립·진화불능·무자각)×4원인=32셀 매트릭스 진단엔진. **v2.1: PRE_DIAGNOSE_GUARD 사전진단형 전환** — ③ 32셀 스캔 *진입 전* 5종 사전 활성화(본질질문·톱3 사전식별·증거기반·UP가중치·처방청사진). 사후처방 → 사전진단. 32셀 전수는 안전망. 진단·처방·모니터 3모드+UP특화. Python 스캐너 내장.
  P1: 스킬닥터, skill doctor, skill-doctor, 스킬진단, UP진단, 스킬검진, 스킬감사, 스킬병리, 32셀매트릭스, 8대병리, 스킬건강, 사전진단가드, PRE_DIAGNOSE_GUARD.
  P2: 진단해줘, 검진해줘, 점검해줘, diagnose, audit, checkup.
  P3: skill audit, skill diagnostics, pathology check, UP integrity check, pre-diagnose guard.
  P5: 진단리포트로, 처방전으로, 대시보드로.
  NOT: 변이·최적화(→autoloop), 생성·수정(→skill-builder), 팩트체크(→fact-checker), 리스크(→risk-radar), UP편집(→up-manager).
---

# Skill Doctor (스킬닥터)

스킬/UP의 8대 병리를 32셀 매트릭스로 진단하고 처방하는 메타 스킬. 스킬진단·UP진단·스킬검진·스킬감사·스킬병리·스킬건강 요청 시 발동. 32셀매트릭스로 전수 점검. 약어: 8대병리.
**v2.1 사전진단형:** 진단 단계 *자체*에 5종 사전 활성화. 32셀 전수 스캔 = 안전망. 사후처방 의존 ✗.

---

## 절대 규칙

| # | 규칙 | 이유 |
|---|------|------|
| 1 | **진단만 수행** — 스킬 파일을 직접 수정하지 않음. 처방전·handoff.json만 발행, 수정은 skill-builder에 위임 | 진단과 치료 분리 (측정 주체가 수정하면 편향) |
| 2 | **32셀 전수 점검** — 8병리×4원인 누락 없이. 해당없음은 `N/A` 명시 | MECE 보장, 사각지대 차단 |
| 3 | **증거 기반 판정** — FAIL/WARN 시 반드시 근거(파일경로·라인·grep결과) 병기 | 주관 판정 금지 |
| 4 | **UP은 가중치 모드** — UP 진단 시 `references/up-specific-rules.md` 자동 로드, 비대·고립·진화불능 가중치 ×3 | 상시 로드 특성 반영 |
| 5 | **자기참조 허용** — skill-doctor로 skill-doctor 진단 가능 (무한루프 방지 위해 1회만) | 자기검증 필수 |
| 6 | **결정성 우선** — 같은 셀에 여러 검사가 걸리면 가장 엄격한 판정 채택. 정량 기준(자수·줄수·필드규약)이 휴리스틱(grep)보다 우선 | 진단 결과 재현성·표준 정합성 보장 |
| 7 | **PRE_DIAGNOSE_GUARD 사전진단형 (v2.1)** — ③ 32셀 스캔 *진입 전* 5종 사전 활성화 → 사전 식별된 톱3가 32셀의 80%를 미리 잡아냄. ①본질질문(스킬 1줄 본질·존재 이유) ②톱3 사전식별(8대 병리 중 가장 의심되는 3개를 SKILL.md 1회 스캔으로 사전 추출) ③증거기반 사전(grep·라인 사전 추출 후 32셀 진입) ④UP 가중치 사전(UP 모드면 비대·고립·진화불능 ×3 사전 박제) ⑤처방청사진 사전(FAIL 셀 → handoff.json 슬롯 사전 준비). 사후 32셀 풀스캔 후 처방 = 안전망 1회로 격하 | paper-engine v3.1·skill-builder v1.5와 동일 본질. 사후 32셀 풀스캔만 하면 톱3 발견 후 무의미 셀 27개 토큰 낭비. 사전 톱3로 80% 차단 |

> **INV 7 — PRE_DIAGNOSE_GUARD 본질**
> ③-PRE 5종 활성화 → 톱3 사전 식별 후 32셀 진입. 메커니즘: 사후 풀스캔 ✗·사전 톱3 ○. 자가검사 (스캔 직전): "톱3를 *지금* 식별하고 32셀 진입하나, 32셀 끝나고 톱3 추출하나?" 후자 = FAIL → ③-PRE 재진입.

---

## 실행 흐름

```
🚦 PREFLIGHT → ① 모드 판정 → ② 대상 로드 → ③-PRE PRE_DIAGNOSE_GUARD (5종 활성화·톱3 사전식별) → ③ 32셀 스캔 [톱3 가중치] → ④ 리포트 발행

** 메커니즘: 사전진단형. ③-PRE에서 톱3 박힌 상태로 32셀 진입, ③은 안전망. 사후처방 ✗. **
```

### 🚦 PREFLIGHT

```bash
# 대상 스킬 존재·SKILL.md 가독·references/·scripts/ 확인
ls -la /sessions/{session}/mnt/.claude/skills/{target}/SKILL.md
find /sessions/{session}/mnt/.claude/skills/{target}/ -type f | head -20
```

### ① 모드 판정

| 입력 신호 | 모드 | 프로토콜 |
|----------|------|----------|
| "진단해줘"·"검진해줘" + 스킬 1개 | **진단 (Diagnose)** | `→ references/protocol-diagnose.md` |
| "처방해줘"·"고쳐야 할 거"·진단 결과 후속 | **처방 (Prescribe)** | `→ references/protocol-prescribe.md` |
| "전체 스캔"·"대시보드"·"모니터" | **모니터 (Monitor)** | `→ references/protocol-monitor.md` |
| 대상이 UP (`~/.claude/CLAUDE.md` 또는 UP 본체) | **UP 모드** (진단 + UP 가중치) | `→ references/up-specific-rules.md` 추가 로드 |

### ② 대상 로드

| 대상 | 로드 범위 |
|------|----------|
| 스킬 1개 | SKILL.md + references/ 목록 + scripts/ 목록 |
| UP | UP 본체 1개 (상시로드 특성) |
| 전체 (모니터) | skills/ 하위 모든 SKILL.md |

### ③-PRE 사전 진단 가드 (v2.1, INV 7) — 사전진단가드

③ 32셀 진입 *전* 5종 사전 활성화. 톱3가 사후 적발의 80%를 사전 차단.

| # | 룰 | 사전 강제 (스캔 전 답해야 ③ 진입) | 사후 발견 시 |
|---|---|---|---|
| 1 | **본질 질문** | "이 스킬 1줄 본질? 왜 존재하나? 어떤 사용자 문제 해결?" | ③-PRE 재진입 |
| 2 | **톱3 사전식별** | SKILL.md 1회 스캔 → 8대 병리 중 가장 의심되는 3개 사전 추출. 정의: `→ references/framework-8x4.md` | ③-PRE 재진입 |
| 3 | **증거 사전추출** | 톱3 후보별 grep·라인 사전 추출 (FAIL 후보 위치 사전 확보) | ③-PRE 재진입 |
| 4 | **UP 가중치 사전** | UP 모드면 비대·고립·진화불능 ×3 사전 박제. `→ references/up-specific-rules.md` 사전 로드 | ③-PRE 재진입 |
| 5 | **처방 청사진 사전** | 톱3 FAIL 가정 시 handoff.json 슬롯 사전 준비 (skill-builder 위임 형식) | ③-PRE 재진입 |

**메커니즘:** 5종 답을 *먼저* 확정 → 그 답으로 ③ 32셀 진입. "32셀 다 돌리고 톱3 추출" = FAIL. paper-engine v3.1·skill-builder v1.5와 동일 패턴.

**자가검사 (③ 진입 직전):** "톱3를 *지금* 식별하고 32셀 진입하나, 32셀 끝나고 톱3 추출하나?" 후자 = FAIL → ③-PRE 재진입.

**효과:** 사후 32셀 풀스캔 후 톱3 추출 = 27셀 토큰 낭비. 사전 톱3 식별 후 32셀 진입 = 톱3에 가중치, 나머지 29셀은 안전망 통과 검증.

---

### ③ 32셀 스캔 (v2.1 안전망)

**v2.1:** 사전진단형 전환으로 ③은 **톱3 가중치 + 안전망 1회**. 톱3 외 29셀은 빠른 통과 검증. 톱3는 사전 추출된 증거로 정밀 판정.

**프레임:** `→ references/framework-8x4.md` (8대 병리×4대 원인 정의)
**체크리스트:** `→ references/diagnostic-checklist.md` (32셀 grep·규칙·정량 기준 통합)
**Python 자동 스캐너:**
```bash
python /sessions/{session}/skill-doctor/scripts/skill_scanner.py scan {target_path}
# 출력: JSON {cell: {status, evidence, score}}
```

각 셀 판정: {🟢 PASS·🟠 WARN·🔴 FAIL·⚪ N/A}

### ④ 리포트 발행

**생성기:**
```bash
python /sessions/{session}/skill-doctor/scripts/report_generator.py \
  --scan-result scan.json --target {skill-name} --out report.md
```

**리포트 구조:**
1. 전체 건강 점수 (🟢≥85 / 🟠 60-84 / 🔴<60)
2. 8×4 매트릭스 시각화
3. 레드플래그 Top3 (증거 포함)
4. 처방 우선순위 (트리아지: 긴급×중요)
5. 개선 액션 목록 + handoff.json (skill-builder로 위임)

---

## 8대 병리 요약 (스파인)

```
① 느림       흐름이 멈춘다      (흐름단절·과부하·상태오염·결정지연)
② 부정확     엉뚱한 게 발동된다  (오발동·미발동·의도이탈·출력변동)
③ 불통       사용자가 못 쓴다    (스텔스실패·학습곡선·피드백부재·기억부담)
④ 취약       조금만 건드려도 깨진다 (인젝션·엣지케이스·외부의존·상태오염)
⑤ 비대       토큰을 먹어치운다   (토큰폭식·로딩비효율·맥락오염·중복로딩)
⑥ 고립       다른 스킬과 안 논다 (cascade단절·트리거충돌·UP불화·의존사이클)
⑦ 진화불능   고치면 망한다      (하위호환붕괴·본질유실·테스트부재·버전관리부재)
⑧ 무자각     죽어도 모른다      (자기진단불가·실패침묵·개선신호부재·학습축적부재)
```

**상세 정의:** `→ references/framework-8x4.md`
**병리별 실제 사례·안티패턴:** `→ references/pathology-patterns.md`

---

## 예시 (1턴 진단)

```
사용자: "ruby-skill 진단해줘"

Claude: [skill-doctor 발동]
1. PREFLIGHT → SKILL.md 존재 확인
2. 모드 선택 → 진단 모드
3. 대상 로드 → ruby-skill/SKILL.md + references/
4. 32셀 스캔 (skill_scanner.py 실행)
5. 리포트 발행 (report_generator.py)

출력: /sessions/.../mnt/outputs/ruby-skill_diagnosis_{date}.md
- 건강 점수: 🟠 74/100
- 레드플래그 Top3
- 처방 우선순위
```

---

## 자체 점검 (Self-Check)

skill-doctor는 자기 자신을 진단할 수 있어야 한다. 스킬 수정 후 다음 실행:

```bash
# self-check: skill-doctor가 skill-doctor를 진단
python skill-doctor/scripts/skill_scanner.py scan ./skill-doctor/ > self-scan.json
python skill-doctor/scripts/report_generator.py --scan-result self-scan.json --target skill-doctor --out self-report.md
```

- 목표 점수: 🟢 ≥85 (v2 강화 기준), FAIL 셀 0개
- evals/cases.json에 5개 샘플 케이스 포함 — validate 시 비교 기준

---

## Gotchas

| 함정 | 대응 |
|------|------|
| 주관 판정 (증거 없이 "취약해 보임") | 반드시 grep·파일경로·라인 병기. 증거 없음 → ⚪ N/A |
| 전체 스캔 시 토큰 폭발 | 모니터 모드는 요약 통계만, 상세는 스킬당 on-demand |
| UP 진단에 일반 가중치 적용 | UP 진단 시 `up-specific-rules.md` 자동 로드 필수 — 비대·고립·진화불능 ×3 |
| 자기참조 무한루프 | skill-doctor 자체 진단은 1회만. 처방 결과는 사용자에게 출력, 재진단 금지 |
| 진단→수정 직행 | skill-doctor는 진단만. 수정은 반드시 skill-builder로 위임 (절대규칙 1) |
| 32셀 일부 스킵 | N/A도 명시 필수. 빈 셀 = FAIL (MECE 깨짐) |
| Python 스크립트 미실행 | 수동 체크는 오류 가능. 반드시 skill_scanner.py 실행 후 결과 검토 |
| 정량 기준과 휴리스틱 충돌 | 정량 우선 (절대규칙 6). 자수·줄수·필드규약 위반 시 grep PASS 무시하고 FAIL |
| 에러 시 침묵 | 모든 검사 실패는 STOP + 보고. evidence 누락 = 재실행 |
| session-briefing 연계 누락 | 진단·처방 결과는 session-briefing 발동 시 자동 첨부 |
| **사후처방 의존 (32셀 풀스캔 후 톱3 추출)** | INV 7 위반. ③-PRE 5종을 *스캔 전* 활성화. 톱3 사전식별로 27셀 토큰 절감. 사후 적발 시 ③-PRE 재진입 |
| ③-PRE 5종 일부 스킵 ("일단 32셀 돌리고 보자") | 사전진단형 본질 위배 → 톱3 무가중치·증거 미수집 → 처방 부정확. 5종 답 확정 후 ③ 진입 |

## ❌ WRONG vs ✅ CORRECT

```
❌ WRONG: "ruby-skill 좀 취약해 보여" (증거 없음 → 주관 판정)
✅ CORRECT: "[4-2] PREFLIGHT 누락 (line 23, grep '입력 검증' 0건)"
```

```
❌ WRONG: 진단 후 SKILL.md 직접 수정 (절대규칙 1 위반)
✅ CORRECT: 진단 → handoff.json 발행 → skill-builder 위임
```
