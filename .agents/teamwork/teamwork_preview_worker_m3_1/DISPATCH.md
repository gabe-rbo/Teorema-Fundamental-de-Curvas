# Task Assignment: Milestone M3 (CLI Interface & Main Script Worker)

You are an agent with archetype `teamwork_preview_worker`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m3_1`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Original user request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
Project master specification: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md`
CLI Survey report: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_explorer_survey_2/handoff.md`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Write Ownership
You EXCLUSIVELY own and write:
- `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`
Do NOT modify `curva_engine.py` or `curva_viz.py`.

## Instructions & Scope
1. Read `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `teamwork_preview_explorer_survey_2/handoff.md`.
2. Implement `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`:
   - Shebang `#!/usr/bin/env python3` and executable permissions.
   - Argument parsing supporting both positional and flagged formats:
     - `curvatura` (positional or `-k/--curvatura`)
     - `torcao` (positional or `-t/--torcao`, default: `"0"`)
     - `-i/--intervalo S0 S1` (default: `[0.0, 6.28]`, floats)
     - `-n/--num-pontos N` (default: `500`, int)
     - `-o/--output ARQUIVO` (optional str)
   - Filename generation when `-o` is not provided:
     Calls `curva_engine.generate_output_filename(curve_data.classification, args.curvatura, args.torcao, s0, s1)`
     yielding `<identificacao_da_curva>-k<curvatura>-t<torcao>-I<InicioIntervalo_FimIntervalo>.html`.
   - Execution pipeline:
     1. Validate args ($s_0 < s_1$, $N \ge 2$).
     2. Call `curva_engine.reconstruct_curve(args.curvatura, args.torcao, s0, s1, N)`.
     3. Call `curva_viz.export_interactive_html(curve_data, output_path)`.
     4. Print user-friendly summary to stdout with exit code 0.
   - Robust error handling:
     - Print error message to stderr and exit with code 1 for invalid math expressions, domain errors/singularities, negative curvature, inverted intervals, or point count < 2.
     - Argparse standard errors exit with code 2.
3. Verify test suite:
   - Run `python3 -m pytest tests/test_teorema_fundamental.py -v`.
   - All 64 tests (including CLI and E2E tests) must now pass with 0 skipped and 0 failed!
   - Execute CLI commands directly to verify:
     - `python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28` produces `helice_circular-k1-t1-I0_6.28.html`
     - `python3 teorema-fundamental-curvas.py "1" -i 0 6.28` produces `circulo-k1-t0-I0_6.28.html`
     - `python3 teorema-fundamental-curvas.py "1" -i 0 6.28 -o test_out.html` produces `test_out.html`
4. Write your handoff report to `handoff.md` and notify the orchestrator via `send_message`.

## 2026-09-30T15:36:34Z
You are assigned to the Fundamental Theorem of Curves project.
Your assigned working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m3_1
Project root: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas
Original user request: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md
Your detailed task assignment: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m3_1/DISPATCH.md
Project specification: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

You exclusively own:
- /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py

Implement teorema-fundamental-curvas.py:
- Shebang #!/usr/bin/env python3 and executable permissions
- Positional & flagged CLI arguments (curvatura, torcao [default "0"], -i/--intervalo [default 0 6.28], -n/--num-pontos [default 500], -o/--output)
- Automatic sanitized filename generation when -o is omitted: <identificacao_da_curva>-k<curvatura>-t<torcao>-I<InicioIntervalo_FimIntervalo>.html
- Integration: calls curva_engine.reconstruct_curve and curva_viz.export_interactive_html
- Error handling: exits with code 1 on mathematical/domain/interval errors, exits with code 2 on argparse syntax errors
Run the full test suite (python3 -m pytest tests/test_teorema_fundamental.py -v) to verify that all 64 tests pass!
Execute the CLI commands directly to test:
- python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28
- python3 teorema-fundamental-curvas.py "1" -i 0 6.28
- python3 teorema-fundamental-curvas.py "1" -i 0 6.28 -o test_out.html
Write your handoff report to handoff.md in your working directory and notify the orchestrator with send_message.
