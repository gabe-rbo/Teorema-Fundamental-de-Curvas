# Review & Adversarial Challenge Report: Milestone M1 (Math Engine)

**Reviewer / Critic**: `teamwork_preview_reviewer_m1_2`  
**Target**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_engine.py`  
**Milestone**: M1 (Math Engine & Curve Classification)  
**Date**: 2026-09-30  
**Verdict**: **APPROVE**

---

## 1. Observation

1. **Integrity Assessment**:
   - Source inspection of `curva_engine.py` (lines 1–641):
     - No hardcoded test outputs or synthetic return values detected.
     - ODE integration is genuinely executed via `scipy.integrate.solve_ivp` with `DOP853` (fallback `RK45`, lines 538–564).
     - Curve classification uses genuine symbolic differentiation via SymPy with dual-layer numerical polynomial/residual fallbacks (lines 299–433).
     - Modified Gram-Schmidt projection on $SO(3)$ is dynamically vectorized and mathematically rigorous (lines 261–292).
     - **Integrity Violation Check**: PASS (No cheating, no facade, no shortcuts).

2. **Automated Test Execution**:
   - Command: `python3 -m pytest tests/test_teorema_fundamental.py -v`
     - Result: `51 passed, 13 skipped, 3 warnings in 0.91s`
     - All 51 applicable tests in Tiers 1–4 passed with 0 failures.
     - The 13 skipped tests correspond to Milestone M2 (`curva_viz.py`) and Milestone M3 (`teorema-fundamental-curvas.py`), as expected per `PROJECT.md`.
   - Command: `python3 -m pytest tests/test_curva_engine_stress.py -v`
     - Result: `49 passed, 2 warnings in 3.18s`
     - All 49 adversarial stress tests (long-range integration up to $s \in [0, 500]$, 10,000 points, 100 orbits, high-frequency oscillations, $C^0$ non-differentiable curvature) passed with 0 failures.

3. **Mathematical Benchmarks & Orthonormality**:
   - Circle Benchmark ($\kappa=2, \tau=0$ over $[0, \pi/2]$):
     - Endpoint error $< 2.5 \times 10^{-9}$ (vs required $< 10^{-3}$).
     - Circle closure error over $[0, \pi]$ is $< 8.1 \times 10^{-10}$ (vs required $< 10^{-3}$).
   - Helix Benchmark ($\kappa=1, \tau=1$ over $[0, 2\pi\sqrt{2}]$):
     - Analytical Frenet trajectory comparison max error $< 2.7 \times 10^{-9}$ (vs required $< 10^{-3}$).
     - Proper rigid motion isometry to canonical cylinder helix verified within $10^{-14}$.
   - Straight Line Benchmark ($\kappa=0, \tau=0$ over $[0, 10]$):
     - Endpoint trajectory error $< 5.4 \times 10^{-15}$.
   - Clothoid Benchmark ($\kappa(s)=s, \tau=0$ over $[0, 5]$):
     - Scipy Fresnel integral comparison max error $< 4.9 \times 10^{-9}$.
   - Frame Orthonormality on $SO(3)$:
     - $|\|T\| - 1| \le 2.22 \times 10^{-16}$, $|\|N\| - 1| \le 2.22 \times 10^{-16}$, $|\|B\| - 1| \le 4.44 \times 10^{-16}$.
     - $|T \cdot N| \le 1.67 \times 10^{-16}$, $|T \cdot B| \le 1.11 \times 10^{-16}$, $|N \cdot B| \le 1.11 \times 10^{-16}$.
     - $|\det([T, N, B]) - 1| \le 8.88 \times 10^{-16}$.
     - Frame orthonormality maintained to machine precision ($< 10^{-14}$) even over $s \in [0, 500]$.

4. **AST Security Whitelist**:
   - Allowed nodes (`_ALLOWED_AST_NODES`, lines 45–60) strictly limit expressions to basic arithmetic and unary operations, constants, and function calls.
   - Node identifiers are restricted to `{"s", "pi", "E", "e"}` and `_ALLOWED_MATH_FUNCS`.
   - Function calls (`ast.Call`) require direct name identifiers matching `_ALLOWED_MATH_FUNCS` with no keyword arguments.
   - Unauthorized AST nodes (`Attribute`, `Subscript`, `Lambda`, `Import`, `List`, `Dict`) and dangerous built-ins (`__import__`, `eval`, `exec`, `open`, `system`) are rejected with `ValueError`.

5. **8-Class Curve Classification & Lancret's Theorem**:
   - `("0", "0")` and `("0", "5")` -> `reta`
   - `("2", "0")` -> `circulo`
   - `("1", "1")` -> `helice_circular`
   - `("1 + s", "2 + 2*s")` -> `helice_cilindrica_geral` (Lancret's Theorem $\tau/\kappa = 2$)
   - `("s**2", "3*s**2")` -> `helice_cilindrica_geral` (Lancret's Theorem $\tau/\kappa = 3$)
   - `("sin(s)", "sin(s)")` -> `helice_cilindrica_geral`
   - `("2*s", "0")` -> `espiral_de_cornu`
   - `("1/(s + 1)", "0")` -> `espiral_logaritmica`
   - `("cos(s) + 2", "0")` -> `curva_plana`
   - `("1 + s**2", "s")` -> `curva_espacial`

6. **Filename Generation & Sanitization**:
   - `generate_output_filename("helice_circular", "1", "1", 0.0, 6.28)` -> `"helice_circular-k1-t1-I0_6.28.html"`
   - `generate_output_filename("circulo", "1", "0", 0.0, 6.28)` -> `"circulo-k1-t0-I0_6.28.html"`
   - Sanitization replaces operators (`**` -> `_pow_`, `*` -> `_mult_`, `/` -> `_div_`, `+` -> `_plus_`, `-` -> `_minus_`) and strips non-alphanumerics.

7. **Code Quality and Linter**:
   - Command: `uv run --with ruff ruff check --select E,F,W,I curva_engine.py` -> `All checks passed!`
   - Command: `uv run --with ruff ruff format --check curva_engine.py` -> 1 minor line formatting notice on line 101.

---

## 2. Logic Chain

1. Per Observation 1, the implementation contains genuine mathematical logic with no shortcuts, facades, or hardcoded test values, satisfying all code integrity requirements.
2. Per Observation 2, running `pytest tests/test_teorema_fundamental.py -v` results in 51 passes and 0 failures, and `tests/test_curva_engine_stress.py` results in 49 passes and 0 failures, demonstrating robust test coverage across unit, integration, and stress dimensions.
3. Per Observation 3, the numerical solutions achieve errors $\sim 10^{-9}$, outperforming the specification tolerance requirement ($< 10^{-3}$) by six orders of magnitude. The Modified Gram-Schmidt projection on $SO(3)$ preserves unit norms, orthogonality, and $\det=+1.0$ to machine precision ($< 10^{-14}$) across all tested intervals.
4. Per Observation 4, the AST whitelist validator parses and inspects the abstract syntax tree prior to SymPy evaluation, preventing remote code execution or unauthorized attribute traversal.
5. Per Observation 5, the curve classification engine implements exact mathematical criteria for all 8 required curve families, correctly honoring Lancret's theorem both symbolically and numerically.
6. Per Observation 6, filename generation matches the acceptance criteria formatting rules exactly.
7. Consequently, the work delivered for Milestone M1 satisfies all specifications and interface contracts outlined in `PROJECT.md`.

---

## 3. Adversarial Challenges & Findings

### [Minor / Hardening] Finding 1: Bare Function Name Exception Type
- **Observation**: Calling `parse_and_validate_expression("sin")` succeeds and returns the SymPy class `sp.sin` because `"sin"` is present in `_ALLOWED_MATH_FUNCS`. When subsequently passed to `reconstruct_curve("sin", "0")`, inspecting `expr.free_symbols` raises `TypeError: 'property' object is not iterable` rather than a user-friendly `ValueError`.
- **Attack Scenario**: A user specifies CLI input `"sin"` instead of `"sin(s)"`.
- **Blast Radius**: Unhandled `TypeError` instead of a clean `ValueError`.
- **Mitigation**: In `parse_and_validate_expression`, assert `not isinstance(sym_expr, sp.core.function.FunctionClass)` and ensure all identifiers from `_ALLOWED_MATH_FUNCS` only appear as call targets `ast.Call.func`.

### [Minor / Hardening] Finding 2: Unbounded Solver on Non-Finite Interval Limit (`s1 = inf`)
- **Observation**: `s0_f >= s1_f` compares `float(s0)` and `float(s1)`. If `s1 = np.inf`, `s0_f >= np.inf` evaluates to `False`. When passed to `solve_ivp(..., (0.0, np.inf))`, the solver attempts to integrate towards infinity, hanging the process.
- **Attack Scenario**: CLI or programmatic invocation with `s1 = float('inf')`.
- **Blast Radius**: Process hang/resource exhaustion in `solve_ivp`.
- **Mitigation**: Add explicit validation: `if not np.isfinite(s0_f) or not np.isfinite(s1_f): raise ValueError(...)`.

### [Minor / Style] Finding 3: Formatting Linter
- **Observation**: `ruff format --check curva_engine.py` identifies 1 formatting adjustment on line 101.
- **Blast Radius**: None. Code syntax and semantics are completely valid.
- **Mitigation**: Format with `ruff format curva_engine.py`.

---

## 4. Caveats

- **Singularities within ODE Integration**: In cases where a non-integrable singularity lies strictly between discretization grid points (e.g. $1/(s - 0.5)^2$ evaluated with coarse $N=4$ where $0.5$ is not sampled in `s_vals`), `solve_ivp` adaptive step size will take many small steps near the singularity before either failing or timing out. In practice, standard discretization ($N \ge 100$) detects such poles during grid evaluation upfront.
- **Review-Only Scope**: In adherence to the reviewer role constraints, implementation code was not modified by this agent. The 3 findings noted above are minor, non-blocking improvements recommended for final hardening in Milestone M4.

---

## 5. Conclusion

**Verdict: APPROVE**

`curva_engine.py` is fully verified, robust, and mathematically sound. It meets all interface requirements of `PROJECT.md` and passes 100% of the relevant test suites (51/51 in `test_teorema_fundamental.py` and 49/49 in `test_curva_engine_stress.py`). Zero integrity violations were found. Milestone M1 is approved to proceed to Milestone M2 (`curva_viz.py`).

---

## 6. Verification Method

To independently verify this review:

1. **Run full test suite**:
   ```bash
   python3 -m pytest tests/test_teorema_fundamental.py -v
   ```
   *Expected result*: 51 passed, 13 skipped, 0 failed.

2. **Run stress and adversarial test suite**:
   ```bash
   python3 -m pytest tests/test_curva_engine_stress.py -v
   ```
   *Expected result*: 49 passed, 0 failed.

3. **Run code quality linter**:
   ```bash
   uv run --with ruff ruff check --select E,F,W,I curva_engine.py
   ```
   *Expected result*: `All checks passed!`
