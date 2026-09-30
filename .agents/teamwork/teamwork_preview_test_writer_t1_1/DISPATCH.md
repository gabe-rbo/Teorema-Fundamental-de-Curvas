# Task Assignment: E2E Test Suite Track (T1)

You are an agent with archetype `teamwork_preview_test_writer`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_test_writer_t1_1`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Original user request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
Project master specification: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md`
Survey reports to consult:
- Math spec: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_1/handoff.md`
- CLI spec: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_explorer_survey_2/handoff.md`
- UI spec: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_3/handoff.md`

## Write Ownership
You EXCLUSIVELY own and write:
- `tests/__init__.py`
- `tests/test_teorema_fundamental.py`
- `TEST_INFRA.md` (at project root `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/TEST_INFRA.md`)
- `TEST_READY.md` (at project root `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/TEST_READY.md`)
Do NOT write to implementation files (`curva_engine.py`, `curva_viz.py`, `teorema-fundamental-curvas.py`).

## Instructions & Scope
1. Read `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md` and `PROJECT.md`.
2. Install `pytest` in the Python 3.11 environment if missing (`pip3 install pytest`). Verify with `python3 -m pytest --version`.
3. Create `TEST_INFRA.md` at project root using the standard test infrastructure template:
   - Test philosophy (opaque-box, requirement-driven)
   - Feature inventory & mapping
   - Test runner command (`python3 -m pytest tests/test_teorema_fundamental.py -v`)
   - 4-Tier test architecture
4. Design and implement the comprehensive test suite in `tests/test_teorema_fundamental.py`:
   - **Tier 1 - Feature Coverage**:
     - Mathematical ODE integration & frame orthonormality: ||T||=1, ||N||=1, ||B||=1, T·N=0, T·B=0, N·B=0, det(F)=+1.
     - Curve classification for all 8 categories: `reta`, `circulo`, `helice_circular`, `helice_cilindrica_geral` (Lancret), `espiral_de_cornu`, `espiral_logaritmica`, `curva_plana`, `curva_espacial`.
     - CLI argument parsing & validation (positional vs flags, default intervals `[0, 6.28]`, default points 500).
     - Automatic filename generation and sanitization (`circulo-k1-t0-I0_6.28.html`, `helice_circular-k1-t1-I0_6.28.html`, replacement of `/`, `*`, `+`, `^`).
     - HTML output creation: checks HTML file exists, occupies `100vw`/`100vh`, contains Plotly div and script.
   - **Tier 2 - Boundary & Corner Cases**:
     - Zero curvature $\kappa = 0$ (straight line, infinite radius handling).
     - Singularities / undefined domain (e.g. $1/s$ at $s=0$).
     - Very small / large intervals (e.g. $[0, 0.01]$, $[0, 100]$).
     - Inverted intervals $s_0 \ge s_1$ (graceful error exit code 1).
     - Discretization point limits ($N < 2$ rejected).
     - Syntax errors in expressions (e.g. `2*+*3`, malicious inputs blocked).
   - **Tier 3 - Cross-Feature Combinations**:
     - Variable curvature + constant torsion (generalized cylindrical helix: $\kappa(s) = 1 + s, \tau(s) = 2(1 + s)$).
     - Polynomial curvature + zero torsion (Cornu spiral: $\kappa = 2s, \tau = 0$).
     - Inverted radius curvature + zero torsion (Log spiral: $\kappa = 1/(s+1), \tau = 0$).
     - Planar vs 3D camera projection checks.
   - **Tier 4 - Real-World Analytical Acceptance Benchmarks**:
     - Circle test ($\kappa = 2, \tau = 0$ over $[0, \pi/2]$ and $[0, \pi]$): verify radius $R=0.5$, arc length, and chord distance within $10^{-3}$ error.
     - Circular Helix test ($\kappa = 1, \tau = 1$ over $[0, 2\pi\sqrt{2}]$): verify radius $0.5$, pitch $\pi$, and relative error against analytical $r_{frenet}(s)$ within $10^{-3}$.
     - Straight line test ($\kappa = 0, \tau = 0$): length $L$, unit tangent along x-axis.
     - Clothoid test ($\kappa = s, \tau = 0$): compare with `scipy.special.fresnel`.
5. Run the test suite using `python3 -m pytest tests/test_teorema_fundamental.py -v`. (Tests may import `curva_engine` or `teorema-fundamental-curvas.py` conditionally or test CLI subprocess calls; structure tests so that as modules are created, tests execute seamlessly).
6. Create `TEST_READY.md` at project root summarizing all test tiers, test count, runner command, and feature checklist.
7. Write your handoff report to `handoff.md` in your working directory and notify the orchestrator via `send_message`.

## 2026-09-30T14:52:24Z
From: 0b0dffe7-95be-4cd3-9ff5-acde191dd517 (parent)
You are assigned to the Fundamental Theorem of Curves project.
Your assigned working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_test_writer_t1_1
Project root: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas
Original user request: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md
Your detailed task assignment: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_test_writer_t1_1/DISPATCH.md
Project specification: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md

Read ORIGINAL_REQUEST.md, DISPATCH.md, and PROJECT.md.
You exclusively own:
- tests/__init__.py
- tests/test_teorema_fundamental.py
- TEST_INFRA.md (at project root)
- TEST_READY.md (at project root)
Do NOT modify implementation code files.

Install pytest if needed (`pip3 install pytest`).
Design and implement the comprehensive 4-tier test suite in `tests/test_teorema_fundamental.py` covering:
- Tier 1: Feature coverage (math integration, frame orthonormality, classification, CLI args, output generation).
- Tier 2: Boundary & corner cases (zero curvature, singularities, interval bounds, point count limits, syntax errors).
- Tier 3: Pairwise combinations (different curvature and torsion functions).
- Tier 4: Real-world analytical acceptance benchmarks (circle radius 0.5, helix isometry, clothoid with Fresnel, straight line).
Write TEST_INFRA.md and TEST_READY.md when tests are complete.
Run pytest to verify.
Write your handoff report to handoff.md and notify the orchestrator with send_message.
