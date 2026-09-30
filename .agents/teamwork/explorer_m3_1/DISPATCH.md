# DISPATCH: Milestone M3 Explorer 1 (CLI Argument Parsing & Validation)

You are `explorer_m3_1`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_1`
Original User Request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
Project Master Plan: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_2/PROJECT.md`
Test Suite: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/tests/test_teorema_fundamental.py`

Objective:
Investigate and design the CLI argument parsing architecture for `teorema-fundamental-curvas.py`:
1. How to support BOTH positional syntax (`python teorema-fundamental-curvas.py "1"` and `python teorema-fundamental-curvas.py "1" "1"`) AND flag syntax (`-k / --curvatura`, `-t / --torcao`) seamlessly in argparse.
2. Short and long flags: `-k/--curvatura`, `-t/--torcao`, `-i/--intervalo S0 S1`, `-n/--num-pontos N`, `-o/--output PATH`.
3. Validation rules:
   - At least curvature must be provided (exit code 2 if missing).
   - Interval must satisfy s0 < s1 (exit code 1 or 2 if s0 >= s1).
   - Number of points must be >= 2.
4. Provide concrete code structure recommendations for Worker M3.
5. Write your report to `handoff.md` in your working directory and notify the orchestrator.

## 2026-09-30T15:38:11Z
From: c02fecd8-2c8f-44e6-bc31-daf5123708ba
You are explorer_m3_1.
Read your instructions in /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_1/DISPATCH.md.
Also read /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_2/PROJECT.md.
Investigate CLI argument parsing architecture for teorema-fundamental-curvas.py (argparse design supporting both positional and flagged args, intervals, points, output, and validation).
Write your findings to /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_1/handoff.md and notify the orchestrator via send_message.
