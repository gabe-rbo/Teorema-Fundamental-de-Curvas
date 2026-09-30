# BRIEFING — 2026-09-30T15:48:00Z

## Mission
Implement `teorema-fundamental-curvas.py` CLI executable, connect curva_engine and curva_viz, validate and pass all test suites.

## 🔒 My Identity
- Archetype: worker_m3_1
- Roles: implementer, qa, specialist
- Working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_1
- Original parent: c02fecd8-2c8f-44e6-bc31-daf5123708ba
- Milestone: M3 (CLI Interface & Integration)

## 🔒 Key Constraints
- Exclusive write ownership: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py
- Mandatory Integrity: No cheating, no hardcoding, genuine implementation.
- All tests must pass (python3 -m pytest tests/test_teorema_fundamental.py -v).
- Ensure executable permissions (chmod +x).
- Dual invocation syntax (positional and short/long flags).
- Automatic output naming if -o omitted.
- Input validation (s0 < s1, num_points >= 2, curvature required).

## Current Parent
- Conversation ID: c02fecd8-2c8f-44e6-bc31-daf5123708ba
- Updated: not yet

## Task Summary
- **What to build**: teorema-fundamental-curvas.py CLI script
- **Success criteria**: All tests pass in tests/test_teorema_fundamental.py with 0 failures, 0 skipped.
- **Interface contracts**: curva_engine.reconstruct_curve, curva_engine.generate_output_filename, curva_viz.export_interactive_html
- **Code layout**: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py

## Change Tracker
- **Files modified**: None yet
- **Build status**: Pending
- **Pending issues**: None

## Quality Status
- **Build/test result**: Pending
- **Lint status**: Clean
- **Tests added/modified**: 0 (evaluating existing suite)

## Loaded Skills
None

## Key Decisions Made
- Use argparse with optional positional arguments and flags for curvature and torsion to support both positional and flagged syntax.

## Artifact Index
- handoff.md — will contain final handoff report
- progress.md — liveness heartbeat
