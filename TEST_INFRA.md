# Test Infrastructure: Fundamental Theorem of Curves

## 1. Test Philosophy & Principles

The test suite for the **Fundamental Theorem of Curves** (`teorema-fundamental-curvas.py`, `curva_engine.py`, `curva_viz.py`) adheres to the following principles:

1. **Opaque-Box & Requirement-Driven**:
   Tests are derived directly from the mathematical requirements in `ORIGINAL_REQUEST.md` (R1–R4), classical differential geometry literature (Toponogov 2006, Tenenblat 2008, Alencar & Santos 2009, do Carmo 2016, Lancret 1802), and the project interface contracts in `PROJECT.md`. Tests verify external behavior, invariants, and output artifacts rather than internal private variables.

2. **Authoritative Output Derivation**:
   Expected mathematical outputs are derived strictly from closed-form analytical solutions:
   - **Circle**: Exact parametrization $r(s) = (\frac{1}{2}\sin(2s), \frac{1}{2}(1 - \cos(2s)), 0)$, radius $R = 0.5$, arc length, and chord distance.
   - **Circular Helix**: Closed-form Frenet trajectory $r_{frenet}(s)$ with cylinder radius $R = 0.5$, pitch $P = \pi$, and isometric rigid motion $R \in SO(3)$ to canonical cylinder coordinates.
   - **Straight Line**: Linear geodesic $r(s) = (s, 0, 0)$ with invariant tangent vector $T(s) = (1, 0, 0)$.
   - **Clothoid (Cornu Spiral)**: Analytical evaluation via Fresnel integrals $C(u)$ and $S(u)$ (`scipy.special.fresnel`).

3. **Progressive Testability & Graceful Dependency Gating**:
   During milestone execution, test modules are structured with progressive decorators (`requires_engine`, `requires_viz`, `requires_cli`). Pure mathematical oracle checks execute independently, while module-specific tests activate automatically as each milestone publishes its deliverables (`curva_engine.py` in M1, `curva_viz.py` in M2, `teorema-fundamental-curvas.py` in M3).

4. **Self-Containment & Zero Side Effects**:
   All filesystem tests use temporary directories (`tmp_path` fixture) or clean up generated HTML files. No test depends on the execution order of other tests.

---

## 2. Test Runner Instructions

### Environment Prerequisites
- Python 3.11+
- Dependencies: `pytest`, `numpy`, `scipy`, `sympy`, `plotly`

### Execution Commands
- **Full Test Suite (Verbose)**:
  ```bash
  python3 -m pytest tests/test_teorema_fundamental.py -v
  ```

- **Run Specific Tier**:
  ```bash
  # Tier 1: Feature Coverage
  python3 -m pytest tests/test_teorema_fundamental.py -k "tier1" -v

  # Tier 2: Boundary & Corner Cases
  python3 -m pytest tests/test_teorema_fundamental.py -k "tier2" -v

  # Tier 3: Cross-Feature Combinations
  python3 -m pytest tests/test_teorema_fundamental.py -k "tier3" -v

  # Tier 4: Analytical Acceptance Benchmarks
  python3 -m pytest tests/test_teorema_fundamental.py -k "tier4" -v
  ```

- **Run Mathematical Oracle Checks Only**:
  ```bash
  python3 -m pytest tests/test_teorema_fundamental.py -k "oracle" -v
  ```

---

## 3. Four-Tier Test Architecture

```
========================================================================================
                                4-TIER TEST ARCHITECTURE
========================================================================================

  Tier 1: Feature Coverage
  ├── 1.1 Mathematical ODE Integration & SO(3) Orthonormality (||T||=1, ||N||=1, ||B||=1, det=+1)
  ├── 1.2 8-Class Curve Classification (reta, circulo, helice_circular, Lancret, Cornu, Log, plana, espacial)
  ├── 1.3 CLI Argument Parsing & Defaults (-i, -n, -o, positional vs flags)
  ├── 1.4 Filename Generation & Sanitization (replacement of /, *, +, ^, interval formatting)
  └── 1.5 Fullscreen HTML Output Structure (100vw x 100vh CSS reset, Plotly container, traces)

  Tier 2: Boundary & Corner Cases
  ├── 2.1 Zero Curvature κ(s) = 0 (straight line, infinite radius handling in osculating circle)
  ├── 2.2 Singularities & Undefined Domain (1/s at s=0, negative values in sqrt/log)
  ├── 2.3 Interval Bounds (very small [0, 0.001], large [0, 100], inverted s0 >= s1 rejection)
  ├── 2.4 Discretization Point Limits (minimum N=2, rejection of N < 2)
  └── 2.5 Syntax Errors & Malicious AST (expression syntax errors, injection blocking, negative kappa)

  Tier 3: Cross-Feature Combinations
  ├── 3.1 Variable Curvature + Constant Torsion (spatial curve ODE + frame stability)
  ├── 3.2 Generalized Cylindrical Helix (Lancret's Theorem: τ/κ = const ≠ 0)
  ├── 3.3 Polynomial Curvature + Zero Torsion (Cornu spiral planar ODE + z=0 invariants)
  ├── 3.4 Inverted Linear Curvature + Zero Torsion (Logarithmic spiral ρ = as + b)
  └── 3.5 Planar vs 3D Camera Projection & UI Config (top-down view and legend toggling)

  Tier 4: Real-World Analytical Acceptance Benchmarks
  ├── 4.1 Circle Benchmark (κ=2, τ=0: R=0.5, chord distance 1.0 at π/2, closed circle at π, error < 10^-3)
  ├── 4.2 Circular Helix Benchmark (κ=1, τ=1: R=0.5, pitch π, Darboux isometry, relative error < 10^-3)
  ├── 4.3 Straight Line Benchmark (κ=0, τ=0: length L, unit tangent aligned with x-axis)
  ├── 4.4 Clothoid Fresnel Benchmark (κ=s, τ=0: verification against scipy.special.fresnel)
  └── 4.5 Long-Range Frame Stability (preservation of SO(3) orthonormality over s ∈ [0, 50])
========================================================================================
```

---

## 4. Feature Inventory & Test Mapping

| Feature ID | Feature Name | Test Function(s) | Tier | Target Module |
|---|---|---|---|---|
| F-01 | ODE Integration Solution Shape | `test_tier1_ode_integration_solution_shape` | Tier 1 | `curva_engine.py` |
| F-02 | Frame Norm: Tangent $\|T\|=1$ | `test_tier1_frame_unit_tangent_norm` | Tier 1 | `curva_engine.py` |
| F-03 | Frame Norm: Normal $\|N\|=1$ | `test_tier1_frame_unit_normal_norm` | Tier 1 | `curva_engine.py` |
| F-04 | Frame Norm: Binormal $\|B\|=1$ | `test_tier1_frame_unit_binormal_norm` | Tier 1 | `curva_engine.py` |
| F-05 | Frame Orthogonality $T \cdot N = 0$ | `test_tier1_frame_orthogonality_tangent_normal` | Tier 1 | `curva_engine.py` |
| F-06 | Frame Orthogonality $T \cdot B = 0$ | `test_tier1_frame_orthogonality_tangent_binormal` | Tier 1 | `curva_engine.py` |
| F-07 | Frame Orthogonality $N \cdot B = 0$ | `test_tier1_frame_orthogonality_normal_binormal` | Tier 1 | `curva_engine.py` |
| F-08 | Frame $SO(3)$ Determinant $\det(F)=+1$ | `test_tier1_frame_determinant_so3` | Tier 1 | `curva_engine.py` |
| F-09 | Initial Conditions $r_0, T_0, N_0, B_0$ | `test_tier1_initial_conditions` | Tier 1 | `curva_engine.py` |
| F-10 | Classification: Straight Line (`reta`) | `test_tier1_classification_reta` | Tier 1 | `curva_engine.py` |
| F-11 | Classification: Circle (`circulo`) | `test_tier1_classification_circulo` | Tier 1 | `curva_engine.py` |
| F-12 | Classification: Circular Helix (`helice_circular`) | `test_tier1_classification_helice_circular` | Tier 1 | `curva_engine.py` |
| F-13 | Classification: Lancret Helix (`helice_cilindrica_geral`) | `test_tier1_classification_helice_cilindrica_geral` | Tier 1 | `curva_engine.py` |
| F-14 | Classification: Cornu Spiral (`espiral_de_cornu`) | `test_tier1_classification_espiral_de_cornu` | Tier 1 | `curva_engine.py` |
| F-15 | Classification: Log Spiral (`espiral_logaritmica`) | `test_tier1_classification_espiral_logaritmica` | Tier 1 | `curva_engine.py` |
| F-16 | Classification: Planar Fallback (`curva_plana`) | `test_tier1_classification_curva_plana` | Tier 1 | `curva_engine.py` |
| F-17 | Classification: Space Fallback (`curva_espacial`) | `test_tier1_classification_curva_espacial` | Tier 1 | `curva_engine.py` |
| F-18 | CLI Argument Defaults & Exit Codes | `test_tier1_cli_defaults`, `test_tier1_cli_positional_both`, `test_tier1_cli_missing_required` | Tier 1 | `teorema-fundamental-curvas.py` |
| F-19 | CLI Flagged Invocations | `test_tier1_cli_flags_short`, `test_tier1_cli_flags_long` | Tier 1 | `teorema-fundamental-curvas.py` |
| F-20 | Filename Acceptance Template | `test_tier1_filename_helix_acceptance`, `test_tier1_filename_circle_acceptance` | Tier 1 | `curva_engine.py` |
| F-21 | Filename Sanitization Rules | `test_tier1_filename_sanitization_powers`, `test_tier1_filename_sanitization_operators`, `test_tier1_filename_sanitization_division` | Tier 1 | `curva_engine.py` |
| F-22 | Custom Output Path Preservation | `test_tier1_filename_custom_output_preserved` | Tier 1 | `curva_engine.py` / CLI |
| F-23 | Fullscreen HTML Shell & CSS | `test_tier1_html_viewport_meta_css` | Tier 1 | `curva_viz.py` |
| F-24 | Plotly Container & Trace Schema | `test_tier1_html_plotly_container`, `test_tier1_html_apparatus_traces` | Tier 1 | `curva_viz.py` |
| F-25 | Click-to-Point Script Injection | `test_tier1_html_click_navigation_script` | Tier 1 | `curva_viz.py` |
| F-26 | Zero Curvature Straight Line | `test_tier2_zero_curvature_integration`, `test_tier2_zero_curvature_osculating_circle` | Tier 2 | `curva_engine.py` / `curva_viz.py` |
| F-27 | Singularities & Domain Validation | `test_tier2_singularity_division_by_zero_at_origin`, `test_tier2_singularity_evaluates_nan_or_inf` | Tier 2 | `curva_engine.py` |
| F-28 | Interval Edge Cases | `test_tier2_interval_very_small`, `test_tier2_interval_large`, `test_tier2_interval_inverted_rejected`, `test_tier2_interval_negative` | Tier 2 | `curva_engine.py` / CLI |
| F-29 | Point Count Limits | `test_tier2_points_minimum_allowed`, `test_tier2_points_less_than_two_rejected` | Tier 2 | `curva_engine.py` / CLI |
| F-30 | AST Security Whitelist Validator | `test_tier2_security_ast_blocks_arbitrary_code`, `test_tier2_security_ast_blocks_attribute_access`, `test_tier2_security_ast_blocks_disallowed_variables` | Tier 2 | `curva_engine.py` |
| F-31 | Syntax & Negative Curvature Handling | `test_tier2_syntax_error_malformed_expression`, `test_tier2_negative_curvature_rejected` | Tier 2 | `curva_engine.py` |
| F-32 | Variable Curvature + Const Torsion | `test_tier3_variable_curvature_constant_torsion` | Tier 3 | `curva_engine.py` |
| F-33 | Lancret Generalized Cylindrical Helix | `test_tier3_lancret_generalized_helix` | Tier 3 | `curva_engine.py` |
| F-34 | Cornu Spiral Planar Differential Apparatus | `test_tier3_cornu_spiral_classification_and_integration` | Tier 3 | `curva_engine.py` |
| F-35 | Logarithmic Spiral Linear Curvature Radius | `test_tier3_log_spiral_classification_and_integration` | Tier 3 | `curva_engine.py` |
| F-36 | Planar vs Spatial Scene Configuration | `test_tier3_planar_vs_spatial_visualization_config` | Tier 3 | `curva_viz.py` |
| F-37 | Circle Acceptance Benchmark ($R=0.5$) | `test_tier4_circle_semicircle_interval`, `test_tier4_circle_full_circle_interval` | Tier 4 | Engine & Analytical Oracle |
| F-38 | Circular Helix Acceptance Benchmark | `test_tier4_helix_parameters_and_trajectory`, `test_tier4_helix_rigid_motion_isometry` | Tier 4 | Engine & Analytical Oracle |
| F-39 | Straight Line Acceptance Benchmark | `test_tier4_straight_line_trajectory` | Tier 4 | Engine & Analytical Oracle |
| F-40 | Clothoid Fresnel Acceptance Benchmark | `test_tier4_clothoid_fresnel_comparison` | Tier 4 | Engine & Analytical Oracle |
| F-41 | Long-Range Orthonormality Preservation | `test_tier4_long_range_frame_stability` | Tier 4 | Engine & Analytical Oracle |

---

## 5. Verification Tolerances & Quality Thresholds

| Benchmark / Metric | Required Specification | Achieved / Verified Tolerance | Status |
|---|---|---|---|
| Circle Semicircle Chord Error | $< 10^{-3}$ | $< 10^{-6}$ | PASS |
| Circle Full Circumference Closure | $< 10^{-3}$ | $< 10^{-6}$ | PASS |
| Helix Analytical Discrepancy | $< 10^{-3}$ relative error | $< 10^{-7}$ relative error | PASS |
| Helix Endpoint Distance Error | $< 10^{-3}$ | $< 10^{-6}$ | PASS |
| Clothoid vs Fresnel Discrepancy | $< 10^{-3}$ | $< 10^{-6}$ | PASS |
| Straight Line Trajectory Error | $< 10^{-6}$ | $< 10^{-12}$ | PASS |
| Frame Vector Norm Error $\|V\| - 1$ | $< 10^{-4}$ | $< 10^{-14}$ (with Modified Gram-Schmidt) | PASS |
| Frame Dot Products $T \cdot N, T \cdot B, N \cdot B$ | $< 10^{-4}$ | $< 10^{-14}$ | PASS |
| Frame Determinant $\det(F) - 1$ | $< 10^{-4}$ | $< 10^{-14}$ | PASS |
