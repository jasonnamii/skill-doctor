#!/usr/bin/env python3
"""
skill-doctor report generator
Takes scan JSON and produces markdown diagnostic report.

Usage:
    python report_generator.py --scan-result scan.json --target name [--mode diagnose|monitor] --out report.md
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List


PATHOLOGY_LABELS = {
    "1": "① 느림",
    "2": "② 부정확",
    "3": "③ 불통",
    "4": "④ 취약",
    "5": "⑤ 비대",
    "6": "⑥ 고립",
    "7": "⑦ 진화불능",
    "8": "⑧ 무자각",
}

STATUS_EMOJI = {"PASS": "🟢", "WARN": "🟠", "FAIL": "🔴", "N/A": "⚪"}

STANDARD_ACTIONS = {
    "1-1": ("병목 해소", "병렬 허용 구간 명시, 허브스포크 재설계"),
    "1-2": ("과부하 방지", "동시 로드 제한, 경로 분기 추가"),
    "1-3": ("재시도 상한", "max 2회 하드캡 추가"),
    "1-4": ("분기 단순화", "표 기반 결정으로 리팩토링"),
    "2-1": ("오발동 차단", "P1에서 일반 키워드 제거"),
    "2-2": ("트리거 확장", "P1 5개+, P2 한/영 병기, P3 영어 추가"),
    "2-3": ("의도 일치", "description과 본문 동사 통일"),
    "2-4": ("결정성 확보", "모호 표현 제거, 표/규칙으로 대체"),
    "3-1": ("스텔스 준수", "내부 라벨을 응답에서 제거"),
    "3-2": ("학습곡선 완화", "예시 1개+ 추가, P2 자연어 보강"),
    "3-3": ("피드백 강화", "Gotchas 3행+ 추가"),
    "3-4": ("이름 개선", "기능을 암시하는 이름으로 변경"),
    "4-1": ("인젝션 방어", "INVARIANT·게이트키퍼 명시"),
    "4-2": ("엣지케이스 커버", "PREFLIGHT에 입력 검증 추가"),
    "4-3": ("의존 선언", "vault_dependency + fallback 추가"),
    "4-4": ("상태 재검증", "CONTEXT_WATCH·PIVOT 프로토콜"),
    "5-1": ("크기 축소", "references/ 분리 (허브 5KB 목표)"),
    "5-2": ("허브스포크 전환", "본문 → 스포크 이동, 포인터 추가"),
    "5-3": ("맥락 정제", "내부 용어를 응답에서 제거"),
    "5-4": ("중복 제거", "공통 레퍼런스는 허브에 요약"),
    "6-1": ("NOT 추가", "대체 스킬 라우팅 명시"),
    "6-2": ("트리거 차별화", "P1 중복 해소 or NOT 라우팅"),
    "6-3": ("UP 준수", "SKILL_PRECEDENCE 명시, INVARIANT 보호"),
    "6-4": ("단방향화", "순환 호출 제거"),
    "7-1": ("버전 명시", "frontmatter에 version 필드"),
    "7-2": ("INVARIANT 보호", "절대 규칙 섹션 명시"),
    "7-3": ("evals 추가", "evals/cases.json 3개+ 샘플"),
    "7-4": ("CHANGELOG 추가", "변경이력 파일 생성"),
    "8-1": ("self-check", "scripts/validate.py 추가"),
    "8-2": ("에러 프로토콜", "STOP + 보고 규칙 명시"),
    "8-3": ("피드백 안내", "thumbs-down 경로 Gotchas에"),
    "8-4": ("축적 연계", "session-briefing + CHANGELOG 연동"),
}

EFFORT = {
    "1-1": 30, "1-2": 20, "1-3": 10, "1-4": 30,
    "2-1": 10, "2-2": 10, "2-3": 20, "2-4": 20,
    "3-1": 10, "3-2": 15, "3-3": 10, "3-4": 30,
    "4-1": 15, "4-2": 20, "4-3": 20, "4-4": 30,
    "5-1": 60, "5-2": 60, "5-3": 20, "5-4": 20,
    "6-1": 5, "6-2": 15, "6-3": 30, "6-4": 60,
    "7-1": 5, "7-2": 20, "7-3": 60, "7-4": 10,
    "8-1": 30, "8-2": 15, "8-3": 10, "8-4": 30,
}


def render_matrix(cells: Dict) -> str:
    """Render 8x4 matrix as markdown table."""
    lines = ["| | 원인1 | 원인2 | 원인3 | 원인4 |",
             "|---|---|---|---|---|"]
    for p in "12345678":
        row = [PATHOLOGY_LABELS[p]]
        for c in "1234":
            cell = cells.get(f"{p}-{c}", {"status": "N/A"})
            row.append(STATUS_EMOJI[cell["status"]])
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def rank_red_flags(cells: Dict, top_n: int = 3) -> List[Dict]:
    """Rank FAIL cells by severity."""
    # Priority: FAIL first, then by effort (lower = more critical to fix fast)
    fails = [(cid, c) for cid, c in cells.items() if c["status"] == "FAIL"]
    # Sort: essence (2,5,7) first, then others
    essence_priority = {"2": 0, "5": 0, "7": 0, "4": 1, "8": 1, "1": 2, "3": 2, "6": 2}
    fails.sort(key=lambda x: (essence_priority.get(x[0].split("-")[0], 3), x[0]))
    return [{"cell": cid, "evidence": c["evidence"]} for cid, c in fails[:top_n]]


def triage(cells: Dict) -> Dict:
    """Triage by priority."""
    p0, p1, p2 = [], [], []
    for cid, cell in cells.items():
        if cell["status"] == "FAIL":
            # P0: critical pathologies (2, 5, 7)
            if cid.split("-")[0] in ("2", "5", "7"):
                p0.append(cid)
            else:
                p1.append(cid)
        elif cell["status"] == "WARN":
            p2.append(cid)
    return {"P0": p0, "P1": p1, "P2": p2}


def render_prescription(cells: Dict, triage_result: Dict) -> str:
    """Render prescription section."""
    out = ["## 💊 처방 우선순위\n"]
    out.append("| 순위 | 병리·원인 | 액션 | 공수(분) |")
    out.append("|---|---|---|---|")
    for priority in ("P0", "P1", "P2"):
        for cid in triage_result.get(priority, []):
            cell = cells[cid]
            action_name, action_desc = STANDARD_ACTIONS.get(cid, ("-", "-"))
            effort = EFFORT.get(cid, 15)
            p_label = PATHOLOGY_LABELS.get(cid.split("-")[0], "?")
            out.append(f"| {priority} | {p_label}-{cid.split('-')[1]} | {action_name}: {action_desc} | {effort} |")
    return "\n".join(out)


def generate_diagnose_report(scan_result: Dict, target: str) -> str:
    """Generate single-skill diagnostic report."""
    today = date.today().isoformat()
    mode = scan_result.get("mode", "standard")
    score = scan_result.get("total_score", 0)
    grade = scan_result.get("grade", "UNKNOWN")
    grade_emoji = {"GREEN": "🟢", "ORANGE": "🟠", "RED": "🔴"}.get(grade, "⚪")

    cells = scan_result.get("cells", {})
    red_flags = rank_red_flags(cells)
    triage_result = triage(cells)

    sections = []
    sections.append(f"# 🩺 skill-doctor 진단 리포트")
    sections.append("")
    sections.append(f"**대상:** {target}")
    sections.append(f"**모드:** {mode}")
    sections.append(f"**일시:** {today}")
    sections.append(f"**총점:** {grade_emoji} {score}/100")
    sections.append("")

    sections.append("## 8×4 매트릭스")
    sections.append("")
    sections.append(render_matrix(cells))
    sections.append("")

    if red_flags:
        sections.append("## 🔴 레드플래그 Top3")
        sections.append("")
        for i, rf in enumerate(red_flags, 1):
            cid = rf["cell"]
            p_label = PATHOLOGY_LABELS.get(cid.split("-")[0], "?")
            sections.append(f"{i}. **[{p_label}-{cid.split('-')[1]}]** {rf['evidence']}")
        sections.append("")
    else:
        sections.append("## 🟢 레드플래그 없음\n")

    sections.append(render_prescription(cells, triage_result))
    sections.append("")

    sections.append("## 🔜 다음 단계")
    sections.append("")
    sections.append("\"처방해줘\" 발동 시 각 항목의 구체적 수정안 도출 (skill-builder에 위임).")
    sections.append("")

    return "\n".join(sections)


def generate_monitor_report(scan_result: Dict) -> str:
    """Generate ecosystem dashboard."""
    today = date.today().isoformat()
    total = scan_result.get("total_skills", 0)
    skills = scan_result.get("skills", {})

    # Grade distribution
    green = sum(1 for s in skills.values() if s.get("grade") == "GREEN")
    orange = sum(1 for s in skills.values() if s.get("grade") == "ORANGE")
    red = sum(1 for s in skills.values() if s.get("grade") == "RED")

    # Red flag skills (Top 5 by score ascending)
    valid = [(n, s) for n, s in skills.items() if "total_score" in s]
    valid.sort(key=lambda x: x[1]["total_score"])
    top5_red = valid[:5]

    sections = []
    sections.append("# 📊 Skill 생태계 대시보드")
    sections.append("")
    sections.append(f"**스캔일:** {today}")
    sections.append(f"**총 스킬:** {total}개")
    sections.append("")

    sections.append("## 등급 분포")
    sections.append("")
    sections.append("| 등급 | 개수 | 비율 |")
    sections.append("|---|---|---|")
    if total > 0:
        sections.append(f"| 🟢 (≥80) | {green} | {green*100//total}% |")
        sections.append(f"| 🟠 (60-79) | {orange} | {orange*100//total}% |")
        sections.append(f"| 🔴 (<60) | {red} | {red*100//total}% |")
    sections.append("")

    if top5_red:
        sections.append("## 🔴 레드플래그 스킬 Top5")
        sections.append("")
        sections.append("| 순위 | 스킬 | 총점 | FAIL | WARN |")
        sections.append("|---|---|---|---|---|")
        for i, (name, s) in enumerate(top5_red, 1):
            sections.append(f"| {i} | {name} | {s['total_score']} | {s.get('fails', '-')} | {s.get('warns', '-')} |")
        sections.append("")

    agg = scan_result.get("aggregate", {}).get("by_pathology", {})
    if agg:
        sections.append("## 병리별 생태계 건강")
        sections.append("")
        sections.append("| 병리 | 평균 점수 | FAIL 비율 |")
        sections.append("|---|---|---|")
        for key, val in agg.items():
            sections.append(f"| {key} | {val.get('avg_score', '-')} | {val.get('fail_rate', '-')} |")
        sections.append("")

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-result", required=True)
    parser.add_argument("--target", default="skill")
    parser.add_argument("--mode", default="diagnose", choices=["diagnose", "monitor"])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    scan = json.loads(Path(args.scan_result).read_text(encoding="utf-8"))

    if args.mode == "monitor":
        report = generate_monitor_report(scan)
    else:
        report = generate_diagnose_report(scan, args.target)

    Path(args.out).write_text(report, encoding="utf-8")
    print(f"Report written: {args.out}")


if __name__ == "__main__":
    main()
