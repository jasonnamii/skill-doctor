#!/usr/bin/env python3
"""
skill-doctor scanner
Scans a skill directory (or UP file) and produces 32-cell diagnostic JSON.

Usage:
    python skill_scanner.py scan <target_path>
    python skill_scanner.py scan-all <skills_dir>
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any


# ---------- Constants ----------

PATHOLOGIES = {
    "1": "느림 (Latency)",
    "2": "부정확성 (Inaccuracy)",
    "3": "불통성 (Opacity)",
    "4": "취약성 (Fragility)",
    "5": "비대함 (Bloat)",
    "6": "고립성 (Isolation)",
    "7": "진화불능 (Rigidity)",
    "8": "무자각 (Meta-Blindness)",
}

CAUSES = {
    "1-1": "흐름단절", "1-2": "과부하", "1-3": "상태오염", "1-4": "결정지연",
    "2-1": "오발동", "2-2": "미발동", "2-3": "의도이탈", "2-4": "출력변동",
    "3-1": "스텔스실패", "3-2": "학습곡선", "3-3": "피드백부재", "3-4": "기억부담",
    "4-1": "프롬프트인젝션", "4-2": "엣지케이스", "4-3": "외부의존", "4-4": "상태오염",
    "5-1": "토큰폭식", "5-2": "로딩비효율", "5-3": "맥락오염", "5-4": "중복로딩",
    "6-1": "cascade단절", "6-2": "트리거충돌", "6-3": "UP불화", "6-4": "의존사이클",
    "7-1": "하위호환붕괴", "7-2": "본질유실", "7-3": "테스트부재", "7-4": "버전관리부재",
    "8-1": "자기진단불가", "8-2": "실패침묵", "8-3": "개선신호부재", "8-4": "학습축적부재",
}

GENERIC_KEYWORDS = ["정리", "분석", "만들기", "확인", "검토", "처리", "작성", "생성"]

UP_INVARIANTS = ["HONORIFIC", "OVERWRITE_BAN", "PATTERN_GUARD", "STEALTH",
                 "ERROR_CORRECTION", "MODE_GATES", "INVARIANT"]

UP_GAUGE_WEIGHTS = {"5": 3, "6": 3, "7": 3, "8": 3}  # UP mode weights


# ---------- Utilities ----------

def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def is_up_target(target_path: Path, content: str) -> bool:
    """Detect if target is UP (User Preferences)."""
    name = target_path.name.lower()
    if "claude.md" in name or "up-" in name or name == "up.md":
        return True
    # Signature patterns
    signatures = ["M1. FRAME", "M2. FAST_LANE", "BEDROCK", "CONFIDENCE",
                  "FAST_LANE", "DENSITY"]
    hits = sum(1 for s in signatures if s in content)
    return hits >= 3


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """Parse YAML frontmatter from SKILL.md."""
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}
    fm_text = m.group(1)
    result = {}
    current_key = None
    for line in fm_text.split("\n"):
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            current_key = key.strip()
            result[current_key] = val.strip().lstrip("|").strip()
        elif current_key and line.strip():
            result[current_key] += " " + line.strip()
    return result


def count_trigger_tier(description: str, tier: str) -> int:
    """Count items in P1/P2/P3/P4/P5/NOT tier."""
    pattern = rf"{tier}:\s*([^.]*)\."
    m = re.search(pattern, description)
    if not m:
        return 0
    items = [x.strip() for x in m.group(1).split(",") if x.strip()]
    return len(items)


def make_cell(status: str, evidence: str, score: float = None) -> Dict:
    if score is None:
        score = {"PASS": 1.0, "WARN": 0.5, "FAIL": 0.0, "N/A": None}[status]
    return {"status": status, "evidence": evidence, "score": score}


# ---------- Cell Checks ----------

def check_1_1(content: str, files: List[Path]) -> Dict:
    """Bottleneck: sequential enforcement"""
    sequential_markers = len(re.findall(r"반드시 순차|먼저.*후에|동기 실행|순서대로만", content))
    if sequential_markers >= 3:
        return make_cell("FAIL", f"순차 강요 {sequential_markers}건 감지")
    if sequential_markers >= 1:
        return make_cell("WARN", f"순차 강요 {sequential_markers}건")
    return make_cell("PASS", "병렬 허용 가능")


def check_1_2(content: str, files: List[Path]) -> Dict:
    """Overload: references simultaneous loading"""
    ref_files = [f for f in files if "references" in str(f)]
    concurrent_load = len(re.findall(r"모두 읽고|전체 참조|references/.*모두", content))
    if concurrent_load >= 2 or len(ref_files) >= 6:
        return make_cell("FAIL", f"references {len(ref_files)}개, 동시로드 힌트 {concurrent_load}")
    if concurrent_load >= 1:
        return make_cell("WARN", f"동시 로드 힌트 {concurrent_load}건")
    return make_cell("PASS", f"references {len(ref_files)}개, 허브스포크 명확")


def check_1_3(content: str, files: List[Path]) -> Dict:
    """State Corruption: retry loops"""
    has_retry_cap = "max 2회" in content or "상한" in content or "hardcap" in content.lower()
    retry_mentioned = "재시도" in content or "retry" in content.lower()
    if retry_mentioned and not has_retry_cap:
        return make_cell("FAIL", "재시도 상한 없음")
    if retry_mentioned and has_retry_cap:
        return make_cell("PASS", "재시도 상한 명시")
    return make_cell("PASS", "재시도 루프 없음")


def check_1_4(content: str, files: List[Path]) -> Dict:
    """Decision Latency: nested branching"""
    # Count nested if/elif depth
    if_chains = re.findall(r"(if.*?(?:elif.*?){3,})", content, re.IGNORECASE)
    if if_chains:
        return make_cell("FAIL", f"4단+ 분기 체인 {len(if_chains)}개")
    table_count = content.count("|---|")
    if table_count >= 2:
        return make_cell("PASS", f"표 기반 결정 {table_count}개")
    return make_cell("WARN", "결정 구조 모호")


def check_2_1(fm: Dict, content: str) -> Dict:
    """False Positive: generic P1 keywords"""
    desc = fm.get("description", "")
    p1_match = re.search(r"P1:\s*([^.]+)\.", desc)
    if not p1_match:
        return make_cell("FAIL", "P1 섹션 없음")
    p1_text = p1_match.group(1)
    generic_hits = [kw for kw in GENERIC_KEYWORDS if kw in p1_text]
    if len(generic_hits) >= 3:
        return make_cell("FAIL", f"일반 키워드 {len(generic_hits)}개: {generic_hits}")
    if len(generic_hits) >= 1:
        return make_cell("WARN", f"일반 키워드 {generic_hits}")
    return make_cell("PASS", "도메인 특화 키워드만")


def check_2_2(fm: Dict) -> Dict:
    """False Negative: trigger tier minimums"""
    desc = fm.get("description", "")
    p1 = count_trigger_tier(desc, "P1")
    p2 = count_trigger_tier(desc, "P2")
    p3 = count_trigger_tier(desc, "P3")
    p5 = count_trigger_tier(desc, "P5")
    has_not = "NOT:" in desc
    fails = []
    if p1 < 5: fails.append(f"P1={p1}<5")
    if p2 < 2: fails.append(f"P2={p2}<2")
    if p3 < 2: fails.append(f"P3={p3}<2")
    if p5 < 1: fails.append(f"P5={p5}<1")
    if not has_not: fails.append("NOT 없음")
    if len(fails) >= 3:
        return make_cell("FAIL", ", ".join(fails))
    if fails:
        return make_cell("WARN", ", ".join(fails))
    return make_cell("PASS", f"P1={p1} P2={p2} P3={p3} P5={p5} NOT=Y")


def check_2_3(fm: Dict, content: str) -> Dict:
    """Intent Drift: description vs body mismatch - heuristic"""
    desc = fm.get("description", "")
    # Extract likely verbs from description
    desc_verbs = set(re.findall(r"(진단|평가|검진|수정|생성|분석|설계|변환|번역)", desc))
    body_verbs = set(re.findall(r"##.*?(진단|평가|검진|수정|생성|분석|설계|변환|번역)", content))
    if desc_verbs and body_verbs:
        overlap = desc_verbs & body_verbs
        if len(overlap) / len(desc_verbs) < 0.5:
            return make_cell("WARN", f"desc {desc_verbs} vs body {body_verbs}")
    return make_cell("PASS", f"desc-body 동사 일치")


def check_2_4(content: str) -> Dict:
    """Non-determinism: vague expressions"""
    vague = len(re.findall(r"적절히 판단|자유롭게|알아서|상황에 맞게", content))
    if vague >= 5:
        return make_cell("FAIL", f"모호 표현 {vague}건")
    if vague >= 2:
        return make_cell("WARN", f"모호 표현 {vague}건")
    return make_cell("PASS", "결정적 규칙")


def check_3_1(content: str) -> Dict:
    """Stealth Failure: internal labels in user-facing output"""
    labels = ["[L0]", "[L1]", "[L2]", "[L3]", "Phase 1", "Phase 2", "WEIGHT:", "판정:"]
    hits = [l for l in labels if l in content]
    # Heuristic: if these appear in "응답" or "출력" sections, bad
    example_section = re.search(r"(?:예시|출력|응답).*?(?=##|\Z)", content, re.DOTALL)
    if example_section:
        ex_text = example_section.group(0)
        ex_hits = [l for l in labels if l in ex_text]
        if ex_hits:
            return make_cell("FAIL", f"응답 예시에 내부 라벨: {ex_hits}")
    if hits and "STEALTH" not in content:
        return make_cell("WARN", f"내부 라벨 {len(hits)}건, STEALTH 미언급")
    return make_cell("PASS", "스텔스 준수")


def check_3_2(content: str, fm: Dict) -> Dict:
    """Learning Curve: examples + P2"""
    p2 = count_trigger_tier(fm.get("description", ""), "P2")
    has_example = bool(re.search(r"##\s*예시|##\s*Example", content))
    if not has_example and p2 < 2:
        return make_cell("FAIL", f"예시 없음 + P2={p2}")
    if not has_example or p2 < 2:
        return make_cell("WARN", f"예시={has_example}, P2={p2}")
    return make_cell("PASS", "예시 + P2 충분")


def check_3_3(content: str) -> Dict:
    """Feedback Absence: Gotchas section"""
    gotchas_match = re.search(r"##\s*Gotchas.*?(?=##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if not gotchas_match:
        return make_cell("FAIL", "Gotchas 섹션 없음")
    gotcha_lines = len([l for l in gotchas_match.group(0).split("\n") if l.strip().startswith("|")])
    if gotcha_lines < 3:
        return make_cell("WARN", f"Gotchas {gotcha_lines}행")
    return make_cell("PASS", f"Gotchas {gotcha_lines}행")


def check_3_4(fm: Dict, target_name: str) -> Dict:
    """Memory Burden: name-function mapping"""
    desc = fm.get("description", "")
    first_line = desc.split(".")[0] if desc else ""
    # Check if skill name words appear in first sentence
    name_parts = target_name.replace("-", " ").replace("_", " ").lower().split()
    matched = sum(1 for p in name_parts if p in first_line.lower())
    if matched == 0 and name_parts:
        return make_cell("WARN", f"이름-기능 연결 불명")
    return make_cell("PASS", "이름이 기능 암시")


def check_4_1(content: str) -> Dict:
    """Prompt Injection defense"""
    has_defense = any(x in content for x in ["INVARIANT", "게이트키퍼", "절대 규칙", "반드시 우선"])
    if not has_defense:
        return make_cell("WARN", "명시적 방어 규칙 없음")
    return make_cell("PASS", "방어 규칙 존재")


def check_4_2(content: str) -> Dict:
    """Edge cases"""
    has_preflight = "PREFLIGHT" in content or "입력 검증" in content or "empty" in content.lower()
    if not has_preflight:
        return make_cell("WARN", "PREFLIGHT/검증 단계 불명")
    return make_cell("PASS", "입력 검증 언급")


def check_4_3(content: str, fm: Dict) -> Dict:
    """External dependency"""
    has_vault = "vault_dependency" in content or "vault_dependency" in str(fm)
    has_fallback = "fallback" in content.lower() or "폴백" in content
    external = "볼트" in content or "mount" in content.lower() or "외부" in content
    if external and not has_vault:
        return make_cell("WARN", "외부 의존, vault_dependency 없음")
    if has_vault and not has_fallback:
        return make_cell("WARN", "vault 선언, fallback 없음")
    if has_vault and has_fallback:
        return make_cell("PASS", "선언 + fallback")
    return make_cell("N/A", "외부 의존 없음")


def check_4_4(content: str) -> Dict:
    """State pollution (session)"""
    has_reset = "CONTEXT_WATCH" in content or "PIVOT" in content or "재검증" in content or "reset" in content.lower()
    if not has_reset:
        return make_cell("WARN", "세션 상태 관리 불명")
    return make_cell("PASS", "재검증 규칙")


def check_5_1(skill_md_path: Path) -> Dict:
    """Token bloat"""
    if not skill_md_path.exists():
        return make_cell("N/A", "SKILL.md 없음")
    size = skill_md_path.stat().st_size
    if size > 10240:
        return make_cell("FAIL", f"SKILL.md {size}B >10KB")
    if size > 5120:
        return make_cell("WARN", f"SKILL.md {size}B >5KB")
    return make_cell("PASS", f"SKILL.md {size}B ≤5KB")


def check_5_2(content: str, files: List[Path], skill_md_size: int) -> Dict:
    """Loading inefficiency"""
    ref_files = [f for f in files if "references" in str(f) and f.suffix == ".md"]
    has_pointers = "→" in content and ("references/" in content or "참조" in content)
    if skill_md_size > 5120 and not ref_files:
        return make_cell("FAIL", f"SKILL.md 큰데 references/ 없음")
    if ref_files and not has_pointers:
        return make_cell("WARN", "references/ 있으나 포인터 없음")
    return make_cell("PASS", f"허브스포크 {len(ref_files)}개")


def check_5_3(content: str) -> Dict:
    """Context pollution"""
    internal_terms = ["Phase 1 완료", "[L2]", "WEIGHT:", "BEDROCK", "판정:"]
    hits = sum(content.count(t) for t in internal_terms)
    if hits >= 5:
        return make_cell("WARN", f"내부 용어 {hits}건")
    return make_cell("PASS", "내부 용어 절제")


def check_5_4(content: str) -> Dict:
    """Duplicate loading"""
    ref_pointers = re.findall(r"references/([a-z0-9\-]+)\.md", content)
    from collections import Counter
    counts = Counter(ref_pointers)
    duplicates = {k: v for k, v in counts.items() if v >= 3}
    if duplicates:
        return make_cell("WARN", f"중복 참조: {duplicates}")
    return make_cell("PASS", "중복 참조 없음")


def check_6_1(content: str, fm: Dict) -> Dict:
    """Cascade disconnection: NOT routing"""
    desc = fm.get("description", "")
    has_not = "NOT:" in desc
    has_routing = "(→" in desc
    if not has_not:
        return make_cell("FAIL", "NOT 섹션 없음")
    if has_not and not has_routing:
        return make_cell("WARN", "NOT 있으나 라우팅 없음")
    return make_cell("PASS", "NOT + 라우팅")


def check_6_2(fm: Dict, all_skills_p1: List[str] = None) -> Dict:
    """Trigger collision (requires external data)"""
    # If no external data, partial check via generic keywords
    desc = fm.get("description", "")
    p1_match = re.search(r"P1:\s*([^.]+)\.", desc)
    if not p1_match:
        return make_cell("N/A", "P1 없음")
    p1_keywords = [x.strip() for x in p1_match.group(1).split(",")]
    # Heuristic: very common single-char words
    common = [k for k in p1_keywords if len(k) <= 2 and k not in ["BP", "UP"]]
    if common:
        return make_cell("WARN", f"너무 짧은 키워드: {common}")
    return make_cell("PASS", "적절한 길이 키워드")


def check_6_3(content: str, is_up: bool) -> Dict:
    """UP discord"""
    if is_up:
        has_precedence = "SKILL_PRECEDENCE" in content
        if not has_precedence:
            return make_cell("FAIL", "SKILL_PRECEDENCE 없음")
        return make_cell("PASS", "SKILL_PRECEDENCE 명시")
    # For regular skills
    has_precedence_mention = "SKILL_PRECEDENCE" in content or "UP 우선" in content or "UP 준수" in content
    if "반말" in content or "평어" in content:
        return make_cell("WARN", "HONORIFIC 충돌 가능")
    return make_cell("PASS", "UP 준수")


def check_6_4(content: str, target_name: str) -> Dict:
    """Dependency cycle"""
    # Self-reference or bi-directional calls (heuristic)
    return make_cell("N/A", "전체 생태계 스캔 필요")


def check_7_1(content: str, fm: Dict) -> Dict:
    """Backward compatibility"""
    has_version = bool(re.search(r"v\d+\.\d+", content) or "version:" in str(fm))
    if not has_version:
        return make_cell("WARN", "버전 스트링 없음")
    return make_cell("PASS", "버전 명시")


def check_7_2(content: str, is_up: bool) -> Dict:
    """Essence loss"""
    has_invariant = "INVARIANT" in content or "절대 규칙" in content
    if is_up:
        invariant_count = sum(1 for inv in UP_INVARIANTS if inv in content)
        if invariant_count < 4:
            return make_cell("FAIL", f"INVARIANT {invariant_count}/6")
        return make_cell("PASS", f"INVARIANT {invariant_count}/6")
    if not has_invariant:
        return make_cell("WARN", "절대 규칙 섹션 없음")
    return make_cell("PASS", "절대 규칙 존재")


def check_7_3(target_path: Path) -> Dict:
    """Tests"""
    evals = target_path / "evals"
    has_self_check = any(f.name == "validate.py" for f in target_path.rglob("*"))
    if evals.exists():
        return make_cell("PASS", "evals/ 존재")
    if has_self_check:
        return make_cell("WARN", "self-check만")
    return make_cell("FAIL", "evals/ 없음")


def check_7_4(target_path: Path) -> Dict:
    """Version management"""
    has_changelog = (target_path / "CHANGELOG.md").exists()
    if has_changelog:
        return make_cell("PASS", "CHANGELOG.md")
    return make_cell("WARN", "CHANGELOG 없음")


def check_8_1(content: str) -> Dict:
    """Self-diagnosis"""
    has_validate = "validate" in content.lower() or "self-check" in content.lower() or "자체 점검" in content
    if not has_validate:
        return make_cell("FAIL", "self-check 없음")
    return make_cell("PASS", "validate 언급")


def check_8_2(content: str) -> Dict:
    """Failure silence"""
    has_error_protocol = "STOP + 보고" in content or "에러 시" in content or "실패 시" in content
    if not has_error_protocol:
        return make_cell("WARN", "에러 프로토콜 불명")
    return make_cell("PASS", "에러 처리 규칙")


def check_8_3(content: str) -> Dict:
    """Improvement signal"""
    has_feedback = "thumbs" in content.lower() or "피드백" in content or "feedback" in content.lower()
    if not has_feedback:
        return make_cell("WARN", "피드백 채널 없음")
    return make_cell("PASS", "피드백 언급")


def check_8_4(content: str) -> Dict:
    """Learning accumulation"""
    has_session = "session-briefing" in content or "CHANGELOG" in content or "session_briefing" in content
    if not has_session:
        return make_cell("WARN", "학습 축적 채널 없음")
    return make_cell("PASS", "축적 언급")


# ---------- Main scan ----------

def scan_target(target_path: Path) -> Dict:
    """Scan a single skill or UP file. Return 32-cell diagnostic JSON."""
    if target_path.is_file():
        skill_md = target_path
        content = read_file(skill_md)
        files = [target_path]
    else:
        skill_md = target_path / "SKILL.md"
        content = read_file(skill_md)
        files = list(target_path.rglob("*")) if target_path.is_dir() else []

    fm = parse_frontmatter(content)
    is_up = is_up_target(target_path, content)
    skill_md_size = skill_md.stat().st_size if skill_md.exists() else 0

    cells = {}
    cells["1-1"] = check_1_1(content, files)
    cells["1-2"] = check_1_2(content, files)
    cells["1-3"] = check_1_3(content, files)
    cells["1-4"] = check_1_4(content, files)
    cells["2-1"] = check_2_1(fm, content)
    cells["2-2"] = check_2_2(fm)
    cells["2-3"] = check_2_3(fm, content)
    cells["2-4"] = check_2_4(content)
    cells["3-1"] = check_3_1(content)
    cells["3-2"] = check_3_2(content, fm)
    cells["3-3"] = check_3_3(content)
    cells["3-4"] = check_3_4(fm, target_path.name)
    cells["4-1"] = check_4_1(content)
    cells["4-2"] = check_4_2(content)
    cells["4-3"] = check_4_3(content, fm)
    cells["4-4"] = check_4_4(content)
    cells["5-1"] = check_5_1(skill_md)
    cells["5-2"] = check_5_2(content, files, skill_md_size)
    cells["5-3"] = check_5_3(content)
    cells["5-4"] = check_5_4(content)
    cells["6-1"] = check_6_1(content, fm)
    cells["6-2"] = check_6_2(fm)
    cells["6-3"] = check_6_3(content, is_up)
    cells["6-4"] = check_6_4(content, target_path.name)
    cells["7-1"] = check_7_1(content, fm)
    cells["7-2"] = check_7_2(content, is_up)
    cells["7-3"] = check_7_3(target_path if target_path.is_dir() else target_path.parent)
    cells["7-4"] = check_7_4(target_path if target_path.is_dir() else target_path.parent)
    cells["8-1"] = check_8_1(content)
    cells["8-2"] = check_8_2(content)
    cells["8-3"] = check_8_3(content)
    cells["8-4"] = check_8_4(content)

    # Score calculation
    total = 0.0
    count = 0
    for cell_id, cell in cells.items():
        score = cell["score"]
        if score is None:
            continue
        pathology = cell_id.split("-")[0]
        weight = UP_GAUGE_WEIGHTS.get(pathology, 1) if is_up else 1
        total += score * weight
        count += weight

    total_score = (total / count * 100) if count > 0 else 0
    grade = "GREEN" if total_score >= 80 else "ORANGE" if total_score >= 60 else "RED"

    return {
        "target": target_path.name,
        "target_path": str(target_path),
        "mode": "up" if is_up else "standard",
        "cells": cells,
        "total_score": round(total_score, 1),
        "grade": grade,
    }


def scan_all(skills_dir: Path) -> Dict:
    """Scan all skills in a directory."""
    results = {"scan_date": "", "total_skills": 0, "skills": {}, "aggregate": {}}
    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    results["total_skills"] = len(skill_dirs)
    for sd in skill_dirs:
        try:
            r = scan_target(sd)
            fails = sum(1 for c in r["cells"].values() if c["status"] == "FAIL")
            warns = sum(1 for c in r["cells"].values() if c["status"] == "WARN")
            results["skills"][sd.name] = {
                "total_score": r["total_score"],
                "grade": r["grade"],
                "fails": fails,
                "warns": warns,
            }
        except Exception as e:
            results["skills"][sd.name] = {"error": str(e)}
    # Aggregate by pathology
    agg = {}
    for p in PATHOLOGIES:
        scores = []
        fail_count = 0
        total_cells = 0
        for sname, sd in [(d.name, d) for d in skill_dirs]:
            try:
                r = scan_target(sd)
                for cid, c in r["cells"].items():
                    if cid.startswith(f"{p}-") and c["score"] is not None:
                        scores.append(c["score"])
                        total_cells += 1
                        if c["status"] == "FAIL":
                            fail_count += 1
            except Exception:
                continue
        if scores:
            agg[f"{p}_{PATHOLOGIES[p].split()[0]}"] = {
                "avg_score": round(sum(scores) / len(scores) * 100, 1),
                "fail_rate": round(fail_count / total_cells, 2) if total_cells else 0,
            }
    results["aggregate"] = {"by_pathology": agg}
    return results


# ---------- CLI ----------

def main():
    if len(sys.argv) < 3:
        print("Usage: python skill_scanner.py scan <target_path>", file=sys.stderr)
        print("       python skill_scanner.py scan-all <skills_dir>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    target = Path(sys.argv[2])

    if not target.exists():
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        sys.exit(2)

    if command == "scan":
        result = scan_target(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif command == "scan-all":
        result = scan_all(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"ERROR: unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
