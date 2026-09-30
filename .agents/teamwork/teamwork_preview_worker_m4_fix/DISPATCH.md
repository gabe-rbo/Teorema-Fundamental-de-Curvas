# Dispatch: Worker M4 Fix (Adversarial Remediation)

## Mission
Remediate the Critical RCE vulnerability identified in `teorema-fundamental-curvas.py` and implement interior pole dense sampling safeguards in `curva_engine.py`.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Inputs
- ORIGINAL_REQUEST.md: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md
- Challenger Report: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_challenger_m4_1/handoff.md
- Target Files:
  - /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py
  - /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_engine.py

## Specific Tasks
1. In `teorema-fundamental-curvas.py`:
   - Replace unsafe `sp.sympify(val)` in `_parse_interval_bound` with safe AST parsing using `curva_engine.parse_and_validate_expression(val)`.
   - Ensure the parsed expression contains NO free symbols other than constants (`pi`, `e`, `E`). Reject expressions containing the parameter variable `s` or other symbols.
   - Safely convert to float (`float(expr.evalf())`) and ensure the result is finite.
   - Remove any leftover test artifacts like `pwned.txt`.

2. In `curva_engine.py`:
   - In `reconstruct_curve`, enhance domain validation by checking $\kappa(s)$ and $\tau(s)$ over a dense grid (e.g., 2000 points across $[s_0, s_1]$) in addition to the user discretization grid, and raise ValueError if any value is non-finite or $\kappa < 0$, preventing solver step-collapse and hangs on unaligned interior poles.

3. Verification:
   - Run `pytest tests/test_adversarial_m4.py -v` (confirm 26/26 pass, and `test_interval_bound_security_injection` passes).
   - Run `pytest tests/test_teorema_fundamental.py -v` (confirm 64/64 pass).
   - Run `pytest tests/ -v` (confirm 100% pass across all tests).
   - Verify CLI commands still execute cleanly with exit code 0 for circle and helix.

4. Write handoff report to:
   `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m4_fix/handoff.md`

## 2026-09-30T19:21:22Z
Received dispatch from parent (6d9b0255-066a-4324-86fb-333a362db5be):
Remediate the Critical RCE in `teorema-fundamental-curvas.py` `_parse_interval_bound` using `curva_engine.parse_and_validate_expression` and add dense grid checks in `curva_engine.py` for pole handling. Clean up any pwned.txt test file. Run `pytest tests/test_adversarial_m4.py -v`, `pytest tests/test_teorema_fundamental.py -v`, and `pytest tests/ -v`.
Write your handoff report to /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m4_fix/handoff.md. Notify caller via send_message when done.
