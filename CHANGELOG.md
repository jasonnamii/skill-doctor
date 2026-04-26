# Changelog — skill-doctor

스킬·UP 32셀 진단 엔진 변경이력.

---

## 2.0.0 — 2026-04-26 (베놈화)

**트리거:** 형 요청 — "안트로픽의 권장 사항을 참조하여 진단 수준과 리팩토링 능력을 올리고 싶어. 베놈처럼 완벽하게 적용해줘."

### 컨셉: 베놈 일체화
별도 모듈/축 추가 없이, 안트로픽 공식 권장사항을 32셀 내부의 휴리스틱과 자연 합체. 외관상 v1과 동일한 32셀, 내부 DNA만 안트로픽 표준으로 강화.

### Added
- 절대규칙 #6 신설 — "결정성 우선. 정량 기준이 휴리스틱보다 우선" (Anthropic 표준 정합성 보장)
- frontmatter `version: 2.0.0` + `license` 필드 (anthropic-skills 4개 스킬 표준 정렬)
- ❌ WRONG / ✅ CORRECT 대조 섹션 (xlsx·docx 표준 패턴)
- Gotchas 2행 추가 (에러 침묵·session-briefing 연계)

### Changed (베놈 통합 — 32셀 내부 강화)
- **2-1 오발동**: P1 일반 키워드 검사 + Anthropic 모호 동사 (`Helps with`·`Processes`·`Handles`·`Works with`·`Takes care of`) 통합
- **2-3 의도이탈**: desc-body 동사 일치 + Anthropic 1·2인칭 검사 (3인칭/명령형 권장)
- **3-2 학습곡선**: 예시·P2 + Anthropic Quick Reference 도입부 검사 (첫 100줄 표/도입 헤더)
- **3-3 피드백**: Gotchas + Anthropic ❌WRONG/✅CORRECT 대조 패턴
- **3-4 기억부담**: 이름-기능 매핑 + Anthropic name 형식 `^[a-z0-9-]{1,64}$`
- **4-1 인젝션**: 방어 규칙 + Anthropic allowed-tools 화이트리스트 권장
- **4-2 엣지케이스**: PREFLIGHT + Anthropic "결정적 작업의 scripts/ 위임" 검사 (LLM 강요 안티패턴 차단)
- **5-1 토큰폭식**: KB 임계 + Anthropic description ≤1024자 + SKILL.md ≤500줄 (가장 엄격한 위반 채택)
- **6-1 cascade**: NOT 라우팅 + Anthropic 부정 경계 (`DO NOT`·`except`·`NOT for`·`금지`)
- **7-4 버전관리**: CHANGELOG + Anthropic license 필드

### Self-Diagnosis (v2 자체 진단)
- v1 → v2 전환 후 셀프 점수 측정
- 자체 약점 식별 → 즉시 보완 (예시 코드블록 라벨 정제·CHANGELOG 신설)

### Why
- v1: 형의 UP·스킬 생태계에 특화된 "내부 룰북"
- v2: 안트로픽 공식 표준 + v1 차별점 모두 통합. 외부인이 검사해도 통과하는 표준 정합성 확보

---

## 1.0.0 — initial

8병리×4원인=32셀 매트릭스 진단 엔진. UP 가중치 모드. Python 자동 스캐너.
