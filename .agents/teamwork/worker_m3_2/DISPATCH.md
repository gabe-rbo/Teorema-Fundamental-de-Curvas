# DISPATCH: Milestone M3 Worker 2 (Replacement & Verification)

You are `worker_m3_2`, the replacement worker for Milestone M3.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_2`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Target file: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`

Context:
`worker_m3_1` already created `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py` before hitting a quota timeout.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Tasks:
1. Inspect `teorema-fundamental-curvas.py`. Verify that it satisfies all requirements from `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_3/handoff.md`:
   - Positional arguments (`"1"` and `"1" "1"`)
   - Flags (`-k`, `-t`, `-i`, `-n`, `-o`, `--curvatura`, etc.)
   - Defaults: $\tau=0$, interval `[0.0, 6.28]`, points 500
   - Error exit codes: missing curvature -> code 2, $s_0 \ge s_1$ -> code 1
   - Automatic naming when `-o` is omitted and custom name preserved when `-o` is given.
   - If any small bug or edge case is present, fix it.
2. Ensure executable permissions: `chmod +x teorema-fundamental-curvas.py`.
3. Run the automated test suite:
   `python3 -m pytest tests/test_teorema_fundamental.py -v`
   Ensure ALL 64 tests pass with 0 failures and 0 skipped!
4. Run the acceptance criteria commands:
   - `python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28` -> generates `helice_circular-k1-t1-I0_6.28.html`
   - `python3 teorema-fundamental-curvas.py "1" -i 0 6.28` -> generates `circulo-k1-t0-I0_6.28.html`
   - Clean up those two generated test HTML files after verifying.
5. Write your comprehensive completion report to `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_2/handoff.md`.
6. Send a completion message to the orchestrator via `send_message`.

## 2026-09-30T19:05:45Z
You are worker_m3_2.
Read your instructions in /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_2/DISPATCH.md.
Also read /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md, /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_2/PROJECT.md, and /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/explorer_m3_3/handoff.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Inspect, verify, and finalize /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py.
Ensure chmod +x is set.
Run: python3 -m pytest tests/test_teorema_fundamental.py -v. Ensure 100% of all 64 tests pass with 0 skipped and 0 failed.
Verify acceptance criteria commands.
Write your full handoff report to /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_2/handoff.md and notify the orchestrator via send_message.
