#!/usr/bin/env python3
"""nine_rules_scanner.py — skill-doctor v2.2 9룰 갭 진단 스캐너
7강제룰 + 2선택룰. usage: python3 nine_rules_scanner.py <skill-dir>
"""
import sys, os, re, json

REQUIRED = [
    ("boundaries", r"^## (Skill )?Boundaries", "FAIL"),
    ("when_to_use", r"^## When to Use|언제 (쓰|발동)", "FAIL"),
    ("prerequisites", r"^## Prerequisites|시작 전 체크", "FAIL"),
    ("output_path", r"^## Output Path|산출물.*경로", "FAIL"),
    ("reference_index", r"^## Reference Index", "FAIL_IF_REF_DIR"),
    ("next_phase", r"^## Next Phase|다음엔 →", "FAIL"),
    ("failure_modes", r"^## (Failure Modes|Gotchas)|함정", "FAIL"),
]

def main(skill_dir):
    skill_dir = skill_dir.rstrip("/")
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        print(json.dumps({"error": f"SKILL.md 없음: {skill_md}"}))
        return 1
    s = open(skill_md).read()
    has_refs = os.path.isdir(os.path.join(skill_dir, "references"))
    result = {"target": os.path.basename(skill_dir), "nine_rules": {}}
    score = 0
    for name, pattern, sev in REQUIRED:
        m = re.search(pattern, s, re.MULTILINE)
        if m:
            result["nine_rules"][name] = {"status": "PASS", "evidence": m.group(0)[:60]}
            score += 10
        else:
            if sev == "FAIL_IF_REF_DIR" and not has_refs:
                result["nine_rules"][name] = {"status": "N/A", "evidence": "references/ 없음"}
                score += 10
            else:
                result["nine_rules"][name] = {"status": "FAIL", "evidence": "섹션 누락"}
    # frontmatter
    fm_m = re.search(r"^---\n(.*?)\n---", s, re.DOTALL)
    fm = fm_m.group(1) if fm_m else ""
    # description (multi 우선)
    m_multi = re.search(r"^description:\s*\|\s*\n((?:  .+\n?)+)", fm, re.MULTILINE)
    m_single = re.search(r"^description:\s*([^|\n].+)$", fm, re.MULTILINE)
    desc = (m_multi.group(1) if m_multi else (m_single.group(1) if m_single else "")).strip()
    first_sent = desc.split(".")[0] if desc else ""
    compressed = re.search(r"\d+층|\d+도메인|\d+모드|\d+셀|×", first_sent)
    if first_sent and not compressed:
        result["nine_rules"]["plain_first_sentence"] = {"status": "PASS", "evidence": first_sent[:60]}
        score += 5
    else:
        result["nine_rules"]["plain_first_sentence"] = {"status": "WARN", "evidence": f"압축어: {first_sent[:60]}"}
    # metadata
    if re.search(r"^metadata:", fm, re.MULTILINE) and "author:" in fm and "version:" in fm:
        result["nine_rules"]["metadata_block"] = {"status": "PASS", "evidence": "metadata.author+version OK"}
        score += 5
    else:
        result["nine_rules"]["metadata_block"] = {"status": "INFO", "evidence": "metadata 표준 누락"}
    result["score"] = score
    result["max_score"] = 80
    result["grade"] = "GREEN" if score >= 70 else "YELLOW" if score >= 50 else "RED"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: nine_rules_scanner.py <skill-dir>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
