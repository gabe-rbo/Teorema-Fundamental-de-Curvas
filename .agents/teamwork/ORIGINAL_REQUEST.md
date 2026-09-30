# Original User Request

## Initial Request — 2026-09-30T14:40:50Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full team

Implement a comprehensive Python CLI tool (`teorema-fundamental-curvas.py`) that reconstructs plane and space curves from given curvature $\kappa(s)$ and torsion $\tau(s)$ by integrating the Frenet-Serret differential equations (Fundamental Theorem of Curves). The tool outputs a responsive, full-screen interactive Plotly HTML visualization containing the complete Frenet apparatus, bottom slider navigation, click-to-point curve traversal, automated curve classification, and commits the repository to GitHub.

Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Integrity mode: development

## Requirements

### R1. Mathematical Engine & Curve Reconstruction
- Solve the Frenet-Serret system of ODEs in $\mathbb{R}^3$:
  $$\frac{dT}{ds} = \kappa(s) N(s), \quad \frac{dN}{ds} = -\kappa(s) T(s) + \tau(s) B(s), \quad \frac{dB}{ds} = -\tau(s) N(s), \quad \frac{dr}{ds} = T(s)$$
  subject to initial orthonormal frame $T(s_0) = (1, 0, 0)$, $N(s_0) = (0, 1, 0)$, $B(s_0) = (0, 0, 1)$ and $r(s_0) = (0, 0, 0)$ (or canonical planar frame when $\tau(s) \equiv 0$).
- Support mathematical expressions for $\kappa(s)$ and $\tau(s)$ (constants, polynomial, trigonometric, exponential, rational functions of arc length $s$) parsed safely via SymPy / NumPy.
- Use SciPy's high-order ODE integrators (`solve_ivp`, e.g., RK45 or DOP853) with orthonormalization safeguards (Gram-Schmidt / SVD) along the integration path to preserve frame orthonormality $\|T\|=\|N\|=\|B\|=1$ and $\det([T, N, B]) = 1$.
- Automatically classify the curve based on $\kappa(s)$ and $\tau(s)$ into known geometric classes:
  - $\kappa = 0$: `reta` (straight line)
  - $\kappa = \text{const} > 0, \tau = 0$: `circulo` (circle)
  - $\kappa = \text{const} > 0, \tau = \text{const} \ne 0$: `helice_circular` (circular helix)
  - $\tau / \kappa = \text{const} \ne 0$: `helice_cilindrica_geral` (generalized cylindrical helix / Lancret's theorem)
  - $\tau = 0$ with $\kappa(s) = c \cdot s$: `espiral_de_cornu` (Clothoid / Cornu spiral)
  - $\tau = 0$ with $\kappa(s) = \frac{1}{as + b}$: `espiral_logaritmica` (logarithmic spiral)
  - Fallback if not specifically classified: `curva_plana` if $\tau \equiv 0$, or `curva_espacial` if $\tau \not\equiv 0$.

### R2. CLI Interface & Naming Convention
- Command-line arguments:
  - `curvatura`: mathematical expression or constant for $\kappa(s)$ (required positional or flagged).
  - `torcao`: mathematical expression or constant for $\tau(s)$ (optional, defaults to `"0"` for planar curves).
  - `--intervalo` / `-i`: start and end of arc length interval $[s_0, s_1]$ (default: $[0, 2\pi]$ or $[0, 10]$).
  - `--num-pontos` / `-n`: number of discretization points (default: 500).
  - `--output` / `-o`: output HTML filename (optional).
- If `--output` is not specified, format the filename automatically as:
  `<identificacao_da_curva>-k<curvatura>-t<torcao>-I<InicioIntervalo_FimIntervalo>.html`
  with any characters unsafe for filenames sanitized (e.g., `/` replaced by `_div_`, `*` by `_mult_`).

### R3. Interactive Plotly Visualization & Differential Apparatus
- Generate an interactive Plotly HTML page styled to automatically expand to 100% viewport width and height (`100vw`, `100vh`, no unnecessary scrollbars).
- Differential geometry apparatus visualized at the active point $r(s)$:
  - Curve trajectory $r(s)$.
  - Frenet frame unit vectors: Tangent $\vec{T}(s)$ (green), Principal Normal $\vec{N}(s)$ (red), Binormal $\vec{B}(s)$ (blue).
  - Tangent line: $L_T(u) = r(s) + u \vec{T}(s)$.
  - Osculating plane: plane passing through $r(s)$ spanned by $\vec{T}$ and $\vec{N}$ (normal to $\vec{B}$).
  - Normal plane: plane passing through $r(s)$ spanned by $\vec{N}$ and $\vec{B}$ (normal to $\vec{T}$).
  - Rectifying plane: plane passing through $r(s)$ spanned by $\vec{T}$ and $\vec{B}$ (normal to $\vec{N}$).
  - Osculating circle: circle of radius $\rho(s) = 1/|\kappa(s)|$ centered at $c(s) = r(s) + \frac{1}{\kappa(s)} \vec{N}(s)$ lying in the osculating plane (when $\kappa(s) \ne 0$).
  - For planar curves ($\tau = 0$): render in clean 2D/3D planar projection with diedro de Frenet $\{T, N\}$ and osculating circle.
- Interactivity:
  - Bottom slider allowing the user to scrub parameter $s$ continuously from $s_0$ to $s_1$, updating the position, Frenet frame, tangent line, planes, and osculating circle.
  - Plotly click event (`plotly_click` callback injected into HTML) so clicking on any point along the curve jumps the slider and active apparatus immediately to that point.
  - Interactive legend where each component (planes, frame vectors, osculating circle, tangent line) can be toggled on/off.

### R4. Test Suite, Documentation & GitHub Deployment
- Provide comprehensive automated tests (`tests/test_teorema_fundamental.py`) verifying:
  - Numerical integration accuracy against known analytical curves (circle radius $R$, helix radius and pitch, straight line length, clothoid).
  - Orthonormality of the reconstructed Frenet frame ($\|T\|=1, \|N\|=1, \|B\|=1, T \cdot N = 0, T \cdot B = 0, N \cdot B = 0$).
  - Correct automatic classification and file naming logic.
  - CLI argument parsing and error handling.
- Initialize git repository, configure remote repository on GitHub using `gh` CLI for account `gabe-rbo`, and push initial code, documentation (`README.md`), and example outputs.

## Acceptance Criteria

### Mathematical Verification
- [ ] Circle test: with $\kappa(s) = 2$ and $\tau(s) = 0$ over $[0, \pi]$, reconstructed curve forms a semicircle of radius $0.5$ with endpoint error $< 10^{-3}$.
- [ ] Helix test: with $\kappa(s) = 1$ and $\tau(s) = 1$ over $[0, 2\pi\sqrt{2}]$, reconstructed curve matches circular helix $r(t) = (\frac{1}{2}\cos(\sqrt{2}t), \frac{1}{2}\sin(\sqrt{2}t), \frac{1}{2}t)$ within $10^{-3}$ relative error.
- [ ] Frame orthonormality: $|\|T\| - 1| < 10^{-4}$, $|\|N\| - 1| < 10^{-4}$, $|\|B\| - 1| < 10^{-4}$, and $|T \cdot N| < 10^{-4}$ at all integration steps.

### CLI & Automation
- [ ] Executing `python teorema-fundamental-curvas.py "1" "1" -i 0 6.28` produces `helice_circular-k1-t1-I0_6.28.html` without errors.
- [ ] Executing `python teorema-fundamental-curvas.py "1" -i 0 6.28` (without $\tau$) detects planar circle and produces `circulo-k1-t0-I0_6.28.html`.
- [ ] Specifying `-o test_out.html` correctly writes output to `test_out.html`.

### UI & Interactivity
- [ ] Generated HTML opens in browser and occupies 100% of viewport width and height.
- [ ] Moving the slider updates the point position, frame vectors ($T, N, B$), tangent line, osculating plane, normal plane, rectifying plane, and osculating circle.
- [ ] Clicking any point on the curve navigates the slider and frame directly to that point.
- [ ] Legend allows individual toggling of planes, vectors, and osculating circle.

### Repository & Deployment
- [ ] Clean `git status`, commits pushed to `gabe-rbo` GitHub repository.
- [ ] Comprehensive `README.md` with theoretical foundations (citing Toponogov, Tenenblat, and Alencar et al.), usage guide, and mathematical equations.
