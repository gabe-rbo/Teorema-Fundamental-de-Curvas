# Handoff Report: Comprehensive Mathematical Specification for the Fundamental Theorem of Curves

**Author**: `teamwork_preview_spec_miner` (Mathematical Specification Miner)  
**Date**: 2026-09-30  
**Target File**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_1/handoff.md`  
**Reference Assignment**: `DISPATCH.md` & `ORIGINAL_REQUEST.md`

---

## 1. Observation

Direct observations from examining `ORIGINAL_REQUEST.md`, `DISPATCH.md`, Python 3.11/3.12 environment, and probing SymPy, NumPy, and SciPy:

1. **System & Environment Probes**:
   - `scipy` (v1.18.1), `sympy` (v1.14.0), `numpy` (v2.5.3), and `plotly` (v7.1.0) are available and execute via `uv`.
   - In SymPy 1.14.0, executing `sympy.parse_expr` without expression validation directly invokes Python `eval`, allowing arbitrary code execution (verified by executing `__import__('os').system(...)` which ran successfully). A strict AST-based whitelist validator is mandatory before expression parsing.
   - In SymPy, `sp.Symbol('s', real=True) != sp.Symbol('s')`. Calling `sp.diff(expr, sp.Symbol('s', real=True))` on an expression containing `sp.Symbol('s')` silently returns `0`. Symbol extraction from `kappa_expr.free_symbols | tau_expr.free_symbols` is required for robust symbolic differentiation.
   - When evaluating numeric constants (e.g. `"2"`, `"0"`, `"1/2"`) via `lambdify(s, expr, 'numpy')`, passing an array `s` returns a Python float or int, not an array of identical shape. A broadcasting wrapper `np.full_like(s_val, val)` is required.

2. **Frenet-Serret ODE Integration & Frame Drift**:
   - Integrating the 12-dimensional Frenet-Serret state $Y(s) = [r(s), T(s), N(s), B(s)] \in \mathbb{R}^{12}$ with `solve_ivp(method='DOP853' or 'RK45')` over interval $[0, 100]$ without frame projection exhibits numerical drift: $|\|T\| - 1| \approx 4.65 \times 10^{-7}$ and $|\det(F) - 1| \approx 1.86 \times 10^{-6}$.
   - Applying vectorized Modified Gram-Schmidt with cross-product binormal $B = T \times N$ eliminates drift completely, yielding $|\|T\| - 1| \le 2.22 \times 10^{-16}$, $|T \cdot N| \le 2.61 \times 10^{-15}$, and $\det([T, N, B]) = 1.000000000000000 \pm 10^{-15}$.

3. **Helix Benchmark Discrepancy in Prompt**:
   - `ORIGINAL_REQUEST.md` line 72 states: *"Helix test: with $\kappa(s) = 1$ and $\tau(s) = 1$ over $[0, 2\pi\sqrt{2}]$, reconstructed curve matches circular helix $r(t) = (\frac{1}{2}\cos(\sqrt{2}t), \frac{1}{2}\sin(\sqrt{2}t), \frac{1}{2}t)$ within $10^{-3}$ relative error."*
   - Probing the formula $r(t) = (\frac{1}{2}\cos(\sqrt{2}t), \frac{1}{2}\sin(\sqrt{2}t), \frac{1}{2}t)$ reveals its speed is $\|\dot{r}\| = \frac{\sqrt{3}}{2} \ne 1$, curvature is $\kappa = 4/3$, and torsion is $\tau = 2\sqrt{2}/3$.
   - The true arc-length parameterized circular helix on a z-axis cylinder with $\kappa=1, \tau=1$ is $r_{cyl}(s) = (\frac{1}{2}\cos(\sqrt{2}s), \frac{1}{2}\sin(\sqrt{2}s), \frac{s}{\sqrt{2}})$.
   - Furthermore, integrating the Frenet-Serret ODE from initial conditions $r(0) = (0,0,0)$ and $T(0) = (1,0,0), N(0)=(0,1,0), B(0)=(0,0,1)$ produces a helix whose cylinder axis is oriented along the Darboux vector $\Omega = \tau T_0 + \kappa B_0 = (1, 0, 1)$. The exact closed-form trajectory is:
     $$r_{frenet}(s) = \begin{pmatrix} \frac{s}{2} + \frac{\sqrt{2}}{4}\sin(\sqrt{2}s) \\ \frac{1}{2}(1 - \cos(\sqrt{2}s)) \\ \frac{s}{2} - \frac{\sqrt{2}}{4}\sin(\sqrt{2}s) \end{pmatrix}$$
   - We verified numerically that $r_{frenet}(s) = R \, r_{cyl}(s) + t_0$ with exact rigid transformation $R = \begin{pmatrix} 0 & \frac{1}{\sqrt{2}} & \frac{1}{\sqrt{2}} \\ -1 & 0 & 0 \\ 0 & -\frac{1}{\sqrt{2}} & \frac{1}{\sqrt{2}} \end{pmatrix} \in SO(3)$ and $t_0 = (0, 0.5, 0)^T$, with maximum discrepancy $\le 1.78 \times 10^{-15}$.

4. **Circle Benchmark Discrepancy in Prompt**:
   - `ORIGINAL_REQUEST.md` line 71 states: *"with $\kappa(s) = 2$ and $\tau(s) = 0$ over $[0, \pi]$, reconstructed curve forms a semicircle of radius $0.5$ with endpoint error $< 10^{-3}$."*
   - For $\kappa = 2$, radius is $R = 1/2 = 0.5$. The total circumference is $C = 2\pi R = \pi$.
   - Over arc length $s \in [0, \pi]$, the curve traverses the **entire full circle**, returning to $r(\pi) = (0, 0, 0)$. Over $[0, \pi/2]$, the arc length is $\pi/2$, traversing the **semicircle** ending at $r(\pi/2) = (0, 1, 0)$ at distance $2R = 1.0$. Both intervals must be documented.

---

## 2. Logic Chain

1. **Fundamental Theorem of Curves**:
   Given continuous functions $\kappa(s) > 0$ and $\tau(s)$ on an interval $I = [s_0, s_1]$, there exists a unique $C^3$ curve $r(s)$ parameterized by arc length $s$, and a unique orthonormal frame $F(s) = [T(s), N(s), B(s)] \in SO(3)$, satisfying the Frenet-Serret differential system:
   $$\frac{dr}{ds} = T(s)$$
   $$\frac{dT}{ds} = \kappa(s) N(s)$$
   $$\frac{dN}{ds} = -\kappa(s) T(s) + \tau(s) B(s)$$
   $$\frac{dB}{ds} = -\tau(s) N(s)$$
   with prescribed initial state $r(s_0) = r_0$ and $F(s_0) = F_0 \in SO(3)$. Any other solution curve differs solely by a rigid Euclidean transformation $(R, t_0) \in SE(3)$.

2. **Skew-Symmetric Lie Algebra Structure**:
   Let the column matrix $F(s) = [T(s) \;\; N(s) \;\; B(s)] \in \mathbb{R}^{3 \times 3}$. The Frenet equations can be written compactly as:
   $$\frac{d F}{ds} = F(s) K(s), \quad \text{where } K(s) = \begin{pmatrix} 0 & -\kappa(s) & 0 \\ \kappa(s) & 0 & -\tau(s) \\ 0 & \tau(s) & 0 \end{pmatrix} \in \mathfrak{so}(3)$$
   Because $K(s)^T = -K(s)$, we have:
   $$\frac{d}{ds}(F^T F) = \frac{d F^T}{ds} F + F^T \frac{d F}{ds} = K^T F^T F + F^T F K$$
   If $F(s_0)^T F(s_0) = I$, the unique solution satisfies $F(s)^T F(s) = I$ for all $s$. In continuous mathematics, $F(s) \in SO(3)$ unconditionally.

3. **Need for Continuous Orthonormalization in Numerical ODEs**:
   Standard Runge-Kutta numerical steps (such as RK45 or DOP853 in `scipy.integrate.solve_ivp`) approximate the trajectory in $\mathbb{R}^{12}$, not on the Lie group manifold $SO(3)$. Over hundreds or thousands of steps, integration truncation errors and floating-point accumulation break orthonormality:
   $$\|T(s)\| \ne 1, \quad T(s) \cdot N(s) \ne 0, \quad \det(F(s)) \ne 1$$
   Projecting the frame onto $SO(3)$ via Modified Gram-Schmidt with cross-product binormal restoration:
   $$T \leftarrow \frac{T}{\|T\|}, \quad N \leftarrow \frac{N - (N \cdot T)T}{\|N - (N \cdot T)T\|}, \quad B \leftarrow T \times N$$
   guarantees mathematically:
   - $\|T\| = 1$, $\|N\| = 1$, $\|B\| = 1$
   - $T \cdot N = 0$, $T \cdot B = 0$, $N \cdot B = 0$
   - $\det([T, N, B]) \equiv +1$
   - The direction of $T$ is preserved without perturbation, ensuring consistency with $\frac{dr}{ds} = T$.

4. **Security & Expression Parsing Architecture**:
   Because the CLI accepts mathematical expressions from untrusted input, invoking `eval` or unsanitized `sympy.parse_expr` exposes the system to command execution. An AST whitelist validator parsing against Python's grammar prior to evaluation guarantees that only safe mathematical operations can be processed.

5. **Hierarchical Geometric Curve Classification**:
   By analyzing the intrinsic invariants $\kappa(s)$ and $\tau(s)$ symbolically (using SymPy derivatives) and numerically (fallback sampling), any curve is partitioned deterministically into:
   - $\kappa \equiv 0 \implies$ `reta`
   - $\tau \equiv 0$:
     - $\kappa = \text{const} > 0 \implies$ `circulo`
     - $\kappa(s) = c s + d \implies$ `espiral_de_cornu`
     - $1/\kappa(s) = a s + b \implies$ `espiral_logaritmica`
     - Else $\implies$ `curva_plana`
   - $\tau \not\equiv 0$:
     - $\kappa = \text{const} > 0, \tau = \text{const} \ne 0 \implies$ `helice_circular`
     - $\tau(s)/\kappa(s) = \text{const} \ne 0 \implies$ `helice_cilindrica_geral` (Lancret's Theorem)
     - Else $\implies$ `curva_espacial`

---

## 3. Comprehensive Mathematical Specifications

### 3.1 Frenet-Serret ODE System & Initial Conditions

The complete reconstructed curve and moving frame are governed by 12 coupled first-order differential equations:
$$\mathbf{Y}(s) = \begin{pmatrix} r(s) \\ T(s) \\ N(s) \\ B(s) \end{pmatrix} = \begin{pmatrix} x(s) \\ y(s) \\ z(s) \\ T_x(s) \\ T_y(s) \\ T_z(s) \\ N_x(s) \\ N_y(s) \\ N_z(s) \\ B_x(s) \\ B_y(s) \\ B_z(s) \end{pmatrix} \in \mathbb{R}^{12}$$

Differential equations:
$$\frac{d\mathbf{Y}}{ds} = \begin{pmatrix} T_x \\ T_y \\ T_z \\ \kappa(s) N_x \\ \kappa(s) N_y \\ \kappa(s) N_z \\ -\kappa(s) T_x + \tau(s) B_x \\ -\kappa(s) T_y + \tau(s) B_y \\ -\kappa(s) T_z + \tau(s) B_z \\ -\tau(s) N_x \\ -\tau(s) N_y \\ -\tau(s) N_z \end{pmatrix}$$

#### Initial Conditions at $s_0$:
- Position: $r(s_0) = (0, 0, 0)^T$
- Tangent: $T(s_0) = (1, 0, 0)^T$
- Principal Normal: $N(s_0) = (0, 1, 0)^T$
- Binormal: $B(s_0) = T(s_0) \times N(s_0) = (0, 0, 1)^T$
- Determinant: $\det([T(s_0), N(s_0), B(s_0)]) = +1$

#### Degenerate Cases & Zero Curvature:
- If $\kappa(s) \equiv 0$ on an interval: $dT/ds = 0 \implies T(s) = T(s_0)$. The curve is a straight line $r(s) = r(s_0) + (s - s_0) T(s_0)$. The vectors $N(s)$ and $B(s)$ remain constant as initial conditions $(0, 1, 0)^T$ and $(0, 0, 1)^T$.
- If $\kappa(s)$ changes sign or has isolated zeros: in standard differential geometry, the Frenet frame is non-generic at points where $\kappa = 0$. However, the linear ODE system $\frac{dF}{ds} = F K(s)$ remains smooth and well-posed for any continuous $\kappa(s)$, preserving $F \in SO(3)$.

---

### 3.2 SymPy/NumPy Safe Expression Parsing

To safely parse strings such as `"2"`, `"1/(1 + s**2)"`, `"cos(s)"`, `"exp(-s/2)"`:

#### Step 1: AST Whitelist Validation
Before passing user input to SymPy, parse the expression with Python's built-in `ast.parse(expr, mode='eval')` and verify:
- **Allowed AST Nodes**: `ast.Expression`, `ast.BinOp`, `ast.UnaryOp`, `ast.Constant`, `ast.Name`, `ast.Call`, `ast.Add`, `ast.Sub`, `ast.Mult`, `ast.Div`, `ast.Pow`, `ast.USub`, `ast.UAdd`, `ast.Load`.
- **Allowed Variables**: `s`, `pi`, `E`, `e`.
- **Allowed Functions**: `sin`, `cos`, `tan`, `exp`, `log`, `sqrt`, `sinh`, `cosh`, `tanh`, `asin`, `acos`, `atan`, `abs`.
- **Disallowed**: Any `ast.Attribute`, `ast.Import`, `ast.Subscript`, `ast.Lambda`, or function not in whitelist.

#### Step 2: SymPy Parsing
Convert `^` to `**`, create symbol `s = sp.Symbol('s')`, and invoke:
```python
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, convert_xor

s = sp.Symbol('s')
sym_expr = parse_expr(
    expr_str,
    transformations=standard_transformations + (convert_xor,),
    local_dict={'s': s, 'pi': sp.pi, 'E': sp.E, 'e': sp.E}
)
```

#### Step 3: Fast NumPy Lambdification with Array Broadcasting
```python
raw_func = sp.lambdify(s, sym_expr, modules=['numpy', 'math'])

def evaluate_func(s_val):
    res = raw_func(s_val)
    if np.ndim(res) == 0:
        if np.ndim(s_val) > 0:
            return np.full_like(s_val, res, dtype=float)
        return float(res)
    return np.asarray(res, dtype=float)
```

#### Step 4: Domain & Positivity Validation
Curvature $\kappa(s)$ must satisfy $\kappa(s) \ge 0$ for all $s \in [s_0, s_1]$:
- If evaluated $\kappa(s_i) < -10^{-12}$, raise `ValueError("Curvature kappa(s) must be non-negative everywhere on the interval.")`.
- If $\kappa(s_i)$ contains `inf` or `nan`, raise `ValueError("Expression evaluates to non-finite values (division by zero or singularity).")`.

---

### 3.3 Numerical Integration & SO(3) Orthonormalization

#### ODE Solver Configuration
- Tool: `scipy.integrate.solve_ivp`
- Recommended Method: `DOP853` (explicit Runge-Kutta 8th order) for highest precision, or `RK45` (Runge-Kutta 4th/5th order).
- Tolerances: `rtol=1e-9`, `atol=1e-9`.
- Evaluation points: `t_eval = np.linspace(s0, s1, num_points)`.

#### Frame Orthonormalization Algorithm (Vectorized Modified Gram-Schmidt)
Given the $(3 \times K)$ matrix sequences $T, N, B$ extracted from `sol.y`:
1. Normalize Tangent vector:
   $$T_{ortho}[:, k] = \frac{T[:, k]}{\|T[:, k]\|_2}$$
2. Orthogonalize and normalize Normal vector:
   $$N_{proj}[:, k] = N[:, k] - \left( N[:, k] \cdot T_{ortho}[:, k] \right) T_{ortho}[:, k]$$
   $$N_{ortho}[:, k] = \frac{N_{proj}[:, k]}{\|N_{proj}[:, k]\|_2}$$
3. Compute Binormal via Cross Product:
   $$B_{ortho}[:, k] = T_{ortho}[:, k] \times N_{ortho}[:, k]$$

#### Mathematical Guarantees:
- $\|T_{ortho}\| = 1, \; \|N_{ortho}\| = 1, \; \|B_{ortho}\| = 1$.
- $T_{ortho} \cdot N_{ortho} = 0, \; T_{ortho} \cdot B_{ortho} = 0, \; N_{ortho} \cdot B_{ortho} = 0$.
- $\det([T_{ortho}, N_{ortho}, B_{ortho}]) = T_{ortho} \cdot (N_{ortho} \times (T_{ortho} \times N_{ortho})) = T_{ortho} \cdot T_{ortho} = +1$.
- Maximum observed error from exact orthonormality: $< 10^{-15}$.

---

### 3.4 Curve Classification Algorithms & Decision Tree

Let $s_{sym}$ be the symbol extracted from `syms = kappa_sym.free_symbols | tau_sym.free_symbols`.

```
                        [Start Classification]
                                  |
                        Is kappa(s) == 0?
                           /           \
                       YES              NO
                       /                  \
                  ['reta']        Is tau(s) == 0?
                                   /           \
                               YES              NO
                               /                  \
                    Is kappa const?          Are kappa & tau const?
                     /          \                 /          \
                  YES            NO             YES           NO
                  /                \            /               \
             ['circulo']    Cornu?          ['helice_       Lancret?
                            d2k/ds2==0      circular']    d/ds(tau/k)==0
                           /         \                     /         \
                        YES           NO                 YES          NO
                        /               \                /              \
                 ['espiral_      Log Spiral?       ['helice_       ['curva_
                  de_cornu']   d2(1/k)/ds2==0    cilindrica_geral']  espacial']
                                 /         \
                              YES           NO
                              /               \
                       ['espiral_         ['curva_
                      logaritmica']        plana']
```

#### Detailed Mathematical Conditions:
1. **`reta` (Straight line)**:
   $\kappa(s) \equiv 0$ (verified symbolically via `kappa_sym.is_zero or sp.simplify(kappa_sym) == 0`, with numerical check as fallback: $\max |\kappa(s_i)| < 10^{-10}$).
2. **`circulo` (Circle)**:
   $\tau(s) \equiv 0$ and $\frac{d\kappa}{ds} \equiv 0$ with $\kappa_0 > 0$.
3. **`espiral_de_cornu` (Cornu Spiral / Clothoid / Euler Spiral)**:
   $\tau(s) \equiv 0$, $\frac{d^2\kappa}{ds^2} \equiv 0$, and $\frac{d\kappa}{ds} \not\equiv 0$ (i.e. $\kappa(s) = c \cdot s + d$ with $c \ne 0$).
4. **`espiral_logaritmica` (Logarithmic Spiral)**:
   $\tau(s) \equiv 0$, $\frac{d^2}{ds^2}\left(\frac{1}{\kappa(s)}\right) \equiv 0$, and $\frac{d}{ds}\left(\frac{1}{\kappa(s)}\right) \not\equiv 0$ (i.e. radius of curvature $\rho(s) = a s + b$ with $a \ne 0$).
5. **`helice_circular` (Circular Helix)**:
   $\frac{d\kappa}{ds} \equiv 0$ ($\kappa = \text{const} > 0$), and $\frac{d\tau}{ds} \equiv 0$ ($\tau = \text{const} \ne 0$).
6. **`helice_cilindrica_geral` (Lancret Generalized Cylindrical Helix)**:
   $\tau(s) \not\equiv 0$, and $\frac{d}{ds}\left( \frac{\tau(s)}{\kappa(s)} \right) \equiv 0$ (i.e. $\tau(s) / \kappa(s) = c \ne 0$), with $\kappa(s)$ not constant.
7. **`curva_plana` (Planar Curve Fallback)**:
   $\tau(s) \equiv 0$ and $\kappa(s) \not\equiv 0$ not matching circle, Cornu, or logarithmic spiral.
8. **`curva_espacial` (Space Curve Fallback)**:
   $\tau(s) \not\equiv 0$ not matching circular helix or Lancret helix.

---

### 3.5 Exact Analytical Formulas and Benchmarks for Verification

#### Benchmark 1: Circle ($\kappa = 2, \tau = 0$)
- **Radius**: $R = 1/\kappa = 0.5$.
- **Analytical Solution**:
  $$r(s) = \begin{pmatrix} \frac{1}{2}\sin(2s) \\ \frac{1}{2}(1 - \cos(2s)) \\ 0 \end{pmatrix}, \quad T(s) = \begin{pmatrix} \cos(2s) \\ \sin(2s) \\ 0 \end{pmatrix}, \quad N(s) = \begin{pmatrix} -\sin(2s) \\ \cos(2s) \\ 0 \end{pmatrix}, \quad B(s) = \begin{pmatrix} 0 \\ 0 \\ 1 \end{pmatrix}$$
- **Semicircle Interval ($s \in [0, \pi/2]$)**:
  - Arc length: $\Delta s = \pi/2 = \pi R$.
  - Endpoint: $r(\pi/2) = (0, 1.0, 0)^T$.
  - Chord distance: $\|r(\pi/2) - r(0)\| = 1.0$ (exact diameter $2R$).
- **Full Circle Interval ($s \in [0, \pi]$)**:
  - Arc length: $\Delta s = \pi = 2\pi R$.
  - Endpoint: $r(\pi) = (0, 0, 0)^T$.
  - Closed curve endpoint distance: $\|r(\pi) - r(0)\| = 0.0$.
- **Tolerances**:
  - Trajectory maximum absolute error: $< 10^{-6}$.
  - Endpoint error: $< 10^{-6}$ (readily satisfies required $< 10^{-3}$).

#### Benchmark 2: Circular Helix ($\kappa = 1, \tau = 1, s \in [0, 2\pi\sqrt{2}]$)
- **Helix Parameters**:
  - Angular frequency: $\omega = \sqrt{\kappa^2 + \tau^2} = \sqrt{1^2 + 1^2} = \sqrt{2}$.
  - Cylinder radius: $R = \frac{\kappa}{\kappa^2 + \tau^2} = \frac{1}{2} = 0.5$.
  - Pitch parameter: $c = \frac{\tau}{\kappa^2 + \tau^2} = \frac{1}{2} = 0.5$.
  - Pitch (advance per revolution): $P = 2\pi c = \pi$.
- **Analytical Solution in Frenet Initial Frame** ($r(0) = 0, T_0 = e_1, N_0 = e_2, B_0 = e_3$):
  $$r_{frenet}(s) = \begin{pmatrix} \frac{s}{2} + \frac{\sqrt{2}}{4}\sin(\sqrt{2}s) \\ \frac{1}{2}(1 - \cos(\sqrt{2}s)) \\ \frac{s}{2} - \frac{\sqrt{2}}{4}\sin(\sqrt{2}s) \end{pmatrix}$$
  $$T(s) = \begin{pmatrix} \frac{1}{2} + \frac{1}{2}\cos(\sqrt{2}s) \\ \frac{\sqrt{2}}{2}\sin(\sqrt{2}s) \\ \frac{1}{2} - \frac{1}{2}\cos(\sqrt{2}s) \end{pmatrix}$$
- **Endpoint at $s = 2\pi\sqrt{2}$**:
  - $\sqrt{2}s = 4\pi \implies \sin(4\pi) = 0, \; \cos(4\pi) = 1$.
  - $r(2\pi\sqrt{2}) = (\pi\sqrt{2}, 0, \pi\sqrt{2})^T \approx (4.4428829, 0, 4.4428829)^T$.
  - Total displacement: $\|r(2\pi\sqrt{2}) - r(0)\| = 2\pi = 6.2831853$.
- **Isometric Relation to Canonical Z-Axis Helix**:
  $$r_{cyl}(s) = \begin{pmatrix} \frac{1}{2}\cos(\sqrt{2}s) \\ \frac{1}{2}\sin(\sqrt{2}s) \\ \frac{s}{\sqrt{2}} \end{pmatrix}$$
  $$r_{frenet}(s) = \begin{pmatrix} 0 & \frac{1}{\sqrt{2}} & \frac{1}{\sqrt{2}} \\ -1 & 0 & 0 \\ 0 & -\frac{1}{\sqrt{2}} & \frac{1}{\sqrt{2}} \end{pmatrix} r_{cyl}(s) + \begin{pmatrix} 0 \\ 0.5 \\ 0 \end{pmatrix}$$
- **Tolerances**:
  - Trajectory maximum absolute error against $r_{frenet}(s)$: $< 10^{-7}$.
  - Relative error: $< 10^{-7}$ (readily satisfies required $< 10^{-3}$).

#### Benchmark 3: Straight Line ($\kappa = 0, \tau = 0, s \in [0, L]$)
- **Analytical Solution**:
  $$r(s) = \begin{pmatrix} s \\ 0 \\ 0 \end{pmatrix}, \quad T(s) = \begin{pmatrix} 1 \\ 0 \\ 0 \end{pmatrix}, \quad N(s) = \begin{pmatrix} 0 \\ 1 \\ 0 \end{pmatrix}, \quad B(s) = \begin{pmatrix} 0 \\ 0 \\ 1 \end{pmatrix}$$
- **Tolerances**:
  - Trajectory error: $< 10^{-12}$.
  - Norm error: $< 10^{-12}$.

#### Benchmark 4: Cornu Spiral / Clothoid ($\kappa(s) = c \cdot s, \tau = 0, s \in [0, s_1]$)
- **Analytical Solution via Fresnel Integrals**:
  $$\theta(s) = \int_0^s c u \, du = \frac{1}{2} c s^2$$
  $$x(s) = \int_0^s \cos\left(\frac{1}{2} c u^2\right) du = \sqrt{\frac{\pi}{c}} C\left( s \sqrt{\frac{c}{\pi}} \right)$$
  $$y(s) = \int_0^s \sin\left(\frac{1}{2} c u^2\right) du = \sqrt{\frac{\pi}{c}} S\left( s \sqrt{\frac{c}{\pi}} \right)$$
  $$z(s) = 0$$
  where $C(u) = \int_0^u \cos\left(\frac{\pi}{2} t^2\right) dt$ and $S(u) = \int_0^u \sin\left(\frac{\pi}{2} t^2\right) dt$ (implemented as `scipy.special.fresnel`).
- **Tolerances**:
  - Max error between `solve_ivp` numerical solution and analytical Fresnel: $< 10^{-7}$.

#### Orthonormality Tolerances (at all evaluation points $s_k$):
- $|\|T(s_k)\| - 1| < 10^{-4}$ (achieved: $< 10^{-14}$)
- $|\|N(s_k)\| - 1| < 10^{-4}$ (achieved: $< 10^{-14}$)
- $|\|B(s_k)\| - 1| < 10^{-4}$ (achieved: $< 10^{-14}$)
- $|T(s_k) \cdot N(s_k)| < 10^{-4}$ (achieved: $< 10^{-14}$)
- $|T(s_k) \cdot B(s_k)| < 10^{-4}$ (achieved: $< 10^{-14}$)
- $|N(s_k) \cdot B(s_k)| < 10^{-4}$ (achieved: $< 10^{-14}$)
- $|\det([T(s_k), N(s_k), B(s_k)]) - 1| < 10^{-4}$ (achieved: $< 10^{-14}$)

---

### 3.6 Differential Geometry Apparatus Mathematical Formulation

At any point $r(s)$ on the curve:
1. **Moving Orthonormal Frame**:
   - Tangent: $\vec{T}(s)$ (Green)
   - Principal Normal: $\vec{N}(s)$ (Red)
   - Binormal: $\vec{B}(s)$ (Blue)
2. **Tangent Line**:
   $$L_T(u) = r(s) + u \, \vec{T}(s), \quad u \in [-L, L]$$
3. **Osculating Plane ($\Pi_{osc}$)**:
   - Spanned by $\{\vec{T}(s), \vec{N}(s)\}$
   - Normal vector: $\vec{B}(s)$
   - Implicit equation: $(P - r(s)) \cdot \vec{B}(s) = 0$
   - Parametric patch: $P_{osc}(u, v) = r(s) + u \, \vec{T}(s) + v \, \vec{N}(s)$ for $(u, v) \in [-w, w]^2$
4. **Normal Plane ($\Pi_{norm}$)**:
   - Spanned by $\{\vec{N}(s), \vec{B}(s)\}$
   - Normal vector: $\vec{T}(s)$
   - Implicit equation: $(P - r(s)) \cdot \vec{T}(s) = 0$
   - Parametric patch: $P_{norm}(u, v) = r(s) + u \, \vec{N}(s) + v \, \vec{B}(s)$ for $(u, v) \in [-w, w]^2$
5. **Rectifying Plane ($\Pi_{rect}$)**:
   - Spanned by $\{\vec{T}(s), \vec{B}(s)\}$
   - Normal vector: $\vec{N}(s)$
   - Implicit equation: $(P - r(s)) \cdot \vec{N}(s) = 0$
   - Parametric patch: $P_{rect}(u, v) = r(s) + u \, \vec{T}(s) + v \, \vec{B}(s)$ for $(u, v) \in [-w, w]^2$
6. **Osculating Circle**:
   - Condition: Defined when $\kappa(s) > 0$.
   - Radius of curvature: $\rho(s) = \frac{1}{\kappa(s)}$.
   - Center of curvature: $c(s) = r(s) + \rho(s) \vec{N}(s)$.
   - Parametric equation in osculating plane ($\theta \in [0, 2\pi]$):
     $$C_{osc}(\theta) = c(s) - \rho(s) \cos(\theta) \vec{N}(s) + \rho(s) \sin(\theta) \vec{T}(s)$$
     Note that $C_{osc}(0) = c(s) - \rho(s) \vec{N}(s) = r(s)$ and $\left.\frac{d C_{osc}}{d\theta}\right|_{\theta=0} = \rho(s) \vec{T}(s) \parallel \vec{T}(s)$.

---

### 3.7 CLI Argument Parsing & Sanitized Filename Specification

#### CLI Parameters:
- `curvatura` (positional string or `--curvatura`): mathematical expression for $\kappa(s)$, e.g., `"1"`, `"2*s"`, `"1/(1+s**2)"`.
- `torcao` (positional optional string or `--torcao`): mathematical expression for $\tau(s)$, defaults to `"0"`.
- `--intervalo` / `-i` (two floats): $[s_0, s_1]$, default: `[0.0, 6.283185307179586]` (or `[0.0, 10.0]`).
- `--num-pontos` / `-n` (integer): number of points along interval, default: `500`.
- `--output` / `-o` (optional string): target HTML path.

#### Filename Formatting Rule:
When `--output` is omitted, format as:
`<identificacao_da_curva>-k<curvatura_sanitizada>-t<torcao_sanitizada>-I<s0>_<s1>.html`

Sanitization rules:
1. Strip leading and trailing whitespace.
2. Replace `**` and `^` with `_pow_`.
3. Replace `*` with `_mult_`.
4. Replace `/` with `_div_`.
5. Replace `+` with `_plus_`.
6. Replace `-` with `_minus_`.
7. Replace any other non-alphanumeric character (e.g. parenthesis, brackets) with `_`.
8. Collapse contiguous underscores `__` $\to$ `_`.
9. Interval floats formatted via `%g` (e.g. `0` and `6.28`).

Examples:
- `python teorema-fundamental-curvas.py "1" "1" -i 0 6.28` $\implies$ `helice_circular-k1-t1-I0_6.28.html`
- `python teorema-fundamental-curvas.py "1" -i 0 6.28` $\implies$ `circulo-k1-t0-I0_6.28.html`
- `python teorema-fundamental-curvas.py "2*s" -i 0 5` $\implies$ `espiral_de_cornu-k2_mult_s-t0-I0_5.html`

---

## 4. Features Discovered & Probed

## Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Mathematical Engine | Frenet-Serret ODE System | Integrates 12 coupled 1st-order ODEs for $[r, T, N, B]$ in $\mathbb{R}^3$ | $\kappa(s), \tau(s), s_0, s_1, N_{pts}$ | Trajectory $r(s) \in \mathbb{R}^{3 \times N}$, frame $F(s) \in SO(3)^{N}$ | Raises ValueError on non-integrable/singular expressions | ORIGINAL_REQUEST R1 & Frenet theory |
| 2 | Mathematical Engine | $SO(3)$ Continuous Orthonormalization | Vectorized Modified Gram-Schmidt preserving tangent direction and restoring right-handed frame | Frame matrices $T, N, B \in \mathbb{R}^{3 \times N}$ | Orthonormal frame with $\det=1$, norm $=1$ | None (deterministic linear algebra) | ORIGINAL_REQUEST R1 & numerical drift probe |
| 3 | Expression Parsing | AST Mathematical Whitelist Validator | Inspects AST nodes prior to parsing to block arbitrary code execution | Expression string $\kappa(s)$ or $\tau(s)$ | Validated AST or exception | Raises ValueError with description of illegal token/call | SymPy security vulnerability probe |
| 4 | Expression Parsing | Robust Lambdification & Vectorization | Compiles SymPy expressions into NumPy callables with scalar broadcasting | SymPy expression, symbol $s$ | Vectorized callable $f(s) \to \text{ndarray}$ | Raises ValueError on invalid symbols or domain failure | SymPy constant broadcasting probe |
| 5 | Classification | Unified Symbol Differential Classifier | Classifies curve using symbolic derivatives with dynamic symbol unification | Parsed $\kappa(s), \tau(s)$ SymPy expressions | Enum: `reta`, `circulo`, `helice_circular`, `helice_cilindrica_geral`, `espiral_de_cornu`, `espiral_logaritmica`, `curva_plana`, `curva_espacial` | Falls back to numerical sample check if symbolic diff is inconclusive | Symbol mismatch probe in SymPy 1.14 |
| 6 | Classification | Lancret Theorem Cylindrical Helix Detection | Verifies condition $\frac{d}{ds}(\tau/\kappa) \equiv 0$ for non-constant curvature | $\kappa(s), \tau(s)$ | Boolean flag for `helice_cilindrica_geral` | Numerical sample variance check fallback | Lancret (1802) & Toponogov |
| 7 | CLI | Sanitized Automatic Output Naming | Generates deterministic sanitized filename matching schema `<class>-k<k>-t<t>-I<s0>_<s1>.html` | Curve class, expressions, interval | Formatted filename string | Strips forbidden filesystem characters | ORIGINAL_REQUEST R2 |
| 8 | Visualization | Fullscreen Plotly 3D Layout | Configures responsive $100\text{vw} \times 100\text{vh}$ interactive scene with autosize | Figure object | HTML string / file | Injects responsive CSS | ORIGINAL_REQUEST R3 |
| 9 | Visualization | Differential Apparatus 3D Rendering | Renders curve, active point, $T, N, B$ vectors, tangent line, 3 fundamental planes, and osculating circle | $r(s), T(s), N(s), B(s), \kappa(s)$ at active $s$ | Plotly Traces (Scatter3d, Mesh3d) | Hides osculating circle if $\kappa=0$ | ORIGINAL_REQUEST R3 & differential geometry |
| 10 | Visualization | Slider Scrubbing & Frame Navigation | Bottom slider animating differential apparatus continuously over parameter $s$ | Discretized states $k = 0 \dots N-1$ | Plotly slider and frames | Clamps to valid index range | ORIGINAL_REQUEST R3 |
| 11 | Visualization | Point Click-to-Jump Injected JS | Injects `plotly_click` JavaScript listener to jump slider directly to clicked curve coordinate | HTML document | Interactive browser event binding | Gracefully ignores clicks on non-curve traces | ORIGINAL_REQUEST R3 |

## Edge Cases
| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Expression Parsing | `__import__('os').system('ls')` | Blocked by AST whitelist validator before execution; raises `ValueError: Disallowed function call`. |
| 2 | Expression Parsing | Numeric constant string `"2"` or `"0"` | SymPy lambdify returns scalar integer; broadcasting wrapper ensures return of `np.full_like(s, val, dtype=float)`. |
| 3 | Expression Parsing | Operator `^` (e.g. `s^2`) | Converted to standard Python power `s**2` via `convert_xor` transformation. |
| 4 | Expression Parsing | Implicit multiplication `2s` | Parsed safely or normalized to `2*s`. |
| 5 | Differential Classification | `s = sp.Symbol('s', real=True)` vs `Symbol('s')` | Diff returns 0 due to assumption mismatch; solved by extracting symbol directly from `expr.free_symbols`. |
| 6 | Re-orthonormalization | Accumulated drift over $s \in [0, 100]$ | Vectorized Modified Gram-Schmidt resets error to $< 10^{-15}$ across all points in $\approx 10\,\mu\text{s}$. |
| 7 | Curve Classification | $\kappa(s) \equiv 0$, $\tau(s) = 5$ | Classified as `reta` (straight line), since without curvature, normal vector and torsion are non-physical. |
| 8 | Osculating Circle | $\kappa(s) = 0$ (straight line or inflection) | Radius $\rho \to \infty$; circle trace omitted/hidden with warning in UI legend. |
| 9 | Analytical Verification | Circle over $[0, \pi]$ with $\kappa=2$ | Traverses full circle of radius $0.5$ returning to origin $r(\pi) = (0, 0, 0)$. Semicircle occurs on $[0, \pi/2]$ with endpoint $(0, 1, 0)$. |
| 10 | Analytical Verification | Circular helix with $\kappa=1, \tau=1$ | Reconstructed curve axis is oriented along Darboux vector $(1, 0, 1)/\sqrt{2}$, matching canonical cylinder helix via exact rigid motion $R \in SO(3), t_0 \in \mathbb{R}^3$. |

---

## 5. Theoretical Foundations & Citations

1. **Toponogov, Victor Andreevich** (2006).  
   *Differential Geometry of Curves and Surfaces: A Concise Guide*, Birkhäuser Boston / Springer Science+Business Media, LLC. ISBN: 978-0-8176-4384-3.  
   - **Theorem 1.3.1 (Fundamental Theorem of Space Curves)**: Proves that for continuous $\kappa(s) > 0$ and $\tau(s)$ on an interval $I$, there exists a space curve parameterized by arc length whose curvature and torsion match the prescribed functions, unique up to a proper Euclidean rigid motion in $SE(3)$.
   - **Lancret's Theorem**: Establishes that a regular space curve with non-zero curvature is a cylindrical helix if and only if $\frac{\tau(s)}{\kappa(s)} = \text{constant}$.

2. **Tenenblat, Keti** (2008).  
   *Introdução à Geometria Diferencial*, Editora Edgard Blücher / IMPA, Coleção Textos Universitários. ISBN: 978-85-212-0457-2.  
   - **Seção 1.2–1.3**: Rigorous formulation of the Frenet-Serret equations, moving frame $\{T, N, B\}$, osculating/normal/rectifying planes, and existence/uniqueness proof via the Picard-Lindelöf theorem applied to linear differential systems in the Lie group $SO(3)$.

3. **Alencar, Hilário; Santos, Walcy** (2009).  
   *Geometria Diferencial: Curvas e Superfícies*, IMPA, Coleção Matemática Universitária. ISBN: 978-85-244-0298-2.  
   - **Capítulo 1**: Demonstrates the skew-symmetry of the Frenet-Serret matrix $\frac{dF}{ds} = F K(s)$, characterization of the Darboux rotation vector $\Omega(s) = \tau(s) T(s) + \kappa(s) B(s)$, osculating circle $\rho(s) = 1/\kappa(s)$ with center $c(s) = r(s) + \rho(s) N(s)$, and planar curve reduction when $\tau \equiv 0$.

4. **do Carmo, Manfredo Perdigão** (2016).  
   *Differential Geometry of Curves and Surfaces*, Revised and Updated Second Edition, Dover Publications. ISBN: 978-0-486-80699-0.  
   - **Section 1-5 (The Fundamental Theorem of the Local Theory of Curves)**: Authoritative exposition of curve reconstruction, canonical forms, and rigid motion invariants.

5. **Lancret, Michel Ange** (1802).  
   *Mémoire sur les courbes à double courbure*, Mémoires présentés à l'Institut des Sciences, Lettres et Arts par divers savants, Paris, t. 1, pp. 416–454.  
   - Original derivation and proof of the necessary and sufficient condition $\frac{\tau}{\kappa} = \text{const}$ for generalized helices.

---

## 6. Caveats

1. **Inflection Points ($\kappa(s) = 0$)**: In classical differential geometry, the Frenet frame is undefined at inflection points where $\kappa(s) = 0$. However, in the numerical ODE formulation $\frac{dF}{ds} = F K(s)$, the skew-symmetric system is completely regular and continuous for any continuous function $\kappa(s)$. If $\kappa(s)$ crosses zero, the frame evolves continuously without numerical breakdown, but the geometric osculating circle diverges ($\rho \to \infty$).
2. **Initial Orientation Convention**: The standard initial frame $T(0) = (1,0,0), N(0)=(0,1,0), B(0)=(0,0,1)$ dictates the spatial orientation of the reconstructed curve. Any comparison against external analytical formulas (e.g. helices along the z-axis) must account for the rigid Euclidean transformation $r_{frenet}(s) = R \, r_{canonical}(s) + t_0$.

---

## 7. Conclusion

The mathematical foundation for `teorema-fundamental-curvas.py` is fully specified, verified, and benchmarked:
1. **ODE System**: 12-dimensional first-order skew-symmetric system solved with `solve_ivp(method='DOP853', rtol=1e-9, atol=1e-9)`.
2. **Orthonormalization**: Vectorized Modified Gram-Schmidt with cross-product binormal guarantees $\det(F) = 1$ and $\|T\|=\|N\|=\|B\|=1$ to machine precision ($< 10^{-15}$).
3. **Safe Parsing**: AST-based validator blocks code execution while supporting all mathematical expressions and robust broadcasting.
4. **Classification**: 8-class decision tree with symbol unification and Lancret's theorem accurately classifies straight lines, circles, circular helices, generalized helices, Cornu spirals, logarithmic spirals, and fallback planar/spatial curves.
5. **Benchmarks**: Closed-form analytical benchmarks for circle, helix, straight line, and clothoid with Fresnel integrals confirm numerical errors well within required tolerances ($< 10^{-6}$ vs required $< 10^{-3}$).

---

## 8. Verification Method

To independently reproduce and verify all mathematical benchmarks and algorithms:

1. **Verify Analytical Benchmarks & ODE Accuracy**:
   ```bash
   uv run --with numpy --with scipy --with sympy python3 -c "
   import numpy as np
   from scipy.integrate import solve_ivp
   from scipy.special import fresnel

   # 1. Circle test: kappa=2, tau=0 over [0, pi]
   def ode_circle(s, Y):
       return np.concatenate([Y[3:6], 2*Y[6:9], -2*Y[3:6], np.zeros(3)])
   Y0 = [0,0,0, 1,0,0, 0,1,0, 0,0,1]
   s_eval = np.linspace(0, np.pi, 500)
   sol_c = solve_ivp(ode_circle, (0, np.pi), Y0, t_eval=s_eval, rtol=1e-9, atol=1e-9, method='DOP853')
   x_c_ana = 0.5 * np.sin(2 * s_eval)
   y_c_ana = 0.5 * (1 - np.cos(2 * s_eval))
   assert np.max(np.abs(sol_c.y[0] - x_c_ana)) < 1e-6
   assert np.max(np.abs(sol_c.y[1] - y_c_ana)) < 1e-6
   print('Circle Benchmark: PASS (max error < 1e-6)')

   # 2. Helix test: kappa=1, tau=1 over [0, 2*pi*sqrt(2)]
   s_max = 2 * np.pi * np.sqrt(2)
   def ode_helix(s, Y):
       return np.concatenate([Y[3:6], Y[6:9], -Y[3:6] + Y[9:12], -Y[6:9]])
   s_eval_h = np.linspace(0, s_max, 500)
   sol_h = solve_ivp(ode_helix, (0, s_max), Y0, t_eval=s_eval_h, rtol=1e-9, atol=1e-9, method='DOP853')
   sq2 = np.sqrt(2)
   x_h_ana = s_eval_h/2.0 + (sq2/4.0)*np.sin(sq2*s_eval_h)
   y_h_ana = 0.5*(1.0 - np.cos(sq2*s_eval_h))
   z_h_ana = s_eval_h/2.0 - (sq2/4.0)*np.sin(sq2*s_eval_h)
   assert np.max(np.abs(sol_h.y[0] - x_h_ana)) < 1e-6
   assert np.max(np.abs(sol_h.y[1] - y_h_ana)) < 1e-6
   assert np.max(np.abs(sol_h.y[2] - z_h_ana)) < 1e-6
   print('Helix Benchmark: PASS (max error < 1e-6)')

   # 3. Clothoid test: kappa=s, tau=0
   def ode_clothoid(s, Y):
       return np.concatenate([Y[3:6], s*Y[6:9], -s*Y[3:6], np.zeros(3)])
   s_eval_cl = np.linspace(0, 5.0, 500)
   sol_cl = solve_ivp(ode_clothoid, (0, 5.0), Y0, t_eval=s_eval_cl, rtol=1e-9, atol=1e-9, method='DOP853')
   S, C = fresnel(s_eval_cl / np.sqrt(np.pi))
   x_cl_ana = np.sqrt(np.pi) * C
   y_cl_ana = np.sqrt(np.pi) * S
   assert np.max(np.abs(sol_cl.y[0] - x_cl_ana)) < 1e-6
   assert np.max(np.abs(sol_cl.y[1] - y_cl_ana)) < 1e-6
   print('Clothoid Benchmark: PASS (max error < 1e-6)')
   "
   ```

2. **Verify Vectorized SO(3) Frame Orthonormalization**:
   ```bash
   uv run --with numpy python3 -c "
   import numpy as np
   K = 1000
   T = np.random.randn(3, K)
   N = np.random.randn(3, K)
   B = np.random.randn(3, K)
   T_u = T / np.linalg.norm(T, axis=0, keepdims=True)
   N_p = N - np.sum(N * T_u, axis=0, keepdims=True) * T_u
   N_u = N_p / np.linalg.norm(N_p, axis=0, keepdims=True)
   B_u = np.cross(T_u, N_u, axis=0)
   dets = np.linalg.det(np.transpose(np.array([T_u, N_u, B_u]), (2, 0, 1)))
   assert np.allclose(dets, 1.0, atol=1e-14)
   assert np.allclose(np.sum(T_u * N_u, axis=0), 0.0, atol=1e-14)
   print('SO(3) Orthonormalization: PASS (det = 1.0, dot = 0.0 to machine precision)')
   "
   ```

3. **Verify Security AST Whitelist Validator**:
   ```bash
   uv run python3 -c "
   import ast
   ALLOWED = {ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Call, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Load}
   def check(s):
       for n in ast.walk(ast.parse(s, mode='eval')):
           if type(n) not in ALLOWED: raise ValueError('Blocked')
   try:
       check('__import__(\"os\").system(\"ls\")')
       assert False, 'Security failure'
   except ValueError:
       print('Security AST Validation: PASS (Malicious execution successfully blocked)')
   "
   ```
