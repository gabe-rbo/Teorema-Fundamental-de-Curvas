# Project: Fundamental Theorem of Curves (Teorema Fundamental de Curvas)

## Architecture
The application reconstructs plane and space curves in $\mathbb{R}^3$ from user-specified curvature $\kappa(s)$ and torsion $\tau(s)$ by integrating the Frenet-Serret differential system. It outputs a responsive, full-screen interactive Plotly visualization with dynamic apparatus, scrubbable slider, and click-to-point traversal.

### System Components:
1. **Mathematical Engine & Classification (`curva_engine.py`)**:
   - Safe AST validation of math strings $\kappa(s), \tau(s)$
   - Fast broadcasting NumPy lambdification
   - Frenet-Serret 12-ODE state integration with `scipy.integrate.solve_ivp` (DOP853/RK45)
   - Vectorized Modified Gram-Schmidt $SO(3)$ orthonormalization
   - Deterministic 8-class curve classifier (including Lancret's theorem)
   - Output filename generator and sanitization
2. **Interactive Visualization Engine (`curva_viz.py`)**:
   - 10-trace composite 3D Plotly scene (Curve, Active Point, T, N, B, Tangent line, Osculating plane, Normal plane, Rectifying plane, Osculating circle)
   - Planar curve adaptation ($\tau \equiv 0$ top-down camera and clean Diedro view)
   - Selective frame animation pipeline (`traces=[1..9]`)
   - 100vw x 100vh responsive HTML shell with CSS reset and `100dvh`
   - Custom JavaScript injection (`plotly_click` curve snapping, slider synchronization, floating glassmorphic HUD card)
3. **CLI Interface & Main Script (`teorema-fundamental-curvas.py`)**:
   - Argument parsing: `curvatura`, `torcao`, `-i/--intervalo`, `-n/--num-pontos`, `-o/--output`
   - Validation & friendly error diagnostics
   - Output HTML generation
4. **Test Suite (`tests/test_teorema_fundamental.py`)**:
   - Tiers 1-4 automated tests via `pytest`
5. **Documentation & Deployment**:
   - `README.md` with complete mathematical foundations, citations (Toponogov, Tenenblat, Alencar et al.), and usage guide
   - Git repository initialized on `main` and pushed to GitHub account `gabe-rbo` (`gabe-rbo/Teorema-Fundamental-de-Curvas`)

---

## Feature Inventory

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Test Environment Setup | Install `pytest` in Python 3.11 environment | Track E2E (T1) | Environment Survey |
| 2 | AST Math Whitelist | Validates AST expressions to prevent code execution | Milestone M1 | Spec Miner Survey 1 |
| 3 | Math Expression Lambdification | Safe SymPy parse & NumPy lambdify with broadcasting | Milestone M1 | Spec Miner Survey 1 |
| 4 | Frenet-Serret ODE Formulation | 12-coupled 1st-order ODE system in $\mathbb{R}^3$ | Milestone M1 | ORIGINAL_REQUEST R1 |
| 5 | High-Order ODE Integration | `solve_ivp` with DOP853/RK45, $rtol=10^{-9}, atol=10^{-9}$ | Milestone M1 | ORIGINAL_REQUEST R1 |
| 6 | $SO(3)$ Orthonormalization | Vectorized Gram-Schmidt + cross-product binormal restoration | Milestone M1 | ORIGINAL_REQUEST R1 |
| 7 | Curve Classification Engine | 8-class classification (`reta`, `circulo`, `helice_circular`, `helice_cilindrica_geral`, `espiral_de_cornu`, `espiral_logaritmica`, `curva_plana`, `curva_espacial`) | Milestone M1 | ORIGINAL_REQUEST R1 |
| 8 | Filename Generator & Sanitizer | `<identificacao_da_curva>-k<k>-t<t>-I<s0>_<s1>.html` with sanitization | Milestone M1 | ORIGINAL_REQUEST R2 |
| 9 | 100vw x 100vh Responsive Shell | CSS reset, `100dvh`, zero scrollbars, auto-resize | Milestone M2 | ORIGINAL_REQUEST R3 |
| 10 | Differential Apparatus Traces | 10-trace 3D scene: curve, point, T (green), N (red), B (blue), tangent line, 3 planes (Mesh3d), osculating circle | Milestone M2 | ORIGINAL_REQUEST R3 |
| 11 | Planar Curve Adaptation | Top-down camera view, Diedro emphasis when $\tau \equiv 0$ | Milestone M2 | ORIGINAL_REQUEST R3 |
| 12 | Bottom Slider Animation | Continuous scrub of parameter $s$, selective frame updates | Milestone M2 | ORIGINAL_REQUEST R3 |
| 13 | Click-to-Point Navigation | `plotly_click` JS listener snapping slider and apparatus | Milestone M2 | ORIGINAL_REQUEST R3 |
| 14 | Legend Toggling | Independent toggle of planes, vectors, circle | Milestone M2 | ORIGINAL_REQUEST R3 |
| 15 | Real-Time HUD Metrics | Floating glassmorphic card showing $s, r, \kappa, \tau, \rho$ | Milestone M2 | Spec Miner Survey 3 |
| 16 | CLI Argument Parsing | Positional & flagged args, defaults, exit codes | Milestone M3 | ORIGINAL_REQUEST R2 |
| 17 | CLI Pipeline Orchestration | Integration of engine + viz + file writer in `teorema-fundamental-curvas.py` | Milestone M3 | ORIGINAL_REQUEST R2 |
| 18 | E2E Tier 1 (Feature Coverage) | >=5 tests per feature (math, classification, CLI, output) | Track E2E (T1) | ORIGINAL_REQUEST R4 |
| 19 | E2E Tier 2 (Boundary & Corners) | >=5 tests per feature (zero curvature, singularities, intervals) | Track E2E (T1) | ORIGINAL_REQUEST R4 |
| 20 | E2E Tier 3 (Cross-Feature Combinations) | Pairwise combinations of curvature & torsion forms | Track E2E (T1) | ORIGINAL_REQUEST R4 |
| 21 | E2E Tier 4 (Real-World Benchmarks) | Exact analytical checks (Circle radius 0.5, Helix isometry, Clothoid, Straight line) | Track E2E (T1) | ORIGINAL_REQUEST R4 |
| 22 | Final Verification & Hardening | Pass 100% E2E tests + Tier 5 adversarial hardening | Final Milestone (M4) | Orchestration Pattern |
| 23 | Comprehensive Documentation | `README.md` with theory, citations (Toponogov, Tenenblat, Alencar, do Carmo, Lancret), equations, CLI guide | Milestone M5 | ORIGINAL_REQUEST R4 |
| 24 | Git & GitHub Deployment | Git init on main, commit, `gh repo create gabe-rbo/Teorema-Fundamental-de-Curvas`, push | Milestone M5 | ORIGINAL_REQUEST R4 |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| T1 | E2E Test Suite Track | `pytest` install, `TEST_INFRA.md`, `tests/test_teorema_fundamental.py` (Tiers 1-4), publish `TEST_READY.md` | Survey | DONE |
| M1 | Math Engine & Classification | `curva_engine.py`: AST parser, lambdification, ODE solver, SO(3) orthonormalization, classifier, filename generator | Survey | DONE |
| M2 | Visualization Engine | `curva_viz.py`: Plotly 10-trace apparatus, selective frames, slider, JS click injection, responsive fullscreen HTML shell, HUD | M1 | DONE |
| M3 | CLI Interface & Integration | `teorema-fundamental-curvas.py`: Argparse, validation, connecting engine + viz, CLI error handling | M1, M2 | DONE |
| M4 | Final Milestone (Pass E2E & Hardening) | Phase 1: Pass 100% of E2E tests (T1-T4). Phase 2: Tier 5 Adversarial Coverage Hardening | M3, T1 | DONE |
| M5 | Documentation & GitHub Deployment | `README.md`, git commit, `gh repo create gabe-rbo/Teorema-Fundamental-de-Curvas` & push | M4 | IN_PROGRESS |

---

## Interface Contracts

### `curva_engine.py` ↔ `teorema-fundamental-curvas.py`
```python
def parse_and_validate_expression(expr_str: str) -> sp.Expr: ...
def create_evaluator(expr: sp.Expr) -> Callable[[np.ndarray | float], np.ndarray | float]: ...

@dataclass
class CurveResult:
    s: np.ndarray             # shape (N,)
    r: np.ndarray             # shape (3, N)
    T: np.ndarray             # shape (3, N)
    N: np.ndarray             # shape (3, N)
    B: np.ndarray             # shape (3, N)
    kappa: np.ndarray         # shape (N,)
    tau: np.ndarray           # shape (N,)
    classification: str       # e.g., 'circulo', 'helice_circular'
    s0: float
    s1: float

def reconstruct_curve(
    kappa_expr_str: str,
    tau_expr_str: str = "0",
    s0: float = 0.0,
    s1: float = 6.283185307179586,
    num_points: int = 500
) -> CurveResult: ...

def classify_curve(
    kappa_expr: sp.Expr,
    tau_expr: sp.Expr,
    s_vals: np.ndarray,
    kappa_vals: np.ndarray,
    tau_vals: np.ndarray
) -> str: ...

def sanitize_expr_for_filename(expr_str: str) -> str: ...
def generate_output_filename(curve_class: str, kappa_str: str, tau_str: str, s0: float, s1: float) -> str: ...
```

### `curva_viz.py` ↔ `teorema-fundamental-curvas.py`
```python
def build_curve_figure(curve_data: CurveResult) -> go.Figure: ...
def export_interactive_html(
    curve_data: CurveResult,
    output_path: str,
    title: str | None = None
) -> str: ...
```

---

## Code Layout
```
/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/
├── .agents/                      # Agent metadata (do NOT touch source code here)
├── tests/
│   ├── __init__.py
│   └── test_teorema_fundamental.py  # Comprehensive E2E test suite (Tiers 1-4)
├── curva_engine.py              # Mathematical engine, ODE integration, classification
├── curva_viz.py                 # Plotly 3D visualizer, HTML template, JS injection
├── teorema-fundamental-curvas.py # Main executable CLI entrypoint
├── requirements.txt             # Project dependencies (numpy, scipy, sympy, plotly, pytest)
├── README.md                    # Theoretical foundations, citations, user manual
└── TEST_READY.md                # Signal when E2E test suite is published
```
