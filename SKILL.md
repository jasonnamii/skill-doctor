---
name: skill-doctor
license: Proprietary. LICENSE.txt has complete terms
description: |
  스킬·UP 8대 병리(느림·부정확·불통·취약·비대·고립·진화불능·무자각)×4원인=32셀 매트릭스 + 9룰 베놈 진단축 추가 = **41셀** 진단엔진. v2.2: 9룰 갭(Boundaries·WhenToUse·Prereq·OutputPath·RefIndex·NextPhase·FailureModes·평문톤·metadata) 진단축 추가. PRE_DIAGNOSE_GUARD 사전진단형 유지. 진단·처방·모니터 3모드+UP특화.
  P1: 스킬닥터, skill doctor, skill-doctor, 스킬진단, UP진단, 스킬검진, 스킬감사, 스킬병리, 32셀매트릭스, 41셀매트릭스, 8대병리, 9룰진단, 스킬건강, 사전진단가드, PRE_DIAGNOSE_GUARD.
  P2: 진단해줘, 검진해줘, 점검해줘, diagnose, audit, checkup.
  P3: skill audit, skill diagnostics, pathology check, UP integrity check, pre-diagnose guard, 9-rule audit.
  P5: 진단리포트로, 처방전으로, 대시보드로.
  NOT: 변이·최적화(→autoloop), 생성·수정(→skill-builder), 팩트체크(→fact-checker), 리스크(→risk-radar), UP편집(→up-manager).
metadata:
  author: jason
  version: "2.2.0"
---

# Skill Doctor (스킬닥터) v2.2

스킬/UP의 건강을 **41셀 매트릭스(8병리×4원인 + 9룰 갭)**로 진단하고 처방하는 메타 스킬. 32셀은 내재 결함, 9룰은 구성 결함을 잡는다.

**v2.2 베놈:** skill-builder v3.1의 9룰을 진단축으로 흡수. 7강제룰(Boundaries·WhenToUse·Prereq·OutputPath·RefIndex·NextPhase·FailureModes) + 2선택룰(평문톤·metadata) 갭을 본 진단에서 동시 측정.

## Skill Boundaries

- **하는 것** — 스킬·UP 진단(41셀)·증거 수집·처방전(handoff.json) 발행·모니터링 대시보드
- **안 하는 것** — SKILL.md 직접 수정(→ skill-builder) · 자동변이/최적화(→ autoloop) · 외부 사실검증(→ fact-checker) · 리스크 매트릭스(→ risk-radar) · UP 본체 편집(→ up-manager)

## When to Use

- "{스킬명} 진단해줘·검진해줘·점검해줘" — 단일 스킬 41셀 진단
- "전체 스캔·대시보드" — 모니터 모드, 다수 스킬 요약
- "UP 진단" — UP 본체 가중치 진단
- skill-builder 작업 직후 자동 호출 — 9룰 적용 여부 확인
- autoloop 시작 전 — baseline 진단으로 변이 우선순위 결정
- **안 쓸 때** — 실제 수정 원함(→ skill-builder), 자동 최적화(→ autoloop)

## Prerequisites

| # | 체크 | 미충족 시 |
|---|------|-----------|
| 1 | 대상 스킬 디렉토리 존재·SKILL.md 가독 | "스킬명·경로 확인 필요" 보고 후 STOP |
| 2 | `references/framework-8x4.md` + `references/9-rules-audit.md` 로드 | references/ 없으면 inline fallback |
| 3 | 모드 판정 완료 (진단/처방/모니터/UP) | 모드 미정 = 1줄 확인 후 진입 |
| 4 | UP 모드면 `up-specific-rules.md` 추가 로드 | 가중치 미적용 = 결과 편향 |

## ⛔ 절대 규칙

| # | 규칙 | 이유 |
|---|------|------|
| 1 | **진단만 수행** — 스킬 파일 직접 수정 ✗. 처방전·handoff.json만 발행, 수정은 skill-builder에 위임 | 진단과 치료 분리 (측정 주체가 수정하면 편향) |
| 2 | **41셀 전수 점검** — 32셀(8병리×4원인) + 9룰 갭. 해당없음은 `N/A` 명시 | MECE 보장, 사각지대 차단 |
| 3 | **증거 기반 판정** — FAIL/WARN 시 반드시 근거(파일경로·라인·grep결과) 병기 | 주관 판정 금지 |
| 4 | **UP은 가중치 모드** — UP 진단 시 비대·고립·진화불능 ×3 사전 박제 | 상시 로드 특성 반영 |
| 5 | **자기참조 1회만** — skill-doctor로 skill-doctor 진단 가능, 무한루프 ✗ | 자기검증 필수 |
| 6 | **결정성 우선** — 정량 기준(자수·줄수·필드규약)이 휴리스틱(grep)보다 우선 | 진단 결과 재현성 |
| 7 | **PRE_DIAGNOSE_GUARD 사전진단형** — 41셀 스캔 진입 전 5종 사전 활성화(본질질문·톱3 사전식별·증거기반·UP가중치·처방청사진) | 사후 풀스캔 후 톱3 추출 ✗·사전 톱3 박힘 ○ |
| 8 | **9룰 갭 측정 = 본 진단 필수축** — 32셀 외에 9룰 7강제 + 2선택을 별도 표로 출력. 누락 시 처방 우선 | 9룰은 구성 결함, 32셀은 내재 결함. 별축으로 분리 |

## 실행 흐름

```
🚦 PREFLIGHT → ① 모드 판정 → ② 대상 로드 → ③-PRE 사전진단가드 → ③ 41셀 스캔(32+9룰) → ④ 리포트 발행
```

### ③-PRE 사전 진단 가드 (5종)

| # | 룰 | 사전 강제 |
|---|---|---|
| 1 | 본질 질문 | "이 스킬 1줄 본질? 왜 존재? 어떤 문제 해결?" |
| 2 | 톱3 사전식별 | SKILL.md 1회 스캔 → 8병리 중 의심 3개 추출 |
| 3 | 증거 사전추출 | 톱3 후보별 grep·라인 사전 확보 |
| 4 | UP 가중치 사전 | UP 모드면 비대·고립·진화불능 ×3 사전 박제 |
| 5 | 처방 청사진 사전 | 톱3 FAIL 가정 시 handoff.json 슬롯 사전 준비 |

### ③ 41셀 스캔

**32셀 (8병리×4원인):** `→ references/framework-8x4.md`
**9룰 갭 (7강제 + 2선택):** `→ references/9-rules-audit.md`

| 9룰 # | 진단 항목 | grep·체크 | FAIL 기준 |
|---|---|---|---|
| 1 | Skill Boundaries 섹션 | `grep -E "Skill Boundaries\|## Boundaries"` | 누락 = FAIL |
| 2 | When to Use 조건절 | `grep -E "When to Use\|언제 (쓰\|발동)"` | 누락 = FAIL |
| 3 | Prerequisites 체크 | `grep -E "Prerequisites\|시작 전 체크\|미충족"` | 누락 = FAIL |
| 4 | Output Path 명시 | `grep -E "Output\|산출물.*경로\|VAULT/.*\.md"` | 추상 표현만 = WARN, 누락 = FAIL |
| 5 | Reference Index 표 | references/ 존재 + `grep -E "Reference Index\|references/"` | references/ 있는데 표 없음 = FAIL |
| 6 | Next Phase 추천 | `grep -E "Next Phase\|다음엔 →\|이어지는"` | 누락 = FAIL |
| 7 | Failure Modes/Gotchas | `grep -E "Gotchas\|Failure Modes\|함정"` | 누락 = FAIL |
| 8 (선택) | description 첫문장 평문 | description 첫문장 압축어 없이 한 문장 | 압축어만 = WARN |
| 9 (선택) | metadata 블록 | `grep -E "^metadata:\|author:\|version:"` | 없음 = INFO |

**Python 자동 스캐너:**
```bash
python /sessions/{session}/skill-doctor/scripts/skill_scanner.py scan {target_path}
python /sessions/{session}/skill-doctor/scripts/nine_rules_scanner.py {target_path}
```

각 셀 판정: {🟢 PASS·🟠 WARN·🔴 FAIL·⚪ N/A}

### ④ 리포트 발행

```bash
python /sessions/{session}/skill-doctor/scripts/report_generator.py \
  --scan-result scan.json --nine-rules nine.json --target {skill-name} --out report.md
```

**리포트 구조:**
1. 전체 건강 점수 (🟢≥85 / 🟠 60-84 / 🔴<60) — 32셀 70% + 9룰 30% 가중
2. 32셀 매트릭스 시각화
3. **9룰 갭 표** (신설) — 7강제·2선택 PASS/FAIL
4. 레드플래그 Top3
5. 처방 우선순위 (트리아지) + handoff.json (skill-builder 위임)

## Output Path

| 산출물 | 경로 |
|---|---|
| 진단 리포트 | `mnt/outputs/{SKILL}_diagnosis_{YYYY-MM-DD}.md` |
| 32셀 scan JSON | `/sessions/{id}/skill-doctor/scans/{SKILL}_scan.json` |
| 9룰 scan JSON | `/sessions/{id}/skill-doctor/scans/{SKILL}_nine.json` |
| handoff (skill-builder 위임) | `/sessions/{id}/skill-doctor/handoffs/{SKILL}_handoff.json` |
| 모니터 대시보드 | `mnt/outputs/skill_dashboard_{YYYY-MM-DD}.html` |

## Reference Index

| 파일 | 내용 | 언제 |
|---|---|---|
| `references/framework-8x4.md` | 8병리×4원인 정의 | 32셀 스캔 |
| `references/9-rules-audit.md` | 9룰 갭 진단 체크리스트 | 9룰 스캔 |
| `references/diagnostic-checklist.md` | 32셀 grep·정량 기준 | 셀별 판정 |
| `references/pathology-patterns.md` | 병리별 실제 사례·안티패턴 | 처방 근거 |
| `references/up-specific-rules.md` | UP 가중치 룰 | UP 모드 |
| `references/protocol-diagnose.md` | 진단 모드 프로토콜 | 모드 진입 |
| `references/protocol-prescribe.md` | 처방 모드 프로토콜 | 처방 발행 |
| `references/protocol-monitor.md` | 모니터 모드 프로토콜 | 전수 스캔 |

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

## Next Phase

진단 후 자연스러운 흐름:

- **처방 적용** → `skill-builder` (handoff.json 받아 SKILL.md 수정·패키징)
- **자동 최적화** → `autoloop` (eval 기반 변이로 점수 상승)
- **UP 진단 후** → `up-manager` (UP 본체 수정)
- **모니터 후 추세 저장** → `session-briefing` (VAULT에 진단 이력)

## 자체 점검 (Self-Check)

```bash
python skill-doctor/scripts/skill_scanner.py scan ./skill-doctor/ > self-scan.json
python skill-doctor/scripts/nine_rules_scanner.py ./skill-doctor/ > self-nine.json
python skill-doctor/scripts/report_generator.py --scan-result self-scan.json --nine-rules self-nine.json --target skill-doctor --out self-report.md
```

- 목표 점수: 🟢 ≥90 (v2.2 강화 기준 — 9룰 자체 통과 필수), FAIL 셀 0개

## Failure Modes (Gotchas)

| 함정 | 대응 |
|------|------|
| 주관 판정 (증거 없이 "취약해 보임") | grep·파일경로·라인 병기. 증거 없음 → ⚪ N/A |
| 전체 스캔 토큰 폭발 | 모니터 모드는 요약 통계만, 상세는 on-demand |
| UP 일반 가중치 적용 | UP 모드면 up-specific-rules.md 자동 로드. 비대·고립·진화불능 ×3 |
| 자기참조 무한루프 | 1회만. 재진단 ✗ |
| 진단→수정 직행 | 진단만. 수정은 skill-builder 위임 (절대규칙 1) |
| 32셀 일부 스킵 | N/A 명시 필수. 빈 셀 = FAIL (MECE 깨짐) |
| Python 스크립트 미실행 | 수동 체크 오류 가능. skill_scanner.py + nine_rules_scanner.py 실행 |
| 정량 vs 휴리스틱 충돌 | 정량 우선 (절대규칙 6) |
| 에러 시 침묵 | STOP + 보고. evidence 누락 = 재실행 |
| 사후처방 의존 (32셀 풀스캔 후 톱3) | INV 7 위반. ③-PRE 5종 *스캔 전* 활성화 |
| **9룰 갭 측정 누락** | 절대규칙 8 위반. 9룰 스캔 없이 진단 = v2.1 회귀 |
| **9룰 7강제 누락한 스킬에 32셀만 처방** | 구성 결함을 내재 결함으로 오진. 9룰 처방 먼저, 32셀 처방 다음 |
| **9룰 선택 2개를 강제 취급** | 평문톤·metadata는 INFO/WARN. FAIL 처리 ✗ |

## ❌ WRONG vs ✅ CORRECT

```
❌ WRONG: "ruby-skill 좀 취약해 보여" (증거 없음 → 주관 판정)
✅ CORRECT: "[4-2] PREFLIGHT 누락 (line 23, grep '입력 검증' 0건) | [9룰-3] Prerequisites 섹션 누락"
```

```
❌ WRONG: 32셀만 스캔하고 9룰 갭 스킵 (v2.1 회귀)
✅ CORRECT: 32셀 + 9룰 7강제 + 9룰 2선택 = 41축 동시 측정 후 처방 우선순위 분리
```
