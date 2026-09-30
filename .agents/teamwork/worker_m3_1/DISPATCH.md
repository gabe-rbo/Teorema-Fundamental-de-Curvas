# DISPATCH: Milestone M3 Worker 1 (CLI Implementation)

You are `worker_m3_1`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_1`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Target file (EXCLUSIVE WRITE OWNERSHIP): `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`

Context & References:
- Original User Request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
- Master Plan: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_2/PROJECT.md`
- Explorer Findings & Architecture Checklist: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_3/handoff.md`
- Math Engine: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_engine.py`
- Visualizer: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_viz.py`
- Test Suite: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/tests/test_teorema_fundamental.py`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Objective:
Implement `teorema-fundamental-curvas.py` adhering to:
1. Positional syntax (`python teorema-fundamental-curvas.py "1"` and `python teorema-fundamental-curvas.py "1" "1"`).
2. Short flags (`-k`, `-t`, `-i`, `-n`, `-o`) and long flags (`--curvatura`, `--torcao`, `--intervalo`, `--num-pontos`, `--output`).
3. Defaults: $\tau = "0"$, interval $[0.0, 6.28]$, points 500.
4. Validation:
   - Curvature is required (exit non-zero, code 2 on missing).
   - Inverted intervals ($s_0 \ge s_1$) rejected with non-zero exit code.
   - Number of points must be $\ge 2$.
5. Output resolution:
   - User-specified `-o` preserved.
   - Automatic naming when `-o` is omitted: `curva_engine.generate_output_filename(classification, kappa, tau, s0, s1)` written to current working directory.
6. Execution:
   - Call `curva_engine.reconstruct_curve`.
   - Call `curva_viz.export_interactive_html`.
   - Informative console prints on success (Portuguese or English: curve classification and output file path).
   - Friendly stderr on failure.
7. Verification:
   - Run: `python3 -m pytest tests/test_teorema_fundamental.py -v`.
   - Ensure all 64 tests pass with 0 failures and 0 skipped!
   - Ensure chmod +x is set on `teorema-fundamental-curvas.py`.
8. Write comprehensive `handoff.md` in your working directory and notify the orchestrator.

## 2026-09-30T15:47:19Z
You are worker_m3_1.
Read your instructions in /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_1/DISPATCH.md.
Also read /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md, /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_2/PROJECT.md, and the explorer handoff at /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_3/handoff.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py (you own exclusive write access to this file).
Set executable permissions (chmod +x).
Run tests: python3 -m pytest tests/test_teorema_fundamental.py -v. All 64 tests must pass!
Write your handoff report to /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_1/handoff.md and notify the orchestrator via send_message.
