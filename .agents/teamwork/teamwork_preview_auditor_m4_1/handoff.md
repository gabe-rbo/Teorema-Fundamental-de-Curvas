# Milestone M4 Forensic Integrity Audit Report

**Work Product**: Entire Codebase (`curva_engine.py`, `curva_viz.py`, `teorema-fundamental-curvas.py`, `tests/test_teorema_fundamental.py`)  
**Profile**: General Project  
**Integrity Mode**: Development (also verified against Demo & Benchmark standards)  
**Auditor**: `auditor_m4_1`  
**Verdict**: **CLEAN**

---

## 1. Observation

Direct empirical observations across the audited codebase:

### 1.1 Source Code Inspection
- **`curva_engine.py`**:
  - **Lines 45–79**: Strict AST whitelist configurations (`_ALLOWED_AST_NODES`, `_ALLOWED_VARIABLE_NAMES = {"s", "pi", "E", "e"}`, `_ALLOWED_MATH_FUNCS`).
  - **Lines 137–171**: AST walk validation rejecting unauthorized syntax elements, attributes, keyword args, or unknown identifiers.
  - **Lines 205 & 321**: The only string equality checks in the entire engine check for symbol identity `sym.name == "s"`. Zero string matching or hardcoded shortcuts exist for input formulas (e.g. no `if expr == "1": ...`).
  - **Lines 261–292**: Vectorized Modified Gram-Schmidt implementation:
    $$T_{\text{ortho}} = T / \|T\|$$
    $$N_{\text{diff}} = N - (N \cdot T_{\text{ortho}}) T_{\text{ortho}}, \quad N_{\text{ortho}} = N_{\text{diff}} / \|N_{\text{diff}}\|$$
    $$B_{\text{ortho}} = T_{\text{ortho}} \times N_{\text{ortho}}$$
  - **Lines 515–530**: Authentic 12-state Frenet-Serret ODE system:
    $$\frac{dr}{ds} = T, \quad \frac{dT}{ds} = \kappa N, \quad \frac{dN}{ds} = -\kappa T + \tau B, \quad \frac{dB}{ds} = -\tau N$$
  - **Lines 538–564**: High-order Runge-Kutta numerical integration using `scipy.integrate.solve_ivp` (`DOP853` with fallback to `RK45`, `rtol=1e-9`, `atol=1e-9`).
  - **Lines 299–432**: Curve classification engine with 8 geometric classes (`reta`, `circulo`, `helice_circular`, `helice_cilindrica_geral`, `espiral_de_cornu`, `espiral_logaritmica`, `curva_plana`, `curva_espacial`) utilizing symbolic differentiation (`sp.diff`) and numerical polynomial/variance regression.

- **`curva_viz.py`**:
  - **Lines 125–307**: Full construction of 10 differential apparatus traces:
    - Trace 0: Curva $r(s)$ (`go.Scatter3d`)
    - Trace 1: Ponto Ativo $r(s)$ (`go.Scatter3d`)
    - Trace 2: Vetor Tangente $\vec{T}(s)$ (green unit vector)
    - Trace 3: Vetor Normal $\vec{N}(s)$ (red unit vector)
    - Trace 4: Vetor Binormal $\vec{B}(s)$ (blue unit vector)
    - Trace 5: Reta Tangente $L_T$ (`go.Scatter3d`)
    - Trace 6: Plano Osculador $(T, N)$ (`go.Mesh3d`)
    - Trace 7: Plano Normal $(N, B)$ (`go.Mesh3d`)
    - Trace 8: Plano Retificante $(T, B)$ (`go.Mesh3d`)
    - Trace 9: Círculo Osculador centered at $c = r(s) + \frac{1}{\kappa} \vec{N}$ with radius $\rho = 1/|\kappa|$
  - **Lines 433–494**: Selective animation frames (animating traces 1..9 while leaving trace 0 static for file compactness ~1.1MB) and bottom slider configuration.
  - **Lines 745–805**: Client-side JavaScript injection handling `plotly_click` snapping, `plotly_sliderchange`, `plotly_animatingframe`, and `window.resize`.
  - **Lines 823–925**: Viewport CSS reset with `width: 100vw; height: 100vh; height: 100dvh; overflow: hidden;` and glassmorphic HUD card.

- **`teorema-fundamental-curvas.py`**:
  - **Lines 68–183**: Dual positional/flagged CLI argument parser (`-k`, `-t`, `-i`, `-n`, `-o`) supporting symbolic bounds (`pi`, `2*pi`).
  - **Lines 185–261**: Complete execution pipeline linking engine reconstruction, filename generation, and HTML visualization.

- **`tests/test_teorema_fundamental.py`**:
  - **Total 64 tests**: 4 Oracle tests, 32 Tier 1 tests, 16 Tier 2 tests, 5 Tier 3 tests, 7 Tier 4 benchmarks.
  - **Mocks and Fakes**: Grep search for `mock`, `MagicMock`, `patch`, `unittest.mock` yielded 0 matches across the entire repository.
  - **Tautological Assertions**: Grep search for `assert True` yielded 0 matches across the entire repository.

### 1.2 Independent Empirical Execution
- **Full Test Suite Execution**:
  - `python3 -m pytest tests/test_teorema_fundamental.py -v`:
    - Result: **64 passed, 3 warnings in 11.34s** (exited code 0).
  - `python3 -m pytest tests/ -v`:
    - Result: **156 passed, 5 warnings in 41.38s** (exited code 0).
- **Independent Numerical Machine Precision Check**:
  - Oscillatory inputs ($\kappa(s) = 3 + \sin(2s), \tau(s) = \cos(s)$):
    - Max unit norm error: $2.22 \times 10^{-16}$
    - Max mutual orthogonality error: $1.67 \times 10^{-16}$
    - Max $SO(3)$ determinant error: $6.66 \times 10^{-16}$
  - Inflection point with vanishing curvature ($\kappa(s) = s^2, \tau(s) = 0$):
    - Max unit norm error: $4.44 \times 10^{-16}$
    - Max orthogonality error: $1.67 \times 10^{-16}$
    - Max determinant error: $8.88 \times 10^{-16}$
- **Acceptance Criteria Verification**:
  1. Circle Benchmark ($\kappa = 2, \tau = 0$):
     - Semicircle endpoint error: $3.97 \times 10^{-10}$ (acceptance threshold $< 10^{-3}$)
     - Chord distance: $1.000000$ (acceptance threshold $1.0 \pm 10^{-3}$)
     - Full circle closure error: $8.10 \times 10^{-10}$ (acceptance threshold $< 10^{-3}$)
  2. Helix Benchmark ($\kappa = 1, \tau = 1$ over $[0, 2\pi\sqrt{2}]$):
     - Trajectory max error against analytical solution: $2.76 \times 10^{-9}$ (acceptance threshold $< 10^{-3}$)
     - Endpoint displacement: $6.2831853$, error from $2\pi$: $8.88 \times 10^{-16}$
  3. Straight Line Benchmark ($\kappa = 0, \tau = 0$ over $[0, 10]$):
     - Arc length: $10.0000000000$, deviation from $x=s$: $5.33 \times 10^{-15}$, $y=0$, $z=0$.
  4. Clothoid Benchmark ($\kappa(s) = s, \tau = 0$ over $[0, 5]$):
     - Error against SciPy Fresnel integrals: $x$-error $= 4.94 \times 10^{-9}$, $y$-error $= 3.48 \times 10^{-9}$, $z$-error $= 0.0$.
  5. CLI Automation:
     - `python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28`: cleanly generated `helice_circular-k1-t1-I0_6.28.html` (exit code 0).
     - `python3 teorema-fundamental-curvas.py "1" -i 0 6.28`: cleanly generated `circulo-k1-t0-I0_6.28.html` (exit code 0).
     - `python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28 -o /tmp/test_out.html`: wrote output directly to `/tmp/test_out.html` (exit code 0).

---

## 2. Logic Chain

1. **Absence of Hardcoding & Facades (Observation 1.1)**:
   Grep analysis and line-by-line inspection of `curva_engine.py` confirm that neither input formulas nor expected coordinates are hardcoded. Functions do not return static mocks or stubs. The only equality check is symbol name validation. Therefore, the implementation is authentic.
2. **Authentic Numerical Mathematics (Observation 1.1, 1.2)**:
   The ODE right-hand-side explicitly evaluates the 12-state Frenet-Serret derivatives and integrates them dynamically with high-order SciPy solvers (`solve_ivp` `DOP853`/`RK45`). The Modified Gram-Schmidt algorithm guarantees $\|T\|=\|N\|=\|B\|=1$, mutual orthogonality, and $\det([T, N, B]) = +1$ within machine precision ($< 10^{-15}$). Reconstructed curves match analytical solutions (circle, helix, clothoid, straight line) to errors between $10^{-9}$ and $10^{-16}$, orders of magnitude better than the required $10^{-3}$ threshold.
3. **Absence of Self-Certifying / Mocked Tests (Observation 1.1, 1.2)**:
   All tests in `tests/test_teorema_fundamental.py` derive expected values from analytical closed-form oracles (Fresnel integrals, exact $SO(3)$ cylinder isometries, Euclidean chord formulas) rather than circular self-comparisons. Zero test functions use mocking frameworks or tautological `assert True`.
4. **Full Feature Implementation & Compliance (Observation 1.1, 1.2)**:
   All requirements from `ORIGINAL_REQUEST.md` (R1: Mathematical engine, 8 classifications, R2: CLI interface and sanitization, R3: 10-trace Plotly HTML visualization with 100vw/100vh CSS and click/slider interactivity, R4: Comprehensive test suite) are fully realized and empirically verified.

---

## 3. Caveats

- **No git repository initialized yet**: `git status` reports not a git repository. This is expected because git initialization and GitHub deployment are assigned to Milestone M5.
- No other caveats.

---

## 4. Conclusion & Forensic Audit Report

```markdown
## Forensic Audit Report

**Work Product**: Entire Codebase (curva_engine.py, curva_viz.py, teorema-fundamental-curvas.py, tests/test_teorema_fundamental.py)
**Profile**: General Project
**Verdict**: CLEAN

### Phase Results
- Prohibited Pattern 1 (Hardcoded test results): PASS — 0 hardcoded test values or formula shortcuts found.
- Prohibited Pattern 2 (Facade implementations): PASS — Full authentic logic in all modules; no stubs or empty returns.
- Prohibited Pattern 3 (Fabricated verification outputs): PASS — No pre-populated logs or artifacts; all results generated live.
- Prohibited Pattern 4 (Self-certifying tests): PASS — 0 tautological assertions (`assert True`), 0 mocks, independent mathematical oracles.
- Prohibited Pattern 5 (Execution delegation): PASS — Genuine 12-state ODE integration via SciPy solve_ivp and authentic MGS implementation.
- Mathematical Engine Verification: PASS — SO(3) frame invariants preserved to < 1e-15; analytical benchmark errors < 1e-9.
- Interactive Visualization Verification: PASS — 10 differential apparatus traces, slider, responsive 100vw/100vh CSS, client-side JS.
- CLI Interface & Automation Verification: PASS — Correct argument resolution, sanitization, and exit codes.
```

---

## 5. Verification Method

To independently reproduce the forensic verification findings, execute the following commands in the project root:

1. **Execute full test suite**:
   ```bash
   python3 -m pytest tests/test_teorema_fundamental.py -v
   python3 -m pytest tests/ -v
   ```
2. **Verify CLI end-to-end execution and acceptance criteria**:
   ```bash
   python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28
   python3 teorema-fundamental-curvas.py "1" -i 0 6.28
   python3 teorema-fundamental-curvas.py "s" "0" -i 0 5 -o /tmp/clothoid.html
   ```
3. **Verify MGS numerical precision and SO(3) preservation**:
   ```bash
   python3 -c '
   import numpy as np, curva_engine as ce
   res = ce.reconstruct_curve("3 + sin(2*s)", "cos(s)", s0=0.0, s1=10.0, num_points=1000)
   print("Max det error:", np.max(np.abs(np.linalg.det(np.transpose(np.array([res.T, res.N, res.B]), (2,0,1))) - 1)))
   '
   ```
4. **Invalidation condition**: Any test failure, non-zero return code on valid CLI inputs, or frame orthonormality error $> 10^{-4}$.
