# Project: Fundamental Theorem of Curves (Teorema Fundamental de Curvas)

## Architecture
The application reconstructs plane and space curves in $\mathbb{R}^3$ from user-specified curvature $\kappa(s)$ and torsion $\tau(s)$ by integrating the Frenet-Serret differential system. It outputs a responsive, full-screen interactive Plotly visualization with dynamic apparatus, scrubbable slider, and click-to-point traversal.

### System Components:
1. **Mathematical Engine & Classification (`curva_engine.py`)**: [DONE]
   - Safe AST validation of math strings $\kappa(s), \tau(s)$
   - Fast broadcasting NumPy lambdification
   - Frenet-Serret 12-ODE state integration with `scipy.integrate.solve_ivp` (DOP853/RK45)
   - Vectorized Modified Gram-Schmidt $SO(3)$ orthonormalization
   - Deterministic 8-class curve classifier (including Lancret's theorem)
   - Output filename generator and sanitization
2. **Interactive Visualization Engine (`curva_viz.py`)**: [DONE]
   - 10-trace composite 3D Plotly scene (Curve, Active Point, T, N, B, Tangent line, Osculating plane, Normal plane, Rectifying plane, Osculating circle)
   - Planar curve adaptation ($\tau \equiv 0$ top-down camera and clean Diedro view)
   - Selective frame animation pipeline (`traces=[1..9]`)
   - 100vw x 100vh responsive HTML shell with CSS reset and `100dvh`
   - Custom JavaScript injection (`plotly_click` curve snapping, slider synchronization, floating glassmorphic HUD card)
3. **CLI Interface & Main Script (`teorema-fundamental-curvas.py`)**: [IN_PROGRESS]
   - Argument parsing: `curvatura`, `torcao`, `-i/--intervalo`, `-n/--num-pontos`, `-o/--output`
   - Validation & friendly error diagnostics
   - Output HTML generation
4. **Test Suite (`tests/test_teorema_fundamental.py`)**: [DONE]
   - Tiers 1-4 automated tests via `pytest`
5. **Documentation & Deployment**: [PLANNED]
   - `README.md` with complete mathematical foundations, citations (Toponogov, Tenenblat, Alencar et al.), and usage guide
   - Git repository initialized on `main` and pushed to GitHub account `gabe-rbo` (`gabe-rbo/Teorema-Fundamental-de-Curvas`)

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| T1 | E2E Test Suite Track | `pytest` install, `TEST_INFRA.md`, `tests/test_teorema_fundamental.py` (Tiers 1-4), publish `TEST_READY.md` | Survey | **DONE** |
| M1 | Math Engine & Classification | `curva_engine.py`: AST parser, lambdification, ODE solver, SO(3) orthonormalization, classifier, filename generator | Survey | **DONE** |
| M2 | Visualization Engine | `curva_viz.py`: Plotly 10-trace apparatus, selective frames, slider, JS click injection, responsive fullscreen HTML shell, HUD | M1 | **DONE** |
| M3 | CLI Interface & Integration | `teorema-fundamental-curvas.py`: Argparse, validation, connecting engine + viz, CLI error handling | M1, M2 | **IN_PROGRESS** |
| M4 | Final Milestone (Pass E2E & Hardening) | Phase 1: Pass 100% of E2E tests (T1-T4). Phase 2: Tier 5 Adversarial Coverage Hardening | M3, T1 | **PLANNED** |
| M5 | Documentation & GitHub Deployment | `README.md`, git commit, `gh repo create gabe-rbo/Teorema-Fundamental-de-Curvas` & push | M4 | **PLANNED** |

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
def build_curve_figure(curve_data: CurveResult, title: str | None = None) -> go.Figure: ...
def export_interactive_html(
    curve_data: CurveResult | go.Figure,
    output_path: str,
    title: str | None = None,
    include_plotlyjs: bool | str = 'cdn'
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
