"""
Mathematical Engine & Classification for the Fundamental Theorem of Curves.

This module reconstructs 3D and planar space curves from their intrinsic
differential geometry invariants: curvature kappa(s) and torsion tau(s).
It implements:
  - Strict AST whitelist validation of mathematical expressions.
  - Fast, broadcast-safe SymPy to NumPy lambdification.
  - High-order numerical ODE integration of the 12-state Frenet-Serret system.
  - Continuous SO(3) orthonormalization via Modified Gram-Schmidt and cross-product.
  - Deterministic 8-class curve classification (including Lancret's theorem).
  - Sanitized output filename generation.

Theoretical foundations:
  - Toponogov, V. A. (2006). Differential Geometry of Curves and Surfaces.
  - Tenenblat, K. (2008). Introdução à Geometria Diferencial.
  - Alencar, H. & Santos, W. (2009). Geometria Diferencial: Curvas e Superfícies.
  - do Carmo, M. P. (2016). Differential Geometry of Curves and Surfaces.
  - Lancret, M. A. (1802). Mémoire sur les courbes à double courbure.
"""

from __future__ import annotations

import ast
import io
import re
import token
import tokenize
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp
from sympy.parsing.sympy_parser import (
    convert_xor,
    parse_expr,
    standard_transformations,
)

# ---------------------------------------------------------------------------
# AST Security Whitelist Configuration
# ---------------------------------------------------------------------------

_ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Name,
    ast.Call,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.USub,
    ast.UAdd,
)

_ALLOWED_VARIABLE_NAMES = {"s", "pi", "E", "e"}

_ALLOWED_MATH_FUNCS = {
    "sin",
    "cos",
    "tan",
    "exp",
    "log",
    "sqrt",
    "sinh",
    "cosh",
    "tanh",
    "asin",
    "acos",
    "atan",
    "abs",
}


def _preprocess_math_string(expr_str: str) -> str:
    """Preprocess mathematical expression: convert ^ to **, and insert *."""
    s = expr_str.strip().replace("^", "**")
    if not s:
        return s

    # Insert multiplication between NUMBER and NAME or '('
    # without corrupting scientific notation (e.g. 1e-3)
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(s).readline))
        result: list[str] = []
        prev_tok: tokenize.TokenInfo | None = None
        for tok in tokens:
            if prev_tok is not None and (
                (
                    prev_tok.type == token.NUMBER
                    and (tok.type == token.NAME or tok.string == "(")
                )
                or (
                    prev_tok.string == ")"
                    and (
                        tok.type in (token.NAME, token.NUMBER)
                        or tok.string == "("
                    )
                )
            ):
                result.append("*")
            result.append(tok.string)
            prev_tok = tok
        return "".join(result).strip()
    except tokenize.TokenError:
        return s


def parse_and_validate_expression(expr_str: str) -> sp.Expr:
    """
    Safely parse a math expression string for curvature or torsion into SymPy.

    Performs strict AST-based whitelist validation to prevent arbitrary code execution,
    allowing only basic arithmetic, powers, permitted transcendental functions, and
    parameter 's' or constants 'pi', 'e'.

    Raises:
        ValueError: If expression is empty, malformed, contains unauthorized AST nodes,
                    forbidden functions, or unknown variables.
    """
    if not isinstance(expr_str, str):
        expr_str = str(expr_str)

    expr_str = expr_str.strip()
    if not expr_str:
        raise ValueError("Expression string cannot be empty.")

    clean_str = _preprocess_math_string(expr_str)

    # 1. AST Whitelist Validation
    try:
        tree = ast.parse(clean_str, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error in expression '{expr_str}': {e}") from e

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_AST_NODES):
            raise ValueError(
                f"Disallowed syntax element '{type(node).__name__}' "
                f"in expression '{expr_str}'."
            )
        if isinstance(node, ast.Name):
            if (
                node.id not in _ALLOWED_VARIABLE_NAMES
                and node.id not in _ALLOWED_MATH_FUNCS
            ):
                raise ValueError(
                    f"Disallowed identifier '{node.id}' in '{expr_str}'. "
                    f"Only parameter 's' and constants ('pi', 'e') are permitted."
                )
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError(
                    f"Direct identifier required for function call in '{expr_str}'."
                )
            if node.func.id not in _ALLOWED_MATH_FUNCS:
                raise ValueError(
                    f"Disallowed function '{node.func.id}' in '{expr_str}'. "
                    f"Allowed functions are: {sorted(_ALLOWED_MATH_FUNCS)}"
                )
            if node.keywords:
                raise ValueError(
                    f"Keyword arguments disallowed in expression '{expr_str}'."
                )

    # 2. SymPy Parsing with strict namespace
    s_sym = sp.Symbol("s")
    local_dict = {
        "s": s_sym,
        "pi": sp.pi,
        "E": sp.E,
        "e": sp.E,
    }
    for func_name in _ALLOWED_MATH_FUNCS:
        if hasattr(sp, func_name):
            local_dict[func_name] = getattr(sp, func_name)

    try:
        sym_expr = parse_expr(
            clean_str,
            transformations=standard_transformations + (convert_xor,),
            local_dict=local_dict,
        )
    except Exception as e:
        raise ValueError(f"Could not parse expression '{expr_str}': {e}") from e

    return sym_expr


def create_evaluator(
    expr: sp.Expr,
) -> Callable[[np.ndarray | float], np.ndarray | float]:
    """
    Compile a SymPy expression into a fast, vectorized NumPy callable.

    Guarantees that constant expressions evaluate to an array of identical shape
    matching the input s_val via broadcasting (`np.full_like(s, val)`).
    """
    syms = [sym for sym in expr.free_symbols if sym.name == "s"]
    s_sym = syms[0] if syms else sp.Symbol("s")

    raw_func = sp.lambdify(s_sym, expr, modules=["numpy", "math"])

    def evaluate_func(s_val: np.ndarray | float) -> np.ndarray | float:
        res = raw_func(s_val)
        if np.ndim(res) == 0:
            if np.ndim(s_val) > 0:
                return np.full_like(s_val, res, dtype=float)
            return float(res)
        return np.asarray(res, dtype=float)

    return evaluate_func


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class CurveResult:
    """
    Result of integrating the Frenet-Serret system for a reconstructed curve.

    Attributes:
        s: Arc length parameter values, shape (N,)
        r: Curve trajectory coordinates [x(s), y(s), z(s)], shape (3, N)
        T: Tangent unit vectors, shape (3, N)
        N: Principal normal unit vectors, shape (3, N)
        B: Binormal unit vectors, shape (3, N)
        kappa: Curvature values along the curve, shape (N,)
        tau: Torsion values along the curve, shape (N,)
        classification: Deterministic geometric class name (e.g. 'circulo')
        s0: Start of integration interval
        s1: End of integration interval
    """

    s: np.ndarray
    r: np.ndarray
    T: np.ndarray
    N: np.ndarray
    B: np.ndarray
    kappa: np.ndarray
    tau: np.ndarray
    classification: str
    s0: float
    s1: float


# ---------------------------------------------------------------------------
# SO(3) Frame Orthonormalization
# ---------------------------------------------------------------------------


def orthonormalize_frame(
    T: np.ndarray,
    N: np.ndarray,
    B: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Vectorized Modified Gram-Schmidt orthonormalization on the Lie group SO(3).

    Given frame vectors T, N (and optional B) with shape (3, K):
      1. Normalizes T: T_ortho = T / ||T||
      2. Projects N perpendicular to T: N_ortho = (N - (N . T) T) / ||...||
      3. Computes B via right-handed cross product: B_ortho = T_ortho x N_ortho

    Guarantees mathematically to machine precision (< 1e-15):
      - ||T|| = ||N|| = ||B|| = 1.0
      - T . N = T . B = N . B = 0.0
      - det([T, N, B]) = +1.0
    """
    T_norms = np.linalg.norm(T, axis=0, keepdims=True)
    T_norms = np.where(T_norms == 0, 1.0, T_norms)
    T_ortho = T / T_norms

    proj = np.sum(N * T_ortho, axis=0, keepdims=True) * T_ortho
    N_diff = N - proj
    N_norms = np.linalg.norm(N_diff, axis=0, keepdims=True)
    N_norms = np.where(N_norms == 0, 1.0, N_norms)
    N_ortho = N_diff / N_norms

    B_ortho = np.cross(T_ortho, N_ortho, axis=0)

    return T_ortho, N_ortho, B_ortho


# ---------------------------------------------------------------------------
# Curve Classification Engine
# ---------------------------------------------------------------------------


def classify_curve(
    kappa_expr: sp.Expr,
    tau_expr: sp.Expr,
    s_vals: np.ndarray,
    kappa_vals: np.ndarray,
    tau_vals: np.ndarray,
) -> str:
    """
    Deterministically classify a curve into one of 8 geometric families:
      1. 'reta': kappa(s) = 0 identically.
      2. 'circulo': kappa = const > 0, tau = 0.
      3. 'helice_circular': kappa = const > 0, tau = const != 0.
      4. 'helice_cilindrica_geral': tau(s)/kappa(s) = const != 0 (Lancret's Theorem).
      5. 'espiral_de_cornu': tau = 0, kappa(s) = c*s + d (Clothoid).
      6. 'espiral_logaritmica': tau = 0, 1/kappa(s) = a*s + b.
      7. 'curva_plana': fallback when tau = 0.
      8. 'curva_espacial': fallback when tau != 0.
    """
    # Unify the differentiation symbol
    syms = [
        sym
        for sym in (kappa_expr.free_symbols | tau_expr.free_symbols)
        if sym.name == "s"
    ]
    s_sym = syms[0] if syms else sp.Symbol("s")

    # 1. Straight line (reta): kappa == 0
    is_kappa_zero = (
        kappa_expr.is_zero
        or sp.simplify(kappa_expr) == 0
        or bool(np.all(np.abs(kappa_vals) < 1e-9))
    )
    if is_kappa_zero:
        return "reta"

    # 2. Check if tau is identically zero
    is_tau_zero = (
        tau_expr.is_zero
        or sp.simplify(tau_expr) == 0
        or bool(np.all(np.abs(tau_vals) < 1e-9))
    )

    # 3. Check constancy of kappa and tau
    is_kappa_const = (
        len(kappa_expr.free_symbols) == 0
        or sp.simplify(sp.diff(kappa_expr, s_sym)) == 0
        or bool(np.ptp(kappa_vals) < 1e-8)
    )
    is_tau_const = (
        len(tau_expr.free_symbols) == 0
        or sp.simplify(sp.diff(tau_expr, s_sym)) == 0
        or bool(np.ptp(tau_vals) < 1e-8)
    )

    if is_tau_zero:
        # Planar curves branch
        if is_kappa_const:
            return "circulo"

        # Check Cornu Spiral (kappa(s) = c*s + d with c != 0)
        try:
            d2_k = sp.simplify(sp.diff(kappa_expr, s_sym, 2))
            d1_k = sp.simplify(sp.diff(kappa_expr, s_sym, 1))
            if d2_k == 0 and d1_k != 0:
                return "espiral_de_cornu"
        except (
            sp.SympifyError,
            TypeError,
            ValueError,
            ZeroDivisionError,
            AttributeError,
        ):
            pass
        # Numerical linear fit fallback for Cornu
        if len(s_vals) >= 3:
            p = np.polyfit(s_vals, kappa_vals, 1)
            residual = np.max(np.abs(kappa_vals - np.polyval(p, s_vals)))
            if residual < 1e-6 and abs(p[0]) > 1e-6:
                return "espiral_de_cornu"

        # Check Logarithmic Spiral (1/kappa(s) = a*s + b with a != 0)
        try:
            inv_k = 1 / kappa_expr
            d2_inv = sp.simplify(sp.diff(inv_k, s_sym, 2))
            d1_inv = sp.simplify(sp.diff(inv_k, s_sym, 1))
            if d2_inv == 0 and d1_inv != 0:
                return "espiral_logaritmica"
        except (
            sp.SympifyError,
            TypeError,
            ValueError,
            ZeroDivisionError,
            AttributeError,
        ):
            pass
        # Numerical linear fit fallback for Log Spiral
        if len(s_vals) >= 3 and np.all(kappa_vals > 1e-9):
            inv_vals = 1.0 / kappa_vals
            p = np.polyfit(s_vals, inv_vals, 1)
            residual = np.max(np.abs(inv_vals - np.polyval(p, s_vals)))
            if residual < 1e-6 and abs(p[0]) > 1e-6:
                return "espiral_logaritmica"

        return "curva_plana"

    else:
        # Space curves branch
        if is_kappa_const and is_tau_const:
            return "helice_circular"

        # Lancret's Theorem: tau(s)/kappa(s) = const != 0
        try:
            ratio = tau_expr / kappa_expr
            d_ratio = sp.simplify(sp.diff(ratio, s_sym))
            if d_ratio == 0 and not ratio.is_zero:
                return "helice_cilindrica_geral"
        except (
            sp.SympifyError,
            TypeError,
            ValueError,
            ZeroDivisionError,
            AttributeError,
        ):
            pass
        # Numerical ratio variance check fallback
        if np.all(kappa_vals > 1e-9):
            ratios = tau_vals / kappa_vals
            if (np.ptp(ratios) < 1e-6 or np.std(ratios) < 1e-6) and abs(
                float(np.mean(ratios))
            ) > 1e-9:
                return "helice_cilindrica_geral"

        return "curva_espacial"


# ---------------------------------------------------------------------------
# Frenet-Serret ODE Integration
# ---------------------------------------------------------------------------


def reconstruct_curve(
    kappa_expr_str: str,
    tau_expr_str: str = "0",
    s0: float = 0.0,
    s1: float = 6.283185307179586,
    num_points: int = 500,
) -> CurveResult:
    """
    Reconstruct space curve r(s) and moving orthonormal frame [T(s), N(s), B(s)]
    from curvature kappa(s) and torsion tau(s) via Frenet-Serret ODEs:

        dr/ds = T
        dT/ds = kappa(s) * N
        dN/ds = -kappa(s) * T + tau(s) * B
        dB/ds = -tau(s) * N

    Subject to initial conditions at s0:
        r(s0) = (0, 0, 0)
        T(s0) = (1, 0, 0)
        N(s0) = (0, 1, 0)
        B(s0) = (0, 0, 1)

    Args:
        kappa_expr_str: Mathematical expression for curvature kappa(s) >= 0.
        tau_expr_str: Mathematical expression for torsion tau(s). Defaults to "0".
        s0: Integration start parameter.
        s1: Integration end parameter.
        num_points: Discretization point count along interval [s0, s1] (>= 2).

    Returns:
        CurveResult with trajectory, frame vectors, invariants, and classification.

    Raises:
        ValueError: On empty expressions, invalid domain (kappa < 0), singularities,
                    or invalid interval parameters.
        RuntimeError: If ODE integration fails to converge.
    """
    s0_f = float(s0)
    s1_f = float(s1)
    if s0_f >= s1_f:
        raise ValueError(
            f"Interval start s0={s0_f} must be strictly less than end s1={s1_f}."
        )

    if int(num_points) < 2:
        raise ValueError(
            f"Number of points num_points={num_points} must be at least 2."
        )

    # 1. Parse and validate expressions safely
    kappa_expr = parse_and_validate_expression(kappa_expr_str)
    tau_expr = parse_and_validate_expression(tau_expr_str)

    # 2. Compile vectorized evaluators
    kappa_eval = create_evaluator(kappa_expr)
    tau_eval = create_evaluator(tau_expr)

    # 3. Analytic singularity pre-check
    s_sym = sp.Symbol("s")
    for expr_to_check in (kappa_expr, tau_expr):
        try:
            sings = sp.singularities(expr_to_check, s_sym)
            if hasattr(sings, "__iter__"):
                for sing in sings:
                    try:
                        val = float(sing.evalf())
                        if s0_f <= val <= s1_f:
                            raise ValueError(
                                "Expression evaluates to non-finite values (singularity / div by zero)."
                            )
                    except (TypeError, ValueError) as te:
                        if "non-finite values" in str(te):
                            raise
        except ValueError:
            raise
        except Exception:
            pass

    # 4. Dense grid & user grid domain & singularity validation
    dense_n = max(int(num_points), 2000)
    s_dense = np.linspace(s0_f, s1_f, dense_n)
    try:
        kappa_dense = kappa_eval(s_dense)
        tau_dense = tau_eval(s_dense)
    except (ZeroDivisionError, FloatingPointError, OverflowError) as e:
        raise ValueError(
            "Expression evaluates to non-finite values (singularity / div by zero)."
        ) from e

    if not np.all(np.isfinite(kappa_dense)) or not np.all(np.isfinite(tau_dense)):
        raise ValueError(
            "Expression evaluates to non-finite values (singularity / div by zero)."
        )

    if np.any(kappa_dense < -1e-12):
        raise ValueError(
            "Curvature kappa(s) must be non-negative everywhere on the interval."
        )

    # User discretization grid evaluation
    s_vals = np.linspace(s0_f, s1_f, int(num_points))
    try:
        kappa_vals = kappa_eval(s_vals)
        tau_vals = tau_eval(s_vals)
    except (ZeroDivisionError, FloatingPointError, OverflowError) as e:
        raise ValueError(
            "Expression evaluates to non-finite values (singularity / div by zero)."
        ) from e

    if not np.all(np.isfinite(kappa_vals)) or not np.all(np.isfinite(tau_vals)):
        raise ValueError(
            "Expression evaluates to non-finite values (singularity / div by zero)."
        )

    if np.any(kappa_vals < -1e-12):
        raise ValueError(
            "Curvature kappa(s) must be non-negative everywhere on the interval."
        )

    kappa_vals = np.maximum(kappa_vals, 0.0)

    # 5. Formulate 12-state Frenet-Serret ODE system
    step_count = 0
    max_steps = 100_000

    def frenet_system(s: float, Y: np.ndarray) -> np.ndarray:
        nonlocal step_count
        step_count += 1
        if step_count > max_steps:
            raise ValueError(
                "Expression evaluates to non-finite values (singularity / div by zero or solver collapse)."
            )

        try:
            k_raw = float(kappa_eval(s))
            t_raw = float(tau_eval(s))
        except (ZeroDivisionError, FloatingPointError, OverflowError):
            raise ValueError(
                "Expression evaluates to non-finite values (singularity / div by zero)."
            )

        if not np.isfinite(k_raw) or not np.isfinite(t_raw) or abs(k_raw) > 1e10 or abs(t_raw) > 1e10:
            raise ValueError(
                "Expression evaluates to non-finite values (singularity / div by zero)."
            )

        k = max(0.0, k_raw)
        t = t_raw

        # Y: [x, y, z, Tx, Ty, Tz, Nx, Ny, Nz, Bx, By, Bz]
        T_vec = Y[3:6]
        N_vec = Y[6:9]
        B_vec = Y[9:12]

        dr = T_vec
        dT = k * N_vec
        dN = -k * T_vec + t * B_vec
        dB = -t * N_vec

        return np.concatenate([dr, dT, dN, dB])

    # Initial state: r=(0,0,0), T=(1,0,0), N=(0,1,0), B=(0,0,1)
    Y0 = np.array(
        [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        dtype=float,
    )

    # 6. Solve IVP with high-order Runge-Kutta
    try:
        sol = solve_ivp(
            frenet_system,
            (s0_f, s1_f),
            Y0,
            t_eval=s_vals,
            method="DOP853",
            rtol=1e-9,
            atol=1e-9,
        )
    except ValueError:
        raise
    except Exception:
        sol = None

    if sol is None or not sol.success:
        try:
            sol = solve_ivp(
                frenet_system,
                (s0_f, s1_f),
                Y0,
                t_eval=s_vals,
                method="RK45",
                rtol=1e-9,
                atol=1e-9,
            )
        except ValueError:
            raise
        except Exception:
            sol = None

    if sol is None or not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message if sol else 'Unknown solver error'}")

    # 7. Extract state matrices
    r = sol.y[0:3, :]
    T_raw = sol.y[3:6, :]
    N_raw = sol.y[6:9, :]
    B_raw = sol.y[9:12, :]

    # 8. Vectorized Modified Gram-Schmidt SO(3) orthonormalization
    T_ortho, N_ortho, B_ortho = orthonormalize_frame(T_raw, N_raw, B_raw)

    # 9. Classify curve
    classification = classify_curve(kappa_expr, tau_expr, s_vals, kappa_vals, tau_vals)

    return CurveResult(
        s=s_vals,
        r=r,
        T=T_ortho,
        N=N_ortho,
        B=B_ortho,
        kappa=kappa_vals,
        tau=tau_vals,
        classification=classification,
        s0=s0_f,
        s1=s1_f,
    )


# ---------------------------------------------------------------------------
# Output Filename Generator & Sanitizer
# ---------------------------------------------------------------------------


def sanitize_expr_for_filename(expr_str: str) -> str:
    """
    Sanitize a mathematical expression string for safe filesystem usage.

    Replaces operators with text abbreviations:
      ** or ^ -> _pow_
      *       -> _mult_
      /       -> _div_
      +       -> _plus_
      -       -> _minus_
      other non-alphanumerics -> _
    """
    s = str(expr_str).strip()
    s = s.replace("**", "_pow_").replace("^", "_pow_")
    s = s.replace("*", "_mult_")
    s = s.replace("/", "_div_")
    s = s.replace("+", "_plus_")
    s = s.replace("-", "_minus_")

    # Replace any remaining non-alphanumeric character with underscore
    s = re.sub(r"[^a-zA-Z0-9_]", "_", s)
    # Collapse consecutive underscores
    s = re.sub(r"_+", "_", s)
    # Strip leading and trailing underscores
    s = s.strip("_")

    return s if s else "0"


def generate_output_filename(
    curve_class: str,
    kappa_str: str,
    tau_str: str,
    s0: float,
    s1: float,
) -> str:
    """
    Generate standard sanitized output filename per specification:
    <identificacao_da_curva>-k<curvatura>-t<torcao>-I<InicioIntervalo_FimIntervalo>.html
    """
    k_san = sanitize_expr_for_filename(kappa_str)
    t_san = sanitize_expr_for_filename(tau_str)
    s0_str = f"{s0:g}"
    s1_str = f"{s1:g}"
    return f"{curve_class}-k{k_san}-t{t_san}-I{s0_str}_{s1_str}.html"
