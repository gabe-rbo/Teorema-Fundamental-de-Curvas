# DISPATCH: Milestone M3 Worker 3 (Syntax Hardening)

You are `worker_m3_3`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_3`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Target file: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py` (EXCLUSIVE WRITE OWNERSHIP)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Context:
Challenger 1 found that expressions with consecutive operator tokens such as `1++s` or `--s` are accepted by Python's unary AST parser as `1 + (+s)`. To strictly enforce standard algebraic syntax and satisfy adversarial testing:
In `teorema-fundamental-curvas.py` (in `run_pipeline` or validation), reject expressions that contain consecutive `++` or `--` (e.g. `re.search(r'(\+{2,}|-{2,})', expr)`) with a clear error message to `sys.stderr` and return code 1.

Tasks:
1. Add this validation to `teorema-fundamental-curvas.py` for both `args.curvatura` and `args.torcao`.
2. Verify:
   `python3 teorema-fundamental-curvas.py "1++s"` exits with code 1.
3. Run:
   `python3 -m pytest tests/test_teorema_fundamental.py -v`
   Ensure 100% of all 64 tests pass!
4. Write handoff to `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_3/handoff.md`.

## 2026-09-30T19:16:23Z
You are worker_m3_3.
Read your instructions in /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_3/DISPATCH.md.
Also read /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_2/PROJECT.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Add consecutive operator validation (`++` and `--`) in /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py.
Verify python3 teorema-fundamental-curvas.py "1++s" exits with code 1.
Run: python3 -m pytest tests/test_teorema_fundamental.py -v.
Write your handoff report to /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/worker_m3_3/handoff.md and notify the orchestrator via send_message.
