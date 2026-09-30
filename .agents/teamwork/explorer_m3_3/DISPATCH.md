# DISPATCH: Milestone M3 Explorer 3 (Test Compliance & Acceptance Scenarios)

You are `explorer_m3_3`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_3`
Original User Request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
Project Master Plan: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_2/PROJECT.md`
Test Suite: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/tests/test_teorema_fundamental.py`

Objective:
Investigate and enumerate all test assertions and acceptance criteria that `teorema-fundamental-curvas.py` must pass:
1. Examine all 7 `@requires_cli` tests in `tests/test_teorema_fundamental.py`:
   - `test_tier1_cli_defaults`: `1` -> tau=0, s in [0, 6.28], points=500, creates file.
   - `test_tier1_cli_positional_both`: `1` `1` -> creates file.
   - `test_tier1_cli_flags_short`: `-k 2 -t 0 -i 0 3.14 -n 100 -o ...`
   - `test_tier1_cli_flags_long`: `--curvatura 1 --torcao 1 --intervalo 0 5 --num-pontos 120 --output ...`
   - `test_tier1_cli_missing_required`: no args -> exit code != 0.
   - `test_tier1_filename_custom_output_preserved`: `-o` preserves exact output path.
   - `test_tier2_interval_inverted_cli_exit_code`: `-i 5 2` -> exit code != 0.
2. Examine Acceptance Criteria from `ORIGINAL_REQUEST.md`:
   - `python teorema-fundamental-curvas.py "1" "1" -i 0 6.28` produces `helice_circular-k1-t1-I0_6.28.html`.
   - `python teorema-fundamental-curvas.py "1" -i 0 6.28` produces `circulo-k1-t0-I0_6.28.html`.
3. Provide an exact checklist of compliance criteria for Worker M3.

## 2026-09-30T15:38:11Z
You are explorer_m3_3.
Read your instructions in /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_3/DISPATCH.md.
Also read /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_2/PROJECT.md.
Investigate all 7 @requires_cli tests in tests/test_teorema_fundamental.py and acceptance criteria from ORIGINAL_REQUEST.md. Provide a concrete compliance checklist for Worker M3.
Write your findings to /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_3/handoff.md and notify the orchestrator via send_message.
