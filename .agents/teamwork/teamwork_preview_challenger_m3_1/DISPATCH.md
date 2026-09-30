# Task Assignment: Challenger for Milestone M3 (CLI Interface)

You are an agent with archetype `teamwork_preview_challenger`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_challenger_m3_1`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Original user request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
Implementation target: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`

## Instructions
1. Empirically verify `teorema-fundamental-curvas.py` by executing CLI commands directly via subprocess / shell:
   - Acceptance criteria 1: `python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28` produces `helice_circular-k1-t1-I0_6.28.html` without errors (exit code 0).
   - Acceptance criteria 2: `python3 teorema-fundamental-curvas.py "1" -i 0 6.28` produces `circulo-k1-t0-I0_6.28.html` without errors (exit code 0).
   - Acceptance criteria 3: `python3 teorema-fundamental-curvas.py "1" -i 0 6.28 -o custom_out.html` correctly writes to `custom_out.html` (exit code 0).
   - Negative tests: invalid expressions, invalid interval bounds ($s_0 \ge s_1$), invalid point count ($N < 2$), missing arguments. Check exit codes and error output on stderr.
2. Provide your verdict: `APPROVE` or `REQUEST_CHANGES`.
3. Write report to `handoff.md` and notify orchestrator via `send_message`.

## 2026-09-30T15:43:50Z
You are assigned to the Fundamental Theorem of Curves project.
Your assigned working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_challenger_m3_1
Project root: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas
Original user request: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md
Your detailed task assignment: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_challenger_m3_1/DISPATCH.md
Implementation to verify: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py

Empirically challenge teorema-fundamental-curvas.py by executing CLI commands directly:
- python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28
- python3 teorema-fundamental-curvas.py "1" -i 0 6.28
- python3 teorema-fundamental-curvas.py "1" -i 0 6.28 -o custom_out.html
- Negative tests for exit codes (1 for domain errors, 2 for missing/invalid CLI syntax).
Provide your verdict: APPROVE or REQUEST_CHANGES.
Write report to handoff.md and notify orchestrator with send_message.

