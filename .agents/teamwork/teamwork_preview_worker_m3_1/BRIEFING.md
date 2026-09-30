# BRIEFING — 2026-09-30T15:42:00Z

## Mission
Implement and verify `teorema-fundamental-curvas.py`, the CLI interface and integration entrypoint for reconstructing space/plane curves and generating responsive Plotly HTML visualizations.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m3_1
- Original parent: 0b0dffe7-95be-4cd3-9ff5-acde191dd517
- Milestone: M3 (CLI Interface & Integration)

## 🔒 Key Constraints
- Exclusively own and write `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`
- Do NOT modify `curva_engine.py` or `curva_viz.py`
- Follow integrity mandate: no hardcoding, genuine logic only
- Exit code 1 for mathematical / domain / validation errors
- Exit code 2 for argparse syntax / argument errors
- Pass 100% of tests in `tests/test_teorema_fundamental.py` (all 64 tests pass)

## Current Parent
- Conversation ID: 0b0dffe7-95be-4cd3-9ff5-acde191dd517
- Updated: 2026-09-30T15:36:34Z

## Task Summary
- **What to build**: `teorema-fundamental-curvas.py` with shebang, executable permissions, positional & flag argument parsing, validation, engine + viz integration, automatic sanitized filename generation, and user-friendly console reporting.
- **Success criteria**: All 64 tests in `tests/test_teorema_fundamental.py` pass; direct CLI invocations generate expected HTML files.
- **Interface contracts**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md`
- **Code layout**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md`

## Key Decisions Made
- Used `argparse.ArgumentParser` with positional arguments `pos1`, `pos2` (`nargs='?'`) and flags `-k/--curvatura`, `-t/--torcao` to seamlessly support both purely positional (`1 1`), mixed (`1 -t 1`), and flagged (`-k 1 -t 1`) invocations.
- Check `$s_0 < s_1$` and `$N \ge 2$` prior to calling engine, emitting clear errors to stderr and exiting with code 1.
- Catch `ValueError`, `ZeroDivisionError`, `RuntimeError` from engine/viz, emit diagnostic message to stderr, and exit with code 1.
- Standard argparse syntax / required argument omission exits with code 2.
- Automatically call `curva_engine.generate_output_filename` when `--output` is not specified.
- Set executable bit (`chmod +x`) and shebang `#!/usr/bin/env python3`.

## Artifact Index
- `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py` — Main CLI entrypoint script (executable)
- `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m3_1/progress.md` — Liveness and step tracking
- `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m3_1/handoff.md` — 5-component handoff report

## Change Tracker
- **Files modified**: `teorema-fundamental-curvas.py` (created, 257 lines, executable)
- **Build status**: pytest 64 passed, 0 failed, 0 skipped
- **Pending issues**: none

## Quality Status
- **Build/test result**: 64 passed, 0 failed, 0 skipped in 9.99s
- **Lint status**: clean (py_compile validated)
- **Tests added/modified**: activated all 7 CLI tests in `tests/test_teorema_fundamental.py`

## Loaded Skills
- None
