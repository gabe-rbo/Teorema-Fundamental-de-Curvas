# Task Assignment: Milestone M1 (Math Engine & Classification Worker)

You are an agent with archetype `teamwork_preview_worker`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m1_1`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Original user request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
Project master specification: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md`
Detailed mathematical survey to implement: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_1/handoff.md`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Write Ownership
You EXCLUSIVELY own and write:
- `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_engine.py`
Do NOT modify other implementation files or tests.

## Instructions & Scope
1. Read `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md` and `PROJECT.md`.
2. Study the mathematical specifications and code recipes in `teamwork_preview_spec_miner_survey_1/handoff.md`.
3. Implement `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_engine.py` strictly conforming to the interface contract in `PROJECT.md § Interface Contracts`:
   - **AST-based whitelist validator**: `parse_and_validate_expression(expr_str: str) -> sp.Expr`. Validates that expressions contain only allowed arithmetic, power, trigonometric/exponential functions, and parameter `s` (or constants `pi`, `e`). Blocks any dangerous calls or unapproved AST nodes.
   - **Evaluator compiler with broadcasting**: `create_evaluator(expr: sp.Expr) -> Callable`. Lambdifies SymPy expression to NumPy and ensures constants return `np.full_like(s, val)`.
   - **Domain & Positivity validation**: Verifies $\kappa(s) \ge 0$ (or raises clear ValueError) and checks for non-finite values (singularities).
   - **Frenet-Serret ODE State & Integration**:
     `reconstruct_curve(kappa_expr_str, tau_expr_str="0", s0=0.0, s1=6.28, num_points=500) -> CurveResult`.
     Integrates 12 coupled 1st-order ODEs using `scipy.integrate.solve_ivp(..., method='DOP853', rtol=1e-9, atol=1e-9)` (with fallback to `RK45` if DOP853 is not available).
     Initial condition: $r(s_0) = (0, 0, 0)$, $T(s_0) = (1, 0, 0)$, $N(s_0) = (0, 1, 0)$, $B(s_0) = (0, 0, 1)$.
   - **Vectorized Modified Gram-Schmidt $SO(3)$ Orthonormalization**:
     Normalizes $T$, projects and normalizes $N \perp T$, and sets $B = T \times N$, guaranteeing $\det([T, N, B]) = +1$ and unit norms to machine precision.
   - **Curve Classification Engine**:
     `classify_curve(kappa_expr, tau_expr, s_vals, kappa_vals, tau_vals) -> str`.
     Deterministic classification into:
     - `reta` ($\kappa \equiv 0$)
     - `circulo` ($\kappa = \text{const} > 0, \tau \equiv 0$)
     - `helice_circular` ($\kappa = \text{const} > 0, \tau = \text{const} \ne 0$)
     - `helice_cilindrica_geral` ($\tau/\kappa = \text{const} \ne 0$, Lancret's theorem)
     - `espiral_de_cornu` ($\tau \equiv 0, \kappa(s) = c s + d$)
     - `espiral_logaritmica` ($\tau \equiv 0, 1/\kappa(s) = a s + b$)
     - `curva_plana` (fallback when $\tau \equiv 0$)
     - `curva_espacial` (fallback when $\tau \not\equiv 0$)
   - **Filename Generator & Sanitizer**:
     `sanitize_expr_for_filename(expr_str: str) -> str`
     `generate_output_filename(curve_class, kappa_str, tau_str, s0, s1) -> str`
     Produces `<identificacao_da_curva>-k<curvatura>-t<torcao>-I<InicioIntervalo_FimIntervalo>.html`.
4. Run thorough self-verification:
   - Run verification commands against analytical circle, helix, straight line, and clothoid benchmarks as documented in Spec Miner 1 handoff.
   - Verify orthonormality tolerances: $|\|T\|-1| < 10^{-4}, |T \cdot N| < 10^{-4}, |\det - 1| < 10^{-4}$.
   - Document verification commands and results in your handoff.
5. Write your handoff report to `handoff.md` in your working directory and notify the orchestrator via `send_message`.

## 2026-09-30T14:52:24Z
From: 0b0dffe7-95be-4cd3-9ff5-acde191dd517
Priority: MESSAGE_PRIORITY_HIGH
Content:
You are assigned to the Fundamental Theorem of Curves project.
Your assigned working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m1_1
Project root: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas
Original user request: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md
Your detailed task assignment: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m1_1/DISPATCH.md
Project specification: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md
Detailed math report to follow: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_1/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

You exclusively own:
- /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_engine.py

Implement curva_engine.py strictly per the interface contract in PROJECT.md:
- Safe AST whitelist expression parsing for kappa(s) and tau(s)
- Fast vectorized broadcasting NumPy lambdification
- Frenet-Serret ODE state integration with solve_ivp (DOP853/RK45)
- Vectorized Modified Gram-Schmidt SO(3) orthonormalization (guaranteeing det=1, norms=1 to machine precision)
- Deterministic 8-class curve classifier (including Lancret's theorem)
- Output filename generator & sanitizer
Run self-verification tests against analytical circle, helix, straight line, and clothoid benchmarks.
Write your handoff report to handoff.md in your working directory and notify the orchestrator with send_message.
