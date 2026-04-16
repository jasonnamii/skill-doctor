# Protocol: 모니터 모드 (Monitor)

스킬 폴더 전체 전수 스캔 → 병리 트렌드 집계 → 레드플래그 스킬 Top5 → 대시보드.

---

## 실행 순서

```
PREFLIGHT → 전체 스캔 → 집계 → 대시보드 생성
```

### 1. PREFLIGHT

```bash
SKILLS_DIR=/sessions/{session}/mnt/.claude/skills
echo "=== 스킬 개수 ===" && ls -d $SKILLS_DIR/*/ | wc -l
echo "=== 스킬 목록 ===" && ls -d $SKILLS_DIR/*/ | xargs -n1 basename
```

### 2. 전체 스캔 (병렬)

Python 스캐너를 전체 스킬에 적용:

```bash
cd /sessions/{session}
python skill-doctor/scripts/skill_scanner.py scan-all $SKILLS_DIR > all_scan.json
```

**출력 구조:**
```json
{
  "scan_date": "2026-04-17",
  "total_skills": 45,
  "skills": {
    "skill-a": {"total_score": 82, "grade": "GREEN", "fails": 2, "warns": 5},
    "skill-b": {"total_score": 64, "grade": "ORANGE", "fails": 5, "warns": 8},
    ...
  },
  "aggregate": {
    "by_pathology": {
      "1_latency": {"avg_score": 78, "fail_rate": 0.15},
      "2_inaccuracy": {"avg_score": 82, "fail_rate": 0.10},
      ...
    }
  }
}
```

### 3. 집계 분석

| 집계 축 | 해석 |
|--------|------|
| **병리별 평균 점수** | 어떤 병리가 생태계 전반에 퍼져 있나 |
| **병리별 FAIL 비율** | 긴급 처치 필요 병리 |
| **스킬별 총점 분포** | 상위 20%·하위 20% 식별 |
| **트리거 충돌 그래프** | P1 키워드 겹침 네트워크 |
| **references/ 없는 스킬** | 허브스포크 미적용 |

### 4. 대시보드 생성

```bash
python skill-doctor/scripts/report_generator.py \
  --scan-result all_scan.json \
  --mode monitor \
  --out /sessions/{session}/mnt/outputs/skills_dashboard_{date}.md
```

**대시보드 섹션:**

```markdown
# 📊 Skill 생태계 대시보드

**스캔일:** 2026-04-17
**총 스킬:** 45개
**평균 건강 점수:** 🟠 76/100

## 등급 분포

| 등급 | 개수 | 비율 |
|------|------|------|
| 🟢 (≥80) | 18 | 40% |
| 🟠 (60-79) | 22 | 49% |
| 🔴 (<60) | 5 | 11% |

## 🔴 레드플래그 스킬 Top5

| 순위 | 스킬 | 총점 | 주요 병리 |
|------|------|------|----------|
| 1 | skill-x | 52 | ⑤비대, ⑦진화불능 |
| 2 | skill-y | 58 | ②부정확, ③불통 |
| ... |

## 병리별 생태계 건강

| 병리 | 평균 점수 | FAIL 비율 | 트렌드 |
|------|---------|----------|-------|
| ① 느림 | 82 | 8% | 🟢 양호 |
| ② 부정확 | 74 | 18% | 🟠 주의 |
| ③ 불통 | 78 | 12% | 🟠 주의 |
| ④ 취약 | 68 | 25% | 🔴 경고 |
| ⑤ 비대 | 71 | 22% | 🟠 주의 |
| ⑥ 고립 | 80 | 10% | 🟢 양호 |
| ⑦ 진화불능 | 65 | 30% | 🔴 경고 |
| ⑧ 무자각 | 60 | 35% | 🔴 경고 |

## 🔴 생태계 레벨 레드플래그

1. **⑧ 무자각 (35% FAIL)** — 35% 스킬이 자기 상태를 모름. UP_RESET 트리거·self-check 추가 권장.
2. **⑦ 진화불능 (30% FAIL)** — 30% 스킬이 버전관리 부재. autoloop 핸드오프 확산 필요.
3. **④ 취약 (25% FAIL)** — 25% 스킬이 엣지케이스 방어 부재. PREFLIGHT 템플릿 표준화 필요.

## 💊 생태계 처방

| 순위 | 액션 | 범위 |
|------|------|------|
| P0 | 레드플래그 5개 스킬 개별 진단·처방 | 5개 스킬 |
| P1 | 무자각 병리 전반 — UP_RESET·self-check 프로토콜 표준화 | 전체 |
| P2 | 진화불능 — 버전관리 템플릿 확산 | 전체 |

## 트리거 충돌 경고

다음 P1 키워드가 2개+ 스킬에서 중복:

| 키워드 | 경합 스킬 |
|--------|---------|
| "분석" | skill-a, skill-b, skill-c |
| "진단" | skill-doctor, biz-skill, ... |

→ NOT 라우팅 재점검 권장.
```

### 5. 추적 (선택)

월간 대시보드를 `mnt/outputs/monitoring/` 에 누적:

```
monitoring/
├── 2026-02_dashboard.md
├── 2026-03_dashboard.md
└── 2026-04_dashboard.md
```

트렌드 비교:
- 병리별 FAIL 비율 추이
- 레드플래그 스킬 해소 여부
- 신규 스킬 유입 시 평균 점수 영향

---

## Gotchas

- **전수 스캔 시 토큰 폭발** → 각 스킬 SKILL.md만 로드, references/는 메타 정보만 (크기·개수)
- **병렬 처리 안 하면 느림** → 스캐너 내부에서 multiprocessing 활용 가능
- **트렌드 비교 데이터 부족** → 최소 3개 스냅샷 필요 (1회 스캔만으로는 트렌드 판정 불가)
- **자기 자신(skill-doctor) 포함 여부** → 포함하되 무한루프 방지 플래그 필수
