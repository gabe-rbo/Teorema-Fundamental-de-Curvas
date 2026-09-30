# Handoff Report: Milestone M1 — Math Engine & Classification Engine

**Agent**: `teamwork_preview_worker_m1_1`  
**Milestone**: M1 (Math Engine & Classification)  
**Date**: 2026-09-30  
**Ownership Target**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_engine.py`

---

## 1. Observation

1. **Interface Contract Compliance**:
   Examined `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md` lines 79–114.
   Implemented `curva_engine.py` providing all required components:
   - `parse_and_validate_expression(expr_str: str) -> sp.Expr`
   - `create_evaluator(expr: sp.Expr) -> Callable[[np.ndarray | float], np.ndarray | float]`
   - `CurveResult` dataclass with fields `(s, r, T, N, B, kappa, tau, classification, s0, s1)`
   - `reconstruct_curve(kappa_expr_str, tau_expr_str="0", s0=0.0, s1=6.283185307179586, num_points=500) -> CurveResult`
   - `classify_curve(kappa_expr, tau_expr, s_vals, kappa_vals, tau_vals) -> str`
   - `sanitize_expr_for_filename(expr_str: str) -> str`
   - `generate_output_filename(curve_class: str, kappa_str: str, tau_str: str, s0: float, s1: float) -> str`
   - `orthonormalize_frame(T, N, B) -> tuple[np.ndarray, np.ndarray, np.ndarray]`

2. **AST Whitelist & Security Validation**:
   - Valid expressions accepted: constants (`"2"`, `"0"`, `"pi"`, `"e"`), polynomials (`"2*s"`, `"s**2"`, `"s^2"`, `"2s"`), trigonometric/exponential (`"sin(s)"`, `"cos(s)"`, `"exp(-s/2)"`), rational (`"1/(1 + s**2)"`), roots (`"sqrt(s + 1)"`), absolute value (`"abs(s)"`).
   - Malicious/unauthorized expressions rejected with `ValueError`:
     - `__import__("os").system("ls")` -> `ValueError: Direct identifier required for function call in '__import__("os").system("ls")'.`
     - `open("/etc/passwd")` -> `ValueError: Disallowed function 'open' in 'open("/etc/passwd")'.`
     - `eval("1+1")` -> `ValueError: Disallowed function 'eval' in 'eval("1+1")'.`
     - `[x for x in s]` -> `ValueError: Disallowed syntax element 'List' in expression '[x for x in s]'.`
     - `s.__class__` -> `ValueError: Disallowed syntax element 'Attribute' in expression 's.__class__'.`
     - `x + 1` -> `ValueError: Disallowed identifier 'x' in 'x + 1'. Only parameter 's' and constants ('pi', 'e') are permitted.`

3. **Analytical Benchmark Verification**:
   - **Benchmark 1 (Circle, $\kappa=2, \tau=0$)**:
     - Semicircle $[0, \pi/2]$: max coordinate error $x = 2.35 \times 10^{-9}$, $y = 2.45 \times 10^{-9}$, endpoint error $= 2.45 \times 10^{-9} < 10^{-6}$ (vs required $< 10^{-3}$).
     - Full circle $[0, \pi]$: closed endpoint distance $= 8.10 \times 10^{-10} < 10^{-6}$.
   - **Benchmark 2 (Circular Helix, $\kappa=1, \tau=1, s \in [0, 2\pi\sqrt{2}]$)**:
     - Comparison against Frenet initial frame trajectory $r_{frenet}(s) = (s/2 + \frac{\sqrt{2}}{4}\sin(\sqrt{2}s), \frac{1}{2}(1 - \cos(\sqrt{2}s)), s/2 - \frac{\sqrt{2}}{4}\sin(\sqrt{2}s))$:
     - Max coordinate error: $x = 1.80 \times 10^{-9}, y = 2.65 \times 10^{-9}, z = 1.80 \times 10^{-9} < 10^{-6}$ (vs required $< 10^{-3}$).
   - **Benchmark 3 (Straight line, $\kappa=0, \tau=0, s \in [0, 10]$)**:
     - Trajectory max error: $5.33 \times 10^{-15} < 10^{-12}$.
   - **Benchmark 4 (Clothoid / Cornu spiral, $\kappa=s, \tau=0, s \in [0, 5.0]$)**:
     - Comparison against Fresnel integrals $\sqrt{\pi}(C(s/\sqrt{\pi}), S(s/\sqrt{\pi}), 0)$:
     - Max coordinate error: $x = 4.88 \times 10^{-9}, y = 3.47 \times 10^{-9} < 10^{-6}$.

4. **Frame Orthonormality & $SO(3)$ Preservation**:
   Across all integration points ($N=500$ per curve) for Circle, Helix, Line, and Clothoid:
   - $|\|T\| - 1| \le 2.22 \times 10^{-16}$
   - $|\|N\| - 1| \le 2.22 \times 10^{-16}$
   - $|\|B\| - 1| \le 4.44 \times 10^{-16}$
   - $|T \cdot N| \le 1.67 \times 10^{-16}$
   - $|T \cdot B| \le 1.11 \times 10^{-16}$
   - $|N \cdot B| \le 1.11 \times 10^{-16}$
   - $|\det([T, N, B]) - 1| \le 8.88 \times 10^{-16}$
   All orthonormality tolerances are satisfied to machine precision ($< 10^{-15}$ vs required $< 10^{-4}$).

5. **Curve Classification Engine**:
   Verified deterministic classification across all 8 required families:
   - `("0", "0")` -> `reta`
   - `("0", "5")` -> `reta`
   - `("2", "0")` -> `circulo`
   - `("1", "1")` -> `helice_circular`
   - `("2", "3")` -> `helice_circular`
   - `("2*s", "4*s")` -> `helice_cilindrica_geral` (Lancret's Theorem $\tau/\kappa = 2$)
   - `("s**2", "2*s**2")` -> `helice_cilindrica_geral` (Lancret's Theorem $\tau/\kappa = 2$)
   - `("2*s", "0")` -> `espiral_de_cornu`
   - `("3*s + 1", "0")` -> `espiral_de_cornu`
   - `("1/(2*s + 1)", "0")` -> `espiral_logaritmica`
   - `("1/(s + 2)", "0")` -> `espiral_logaritmica`
   - `("s**2", "0")` -> `curva_plana`
   - `("sin(s)", "0")` -> `curva_plana`
   - `("s", "s**2")` -> `curva_espacial`
   - `("exp(s)", "s")` -> `curva_espacial`

6. **Output Filename Generation & Sanitization**:
   - `generate_output_filename('helice_circular', '1', '1', 0, 6.28)` -> `helice_circular-k1-t1-I0_6.28.html`
   - `generate_output_filename('circulo', '1', '0', 0, 6.28)` -> `circulo-k1-t0-I0_6.28.html`
   - `generate_output_filename('espiral_de_cornu', '2*s', '0', 0, 5)` -> `espiral_de_cornu-k2_mult_s-t0-I0_5.html`
   - `generate_output_filename('curva_plana', '1/(1+s**2)', '0', 0, 10)` -> `curva_plana-k1_div_1_plus_s_pow_2-t0-I0_10.html`

7. **Test Suite Execution**:
   Ran `python3 -m pytest -v tests/`:
   `51 passed, 13 skipped, 3 warnings in 1.09s` (100% of non-skipped tests passed). The 13 skipped tests correspond to Milestone M2 (`curva_viz.py`) and Milestone M3 (`teorema-fundamental-curvas.py` CLI).
   Ran `uv run --with ruff ruff check --select E,F,W,I curva_engine.py`:
   `All checks passed!` (0 lint errors).

---

## 2. Logic Chain

1. Starting from Observation 1, the interface defined in `PROJECT.md` governs downstream consumers (`curva_viz.py`, `teorema-fundamental-curvas.py`, and `test_teorema_fundamental.py`). Implementing exact function signatures and data types guarantees complete modular interoperability.
2. Per Observation 2, direct user strings for curvature and torsion can pose remote execution vulnerabilities in `sympy.parse_expr`. The AST whitelist pre-parser walks the abstract syntax tree and restricts nodes strictly to elementary arithmetic, safe constants (`s`, `pi`, `e`), and approved functions, preventing code execution before SymPy evaluation occurs.
3. Per Observations 3 and 4, solving the Frenet-Serret 12-dimensional system using `solve_ivp` with `DOP853` (8th-order Runge-Kutta) at `rtol=1e-9, atol=1e-9` achieves trajectory errors $< 5 \times 10^{-9}$ against all analytical benchmarks.
4. Numerical drift in Runge-Kutta integration naturally degrades frame orthogonality over time. By applying vectorized Modified Gram-Schmidt followed by cross-product binormal restoration $B = T \times N$, the frame is projected onto the Lie group $SO(3)$, guaranteeing $\det([T, N, B]) = +1.0$ and unit norms to machine precision ($< 10^{-15}$).
5. Per Observation 5, geometric curve classification combines symbolic differentiation (unifying symbol instances dynamically to avoid SymPy 1.14 symbol mismatch) and numerical sample fallbacks. This reliably resolves all 8 geometric classes, specifically validating Lancret's theorem ($\tau(s)/\kappa(s) = \text{const}$).
6. Per Observations 6 and 7, comprehensive test suite execution confirmed all functional requirements and edge cases pass with zero regressions.

---

## 3. Caveats

- **Singularities**: Functions with vertical asymptotes (e.g. `1/s` on an interval starting at `s0=0`) are rejected early during domain validation (`ValueError: Expression evaluates to non-finite values`).
- **Planar Curve Frame Orientation**: In standard planar curves ($\tau = 0$), $B(s)$ remains constant at $(0, 0, 1)$, and $T(s), N(s)$ evolve in the xy-plane. Downstream visualizer (`curva_viz.py`) can directly leverage the 2D projection.

---

## 4. Conclusion

Milestone M1 is complete. `curva_engine.py` is fully implemented, verified, and strictly conforms to the interface contract in `PROJECT.md`. All mathematical benchmarks (circle, helix, line, clothoid), frame orthonormality guarantees, AST security validations, 8-class classification, and filename generation pass 100% of unit and integration tests.

---

## 5. Verification Method

To independently verify the implementation:

1. **Execute full test suite**:
   ```bash
   python3 -m pytest -v tests/
   ```
   *Expected result*: 51 passed, 13 skipped, 0 failed.

2. **Execute standalone 10-suite self-verification**:
   ```bash
   python3 -c "
   import numpy as np
   from scipy.special import fresnel
   import curva_engine as ce

   # Benchmark 1: Circle
   res_c = ce.reconstruct_curve('2', '0', 0, np.pi, 500)
   assert res_c.classification == 'circulo'
   assert np.linalg.norm(res_c.r[:, -1] - res_c.r[:, 0]) < 1e-6

   # Benchmark 2: Helix
   res_h = ce.reconstruct_curve('1', '1', 0, 2*np.pi*np.sqrt(2), 500)
   assert res_h.classification == 'helice_circular'

   # Orthonormality check
   F = np.stack([res_h.T, res_h.N, res_h.B], axis=1)
   dets = np.linalg.det(np.transpose(F, (2, 0, 1)))
   assert np.allclose(dets, 1.0, atol=1e-12)
   print('Verification: ALL CHECKS PASSED!')
   "
   ```

3. **Verify linting and code style**:
   ```bash
   uv run --with ruff ruff check --select E,F,W,I curva_engine.py
   ```
   *Expected result*: `All checks passed!`
