# skill-doctor

Diagnostic engine for skills and UP (User Preferences) — built on an **8 pathologies × 4 causes = 32-cell matrix**.

## What it does

Scans a target skill or UP document and reports:
- **32-cell matrix** score (each cell = pathology × cause)
- **Red-flag top-3** with evidence
- **Triage prescription** (P0 / P1 / P2) handed off to `skill-builder`

## 8 Pathologies

1. Latency
2. Inaccuracy
3. Opacity
4. Fragility
5. Bloat
6. Isolation
7. Rigidity
8. Meta-blindness

UP mode applies ×3 weight to ⑤–⑧.

## 3 Modes

| Mode | Purpose |
|---|---|
| Diagnose | Single target → full 32-cell report |
| Prescribe | Triage + handoff to skill-builder |
| Monitor | Ecosystem-wide scan → dashboard |

## Install

Drop `skill-doctor.skill` into your Cowork skills folder.

## Triggers

`스킬닥터`, `skill doctor`, `스킬진단`, `UP진단`, `스킬검진`, `스킬감사`, `32셀매트릭스`, `8대병리`.

---

한국어 README: [README.ko.md](./README.ko.md)
