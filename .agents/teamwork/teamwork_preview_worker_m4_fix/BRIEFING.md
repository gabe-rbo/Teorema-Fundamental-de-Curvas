# BRIEFING — 2026-09-30T19:21:45Z

## Mission
Remediate the Critical RCE in `teorema-fundamental-curvas.py` `_parse_interval_bound` using `curva_engine.parse_and_validate_expression` and add dense grid checks in `curva_engine.py` for pole handling. Ensure 100% test pass and zero regressions.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m4_fix
- Original parent: 6d9b0255-066a-4324-86fb-333a362db5be
- Milestone: M4 Iteration 2 (Adversarial Remediation)

## 🔒 Key Constraints
- Remediate RCE in `_parse_interval_bound` via safe AST parsing with `curva_engine.parse_and_validate_expression`.
- Ensure no free symbols other than constants (`pi`, `e`, `E`). Reject expressions with `s` or other symbols.
- Safely convert to float (`float(expr.evalf())`) and ensure finite result.
- Clean up any leftover `pwned.txt`.
- Add dense grid checks (e.g. 2000 points) in `curva_engine.reconstruct_curve` for $\kappa(s)$ and $\tau(s)$ finiteness and $\kappa(s) \ge 0$.
- DO NOT CHEAT: Genuine implementation, no hardcoded values or dummy facades.
- Verify with `pytest tests/test_adversarial_m4.py -v`, `pytest tests/test_teorema_fundamental.py -v`, and `pytest tests/ -v`.

## Current Parent
- Conversation ID: 6d9b0255-066a-4324-86fb-333a362db5be
- Updated: 2026-09-30T19:21:45Z

## Task Summary
- **What to build**: Remediation of RCE vulnerability in CLI interval bound parsing and dense pole/non-negativity sampling in curve engine.
- **Success criteria**: All tests in `test_adversarial_m4.py` and `test_teorema_fundamental.py` pass; RCE payload blocked safely without executing arbitrary Python; CLI works seamlessly for normal usage.
- **Interface contracts**: `PROJECT.md` / `ORIGINAL_REQUEST.md`

## Key Decisions Made
- [TBD]

## Artifact Index
- `.agents/teamwork/teamwork_preview_worker_m4_fix/handoff.md` — Final handoff report
- `.agents/teamwork/teamwork_preview_worker_m4_fix/progress.md` — Progress log

## Change Tracker
- **Files modified**: [TBD]
- **Build status**: [TBD]
- **Pending issues**: [TBD]

## Quality Status
- **Build/test result**: [TBD]
- **Lint status**: [TBD]
- **Tests added/modified**: [TBD]

## Loaded Skills
- None
