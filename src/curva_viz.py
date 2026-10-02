"""
Interactive 3D Visualization Engine for the Fundamental Theorem of Curves.

This module provides rich, interactive 3D WebGL visualizations of space and
plane curves reconstructed from their intrinsic differential invariants
(curvature kappa(s) and torsion tau(s)) using Plotly.

Features:
  - 10-trace composite differential apparatus at active point r(s):
      0: Curva r(s) (trajectory with interactive clickable vertices)
      1: Ponto Ativo r(s) (current evaluation point)
      2: Vetor Tangente T (green unit tangent vector)
      3: Vetor Normal N (red principal normal unit vector)
      4: Vetor Binormal B (blue binormal unit vector)
      5: Reta Tangente L_T (tangent line through r(s))
      6: Plano Osculador (T, N) (amber translucent quad, normal to B)
      7: Plano Normal (N, B) (red translucent quad, normal to T)
      8: Plano Retificante (T, B) (blue translucent quad, normal to N)
      9: Círculo Osculador (gold osculating circle with radius rho = 1/|kappa|)
  - Planar curve adaptation:
      When tau == 0, sets top-down orthogonal camera view and hides out-of-plane
      elements (Plano Normal, Plano Retificante, Vetor Binormal) into legendonly.
  - Selective animation frames:
      Animates traces 1..9 while keeping trace 0 static for minimal file size (~1MB).
      Maintains camera orientation via uirevision='constant'.
  - Responsive 100vw x 100vh full-viewport shell:
      CSS reset with 100dvh, zero scrollbars, auto-resize.
  - Client-side JavaScript injection:
      plotly_click curve snapping, slider scrubbing synchronization,
      and floating glassmorphism HUD card with real-time differential invariants.

Theoretical foundations:
  - Toponogov, V. A. (2006). Differential Geometry of Curves and Surfaces.
  - Tenenblat, K. (2008). Introdução à Geometria Diferencial.
  - Alencar, H. & Santos, W. (2009). Geometria Diferencial: Curvas e Superfícies.
  - do Carmo, M. P. (2016). Differential Geometry of Curves and Surfaces.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import plotly.graph_objects as go
import sympy as sp

if TYPE_CHECKING:
    from curva_engine import CurveResult

# ---------------------------------------------------------------------------
# Quad topology for Mesh3d planes
# ---------------------------------------------------------------------------
_QUAD_I = [0, 0]
_QUAD_J = [1, 2]
_QUAD_K = [2, 3]

# ---------------------------------------------------------------------------
# Triedro design system (design-system/): tokens, component CSS, Plotly theme
# ---------------------------------------------------------------------------
_DESIGN_DIR = Path(__file__).resolve().parent.parent / "design-system"


def _read_design_asset(relative: str) -> str:
    """Read a design-system asset, failing loudly if the folder is missing."""
    path = _DESIGN_DIR / relative
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FileNotFoundError(
            f"Design system asset not found: {path}. "
            "Keep the design-system/ folder at the repository root (next to src/)."
        ) from exc


_THEME: dict[str, Any] = json.loads(
    _read_design_asset("assets/Plotly/triedro-plotly-theme.json")
)["themes"]
_LIGHT_TRACES: dict[str, Any] = _THEME["light"]["traces"]
_LIGHT_LAYOUT: dict[str, Any] = _THEME["light"]["layout"]

# Bottom margin (px) that keeps the plot clear of the floating control dock
# (dock height 58 + 24 from the edge, plus room for the axis title).
_DOCK_CLEARANCE = 134
_DOCK_CLEARANCE_3D = 70

# Plotly marker diameters (the theme size is the visual radius token).
_POINT_SIZE_2D = 12
_POINT_SIZE_3D = 9


def _split_rgba(color: str) -> tuple[str, float]:
    """Split 'rgba(r, g, b, a)' into ('rgb(r, g, b)', a); other colors keep alpha 1."""
    m = re.fullmatch(r"rgba\(([^,]+),([^,]+),([^,]+),([^)]+)\)", color.strip())
    if not m:
        return color, 1.0
    r, g, b, a = (part.strip() for part in m.groups())
    return f"rgb({r}, {g}, {b})", float(a)


COLOR_CURVE = _LIGHT_TRACES["curve"]["color"]
COLOR_POINT = _LIGHT_TRACES["active_point"]["color"]
COLOR_POINT_OUTLINE = _LIGHT_TRACES["active_point"]["outline"]
COLOR_TANGENT = _LIGHT_TRACES["tangent"]["color"]
COLOR_NORMAL = _LIGHT_TRACES["normal"]["color"]
COLOR_BINORMAL = _LIGHT_TRACES["binormal"]["color"]
COLOR_CIRCLE = _LIGHT_TRACES["osculating_circle"]["color"]
COLOR_LT_LINE = _LIGHT_TRACES["tangent_line"]["color"]
COLOR_LN_LINE = _LIGHT_TRACES["normal_line"]["color"]
COLOR_PLANE_OSC, _OPACITY_PLANE_OSC = _split_rgba(_LIGHT_TRACES["plane_osculating"]["color"])
COLOR_PLANE_NORM, _OPACITY_PLANE_NORM = _split_rgba(_LIGHT_TRACES["plane_normal"]["color"])
COLOR_PLANE_RECT, _OPACITY_PLANE_RECT = _split_rgba(_LIGHT_TRACES["plane_rectifying"]["color"])

# Roles (keys of the theme's `traces`) of each Plotly trace, by trace index.
_TRACE_ROLES_2D = [
    "curve", "active_point", "tangent", "normal",
    "tangent_line", "normal_line", "osculating_circle", "evolute", "involute",
]
_TRACE_ROLES_3D = [
    "curve", "active_point", "tangent", "normal", "binormal", "tangent_line",
    "plane_osculating", "plane_normal", "plane_rectifying", "osculating_circle",
    "evolute", "involute",
]


def _themed_base_layout() -> dict[str, Any]:
    """Layout fragments shared by 2D and 3D figures (light theme, transparent ground)."""
    return dict(
        paper_bgcolor=_LIGHT_LAYOUT["paper_bgcolor"],
        plot_bgcolor=_LIGHT_LAYOUT["plot_bgcolor"],
        font=_LIGHT_LAYOUT["font"],
        hoverlabel=_LIGHT_LAYOUT["hoverlabel"],
        modebar=_LIGHT_LAYOUT["modebar"],
    )


def _themed_axis_3d(title: str, axis_range: list[float]) -> dict[str, Any]:
    """3D scene axis with fixed range and the theme's axis fragment."""
    return dict(
        title=title,
        range=axis_range,
        autorange=False,
        **_LIGHT_LAYOUT["scene"]["axis"],
    )


# ---------------------------------------------------------------------------
# Geometric classification display names
# ---------------------------------------------------------------------------
_CLASS_DISPLAY_NAMES = {
    "circulo": "Círculo",
    "reta": "Reta",
    "helice_circular": "Hélice Circular",
    "helice_cilindrica_geral": "Hélice Cilíndrica Geral (Lancret)",
    "espiral_de_cornu": "Espiral de Cornu (Clothoid)",
    "espiral_logaritmica": "Espiral Logarítmica",
    "curva_plana": "Curva Plana",
    "curva_espacial": "Curva Espacial",
}


def _format_katex(expr_str: str) -> str:
    """Format an expression string into clean LaTeX for KaTeX rendering."""
    try:
        expr = sp.sympify(expr_str)
        return sp.latex(expr)
    except Exception:
        return expr_str


def _compute_quad_coords(
    P: np.ndarray, v1: np.ndarray, v2: np.ndarray, W: float
) -> tuple[list[float], list[float], list[float]]:
    """Compute 4 vertex coordinates for a planar quad centered at P spanned by v1, v2."""
    p0 = P - W * v1 - W * v2
    p1 = P + W * v1 - W * v2
    p2 = P + W * v1 + W * v2
    p3 = P - W * v1 + W * v2
    return (
        [float(p0[0]), float(p1[0]), float(p2[0]), float(p3[0])],
        [float(p0[1]), float(p1[1]), float(p2[1]), float(p3[1])],
        [float(p0[2]), float(p1[2]), float(p2[2]), float(p3[2])],
    )


def _compute_circle_coords(
    P: np.ndarray,
    T: np.ndarray,
    N: np.ndarray,
    k_val: float,
    span: float,
    num_pts: int = 65,
) -> tuple[list[float], list[float], list[float]]:
    """
    Compute 3D coordinates of the osculating circle at point P.

    Center: c = P + (1/kappa) * N
    Radius: rho = 1/|kappa|
    Parametrization: C(theta) = c - (1/kappa)*N*cos(theta) + rho*T*sin(theta)
    At theta=0: C(0) = P, C'(0) = rho*T, C''(0) = rho*N (second order contact).
    """
    if abs(k_val) <= 1e-5:
        return [], [], []
    rho = 1.0 / abs(k_val)
    if rho > 10.0 * span:
        return [], [], []

    center = P + (1.0 / k_val) * N
    theta = np.linspace(0, 2.0 * np.pi, num_pts)
    # Circle points shape (3, num_pts)
    circle_pts = (
        center[:, None]
        - (1.0 / k_val) * N[:, None] * np.cos(theta)
        + rho * T[:, None] * np.sin(theta)
    )
    return (
        circle_pts[0, :].tolist(),
        circle_pts[1, :].tolist(),
        circle_pts[2, :].tolist(),
    )


_ASSOC_KEYS = ("kE", "tE", "vE", "kI", "tI", "vI")


def _associated_curve_invariants(
    curve_data: CurveResult, is_planar: bool
) -> dict[str, np.ndarray]:
    """
    Curvature, torsion and speed of the evolute E(s) = r + N/kappa and the involute
    I(s) = r + (s1 - s) T, each viewed as a curve parametrized by s.

    Exact symbolic calculus in the Frenet frame: a vector v = v_T T + v_N N + v_B B has
        Dv = (v_T' - kappa v_N) T + (v_N' + kappa v_T - tau v_B) N + (v_B' + tau v_N) B,
    and E' = -(kappa'/kappa^2) N + (tau/kappa) B, I' = (s1 - s) kappa N. For a curve with
    velocity v: curvature = |v x Dv| / |v|^3, torsion = (v x Dv) . D^2v / |v x Dv|^2.
    Points where an invariant is undefined (E' = 0, kappa = 0, ...) are NaN.

    Returns arrays keyed kE, tE, vE (evolute) and kI, tI, vI (involute): curvature,
    torsion and speed |dX/ds|.
    """
    from curva_engine import parse_and_validate_expression

    s_arr = np.asarray(curve_data.s, dtype=float)
    out = {k: np.full_like(s_arr, np.nan) for k in _ASSOC_KEYS}
    try:
        s_sym = sp.Symbol("s")
        kap = parse_and_validate_expression(str(curve_data.kappa_expr))
        tau = sp.Integer(0) if is_planar else parse_and_validate_expression(str(curve_data.tau_expr))
        length = sp.Float(float(s_arr[-1])) - s_sym

        def d_frame(v):
            vt, vn, vb = v
            return (
                sp.diff(vt, s_sym) - kap * vn,
                sp.diff(vn, s_sym) + kap * vt - tau * vb,
                sp.diff(vb, s_sym) + tau * vn,
            )

        def invariants(v1):
            v2 = d_frame(v1)
            v3 = d_frame(v2)
            cross = (
                v1[1] * v2[2] - v1[2] * v2[1],
                v1[2] * v2[0] - v1[0] * v2[2],
                v1[0] * v2[1] - v1[1] * v2[0],
            )
            c2 = sum(c**2 for c in cross)
            speed2 = sum(x**2 for x in v1)
            return (
                sp.sqrt(c2) / speed2 ** sp.Rational(3, 2),
                sum(c * x for c, x in zip(cross, v3)) / c2,
                sp.sqrt(speed2),
            )

        evolute_v = (sp.Integer(0), -sp.diff(kap, s_sym) / kap**2, tau / kap)
        involute_v = (sp.Integer(0), length * kap, sp.Integer(0))
        for (kk, tk, vk), v1 in ((("kE", "tE", "vE"), evolute_v), (("kI", "tI", "vI"), involute_v)):
            for key, expr in zip((kk, tk, vk), invariants(v1)):
                fn = sp.lambdify(s_sym, expr, "numpy")
                with np.errstate(all="ignore"):
                    vals = np.broadcast_to(np.asarray(fn(s_arr), dtype=float), s_arr.shape)
                out[key] = np.where(np.isfinite(vals), vals, np.nan)
    except Exception:
        return {k: np.full_like(s_arr, np.nan) for k in _ASSOC_KEYS}
    if is_planar:
        for key in ("tE", "tI"):
            out[key] = np.where(np.isfinite(out["kE" if key == "tE" else "kI"]), 0.0, np.nan)
    return out


def _opt_float(arr: np.ndarray, idx: int) -> float | None:
    """JSON-safe scalar: NaN becomes None (rendered as an em dash in the viewer)."""
    v = float(arr[idx])
    return v if np.isfinite(v) else None


def _build_apparatus_traces(
    P: np.ndarray,
    T: np.ndarray,
    N: np.ndarray,
    B: np.ndarray,
    L_vec: float,
    L_tan: float,
    W: float,
    k_val: float,
    span: float,
    is_planar: bool,
    is_initial: bool = False,
) -> list[go.Scatter3d | go.Mesh3d]:
    """
    Build traces 1 through 9 for the active Frenet differential apparatus.

    If is_initial is True, includes complete trace styling, names, and visibility.
    If is_initial is False (for animation frames), returns bare coordinates to
    preserve user legend toggles and reduce frame JSON size.
    """
    # Coordinates for tangent line
    lt_x = [float(P[0] - L_tan * T[0]), float(P[0] + L_tan * T[0])]
    lt_y = [float(P[1] - L_tan * T[1]), float(P[1] + L_tan * T[1])]
    lt_z = [float(P[2] - L_tan * T[2]), float(P[2] + L_tan * T[2])]

    # Coordinates for planes
    ox, oy, oz = _compute_quad_coords(P, T, N, W)
    nx, ny, nz = _compute_quad_coords(P, N, B, W)
    rx, ry, rz = _compute_quad_coords(P, T, B, W)

    # Coordinates for osculating circle
    cx, cy, cz = _compute_circle_coords(P, T, N, k_val, span)

    if not is_initial:
        # Bare traces for selective frame update (traces 1..9)
        return [
            # Trace 1: Ponto Ativo
            go.Scatter3d(x=[float(P[0])], y=[float(P[1])], z=[float(P[2])]),
            # Trace 2: Vetor Tangente T
            go.Scatter3d(
                x=[float(P[0]), float(P[0] + L_vec * T[0])],
                y=[float(P[1]), float(P[1] + L_vec * T[1])],
                z=[float(P[2]), float(P[2] + L_vec * T[2])],
            ),
            # Trace 3: Vetor Normal N
            go.Scatter3d(
                x=[float(P[0]), float(P[0] + L_vec * N[0])],
                y=[float(P[1]), float(P[1] + L_vec * N[1])],
                z=[float(P[2]), float(P[2] + L_vec * N[2])],
            ),
            # Trace 4: Vetor Binormal B
            go.Scatter3d(
                x=[float(P[0]), float(P[0] + L_vec * B[0])],
                y=[float(P[1]), float(P[1] + L_vec * B[1])],
                z=[float(P[2]), float(P[2] + L_vec * B[2])],
            ),
            # Trace 5: Reta Tangente
            go.Scatter3d(x=lt_x, y=lt_y, z=lt_z),
            # Trace 6: Plano Osculador
            go.Mesh3d(x=ox, y=oy, z=oz),
            # Trace 7: Plano Normal
            go.Mesh3d(x=nx, y=ny, z=nz),
            # Trace 8: Plano Retificante
            go.Mesh3d(x=rx, y=ry, z=rz),
            # Trace 9: Círculo Osculador
            go.Scatter3d(x=cx, y=cy, z=cz),
        ]

    # Full initial traces with visual styles
    # Trace 1: Ponto Ativo
    t1 = go.Scatter3d(
        x=[float(P[0])],
        y=[float(P[1])],
        z=[float(P[2])],
        mode="markers",
        name="Ponto Ativo r(s)",
        marker=dict(
            size=_POINT_SIZE_3D,
            color=COLOR_POINT,
            symbol="circle",
            line=dict(color=COLOR_POINT_OUTLINE, width=2),
        ),
        hovertemplate="<b>Ponto Ativo r(s)</b><br>x: %{x:.3f}<br>y: %{y:.3f}<br>z: %{z:.3f}<extra></extra>",
    )
    # Trace 2: Vetor Tangente T
    t2 = go.Scatter3d(
        x=[float(P[0]), float(P[0] + L_vec * T[0])],
        y=[float(P[1]), float(P[1] + L_vec * T[1])],
        z=[float(P[2]), float(P[2] + L_vec * T[2])],
        mode="lines+markers",
        name="Vetor Tangente T",
        line=dict(color=COLOR_TANGENT, width=_LIGHT_TRACES["tangent"]["width"]),
        marker=dict(size=[0, 8], color=COLOR_TANGENT),
        hovertemplate="<b>Vetor Tangente T</b><extra></extra>",
    )
    # Trace 3: Vetor Normal N
    t3 = go.Scatter3d(
        x=[float(P[0]), float(P[0] + L_vec * N[0])],
        y=[float(P[1]), float(P[1] + L_vec * N[1])],
        z=[float(P[2]), float(P[2] + L_vec * N[2])],
        mode="lines+markers",
        name="Vetor Normal N",
        line=dict(color=COLOR_NORMAL, width=_LIGHT_TRACES["normal"]["width"]),
        marker=dict(size=[0, 8], color=COLOR_NORMAL),
        hovertemplate="<b>Vetor Normal N</b><extra></extra>",
    )
    # Trace 4: Vetor Binormal B
    t4 = go.Scatter3d(
        x=[float(P[0]), float(P[0] + L_vec * B[0])],
        y=[float(P[1]), float(P[1] + L_vec * B[1])],
        z=[float(P[2]), float(P[2] + L_vec * B[2])],
        mode="lines+markers",
        name="Vetor Binormal B",
        line=dict(color=COLOR_BINORMAL, width=_LIGHT_TRACES["binormal"]["width"]),
        marker=dict(size=[0, 8], color=COLOR_BINORMAL),
        visible="legendonly" if is_planar else True,
        hovertemplate="<b>Vetor Binormal B</b><extra></extra>",
    )
    # Trace 5: Reta Tangente L_T
    t5 = go.Scatter3d(
        x=lt_x,
        y=lt_y,
        z=lt_z,
        mode="lines",
        name="Reta Tangente L_T",
        opacity=_LIGHT_TRACES["tangent_line"]["opacity"],
        line=dict(color=COLOR_LT_LINE, width=_LIGHT_TRACES["tangent_line"]["width"], dash="dash"),
        hovertemplate="<b>Reta Tangente L_T</b><extra></extra>",
    )
    # Trace 6: Plano Osculador (T, N)
    t6 = go.Mesh3d(
        x=ox,
        y=oy,
        z=oz,
        i=_QUAD_I,
        j=_QUAD_J,
        k=_QUAD_K,
        color=COLOR_PLANE_OSC,
        opacity=_OPACITY_PLANE_OSC,
        flatshading=True,
        name="Plano Osculador (T, N)",
        showlegend=True,
        hoverinfo="name",
    )
    # Trace 7: Plano Normal (N, B)
    t7 = go.Mesh3d(
        x=nx,
        y=ny,
        z=nz,
        i=_QUAD_I,
        j=_QUAD_J,
        k=_QUAD_K,
        color=COLOR_PLANE_NORM,
        opacity=_OPACITY_PLANE_NORM,
        flatshading=True,
        name="Plano Normal (N, B)",
        visible="legendonly" if is_planar else True,
        showlegend=True,
        hoverinfo="name",
    )
    # Trace 8: Plano Retificante (T, B)
    t8 = go.Mesh3d(
        x=rx,
        y=ry,
        z=rz,
        i=_QUAD_I,
        j=_QUAD_J,
        k=_QUAD_K,
        color=COLOR_PLANE_RECT,
        opacity=_OPACITY_PLANE_RECT,
        flatshading=True,
        name="Plano Retificante (T, B)",
        visible="legendonly" if is_planar else True,
        showlegend=True,
        hoverinfo="name",
    )
    # Trace 9: Círculo Osculador
    t9 = go.Scatter3d(
        x=cx,
        y=cy,
        z=cz,
        mode="lines",
        name="Círculo Osculador",
        line=dict(color=COLOR_CIRCLE, width=_LIGHT_TRACES["osculating_circle"]["width"]),
        hovertemplate="<b>Círculo Osculador</b><extra></extra>",
    )

    return [t1, t2, t3, t4, t5, t6, t7, t8, t9]


def _build_associated_curve_traces(
    r: np.ndarray,
    T_mat: np.ndarray,
    N_mat: np.ndarray,
    kappa: np.ndarray,
    s: np.ndarray,
    span: float,
    dims: int,
) -> list[go.Scatter | go.Scatter3d]:
    """
    Build the static evolute E(s) = r + N/kappa (dashed) and involute
    I(s) = r + (s1 - s) T (solid), over the whole parameter range. Nothing is
    clipped by size; only points where kappa ~ 0 (no center of curvature) are dropped.
    """
    safe_k = np.where(np.abs(kappa) > 1e-5, kappa, np.nan)
    rho_signed = 1.0 / safe_k
    ok = np.isfinite(rho_signed)
    evo = r[:dims, :] + rho_signed[None, :] * N_mat[:dims, :]
    inv = r[:dims, :] + (s[-1] - s)[None, :] * T_mat[:dims, :]

    def column(arr: np.ndarray, k: int, mask: np.ndarray | None) -> list[float | None]:
        return [
            float(v) if (mask is None or mask[j]) else None
            for j, v in enumerate(arr[k, :])
        ]

    cls = go.Scatter if dims == 2 else go.Scatter3d
    traces = []
    for name, role, arr, mask in (
        ("Evoluta E(s)", "evolute", evo, ok),
        ("Involuta I(s)", "involute", inv, None),
    ):
        spec = _LIGHT_TRACES[role]
        coords = {axis: column(arr, k, mask) for k, axis in enumerate("xyz"[:dims])}
        traces.append(
            cls(
                **coords,
                mode="lines",
                name=name,
                line=dict(color=spec["color"], width=spec["width"], dash="solid"),
                hovertemplate=f"<b>{name}</b><extra></extra>",
            )
        )
    return traces


def _compute_circle_coords_2d(
    P: np.ndarray,
    T: np.ndarray,
    N: np.ndarray,
    k_val: float,
    span: float,
    num_pts: int = 65,
) -> tuple[list[float], list[float]]:
    """Compute 2D coordinates of the osculating circle at point P in R^2."""
    if abs(k_val) <= 1e-5:
        return [], []
    rho = 1.0 / abs(k_val)
    if rho > 10.0 * span:
        return [], []

    center = P[:2] + (1.0 / k_val) * N[:2]
    theta = np.linspace(0.0, 2.0 * np.pi, num_pts)
    circle_pts = (
        center[:, None]
        - (1.0 / k_val) * N[:2, None] * np.cos(theta)
        + rho * T[:2, None] * np.sin(theta)
    )
    return circle_pts[0, :].tolist(), circle_pts[1, :].tolist()


def _build_apparatus_traces_2d(
    P: np.ndarray,
    T: np.ndarray,
    N: np.ndarray,
    L_vec: float,
    L_tan: float,
    k_val: float,
    span: float,
    is_initial: bool = False,
) -> list[go.Scatter]:
    """
    Build traces 1 through 6 for the 2D planar Frenet apparatus.
    """
    lt_x = [float(P[0] - L_tan * T[0]), float(P[0] + L_tan * T[0])]
    lt_y = [float(P[1] - L_tan * T[1]), float(P[1] + L_tan * T[1])]

    ln_x = [float(P[0] - L_tan * N[0]), float(P[0] + L_tan * N[0])]
    ln_y = [float(P[1] - L_tan * N[1]), float(P[1] + L_tan * N[1])]

    cx, cy = _compute_circle_coords_2d(P, T, N, k_val, span)

    if not is_initial:
        return [
            # Trace 1: Ponto Ativo
            go.Scatter(x=[float(P[0])], y=[float(P[1])]),
            # Trace 2: Vetor Tangente T
            go.Scatter(
                x=[float(P[0]), float(P[0] + L_vec * T[0])],
                y=[float(P[1]), float(P[1] + L_vec * T[1])],
            ),
            # Trace 3: Vetor Normal N
            go.Scatter(
                x=[float(P[0]), float(P[0] + L_vec * N[0])],
                y=[float(P[1]), float(P[1] + L_vec * N[1])],
            ),
            # Trace 4: Reta Tangente L_T
            go.Scatter(x=lt_x, y=lt_y),
            # Trace 5: Reta Normal L_N
            go.Scatter(x=ln_x, y=ln_y),
            # Trace 6: Círculo Osculador
            go.Scatter(x=cx, y=cy),
        ]

    # Trace 1: Ponto Ativo r(s)
    t1 = go.Scatter(
        x=[float(P[0])],
        y=[float(P[1])],
        mode="markers",
        name="Ponto Ativo r(s)",
        marker=dict(
            size=_POINT_SIZE_2D,
            color=COLOR_POINT,
            symbol="circle",
            line=dict(color=COLOR_POINT_OUTLINE, width=2),
        ),
        hovertemplate="<b>Ponto Ativo r(s)</b><br>x: %{x:.3f}<br>y: %{y:.3f}<extra></extra>",
    )
    # Trace 2: Vetor Tangente T
    t2 = go.Scatter(
        x=[float(P[0]), float(P[0] + L_vec * T[0])],
        y=[float(P[1]), float(P[1] + L_vec * T[1])],
        mode="lines+markers",
        name="Vetor Tangente T",
        line=dict(color=COLOR_TANGENT, width=_LIGHT_TRACES["tangent"]["width"]),
        marker=dict(size=[0, 8], color=COLOR_TANGENT),
        hovertemplate="<b>Vetor Tangente T</b><extra></extra>",
    )
    # Trace 3: Vetor Normal N
    t3 = go.Scatter(
        x=[float(P[0]), float(P[0] + L_vec * N[0])],
        y=[float(P[1]), float(P[1] + L_vec * N[1])],
        mode="lines+markers",
        name="Vetor Normal N",
        line=dict(color=COLOR_NORMAL, width=_LIGHT_TRACES["normal"]["width"]),
        marker=dict(size=[0, 8], color=COLOR_NORMAL),
        hovertemplate="<b>Vetor Normal N</b><extra></extra>",
    )
    # Trace 4: Reta Tangente L_T
    t4 = go.Scatter(
        x=lt_x,
        y=lt_y,
        mode="lines",
        name="Reta Tangente L_T",
        opacity=_LIGHT_TRACES["tangent_line"]["opacity"],
        line=dict(color=COLOR_LT_LINE, width=_LIGHT_TRACES["tangent_line"]["width"], dash="dash"),
        hovertemplate="<b>Reta Tangente L_T</b><extra></extra>",
    )
    # Trace 5: Reta Normal L_N
    t5 = go.Scatter(
        x=ln_x,
        y=ln_y,
        mode="lines",
        name="Reta Normal L_N",
        opacity=_LIGHT_TRACES["normal_line"]["opacity"],
        line=dict(color=COLOR_LN_LINE, width=_LIGHT_TRACES["normal_line"]["width"], dash="dash"),
        hovertemplate="<b>Reta Normal L_N</b><extra></extra>",
    )
    # Trace 6: Círculo Osculador
    t6 = go.Scatter(
        x=cx,
        y=cy,
        mode="lines",
        name="Círculo Osculador",
        line=dict(color=COLOR_CIRCLE, width=_LIGHT_TRACES["osculating_circle"]["width"]),
        hovertemplate="<b>Círculo Osculador</b><extra></extra>",
    )

    return [t1, t2, t3, t4, t5, t6]


def _build_planar_2d_figure(
    curve_data: CurveResult, title: str | None = None
) -> go.Figure:
    """
    Construct a pure 2D interactive Plotly figure for planar curves (tau == 0).

    The figure carries no title of its own (the viewer sidebar does); ``title`` is
    accepted for API compatibility.
    """
    s = np.asarray(curve_data.s, dtype=float)
    N_pts = len(s)
    r = np.asarray(curve_data.r, dtype=float)
    T_mat = np.asarray(curve_data.T, dtype=float)
    N_mat = np.asarray(curve_data.N, dtype=float)
    kappa = np.asarray(curve_data.kappa, dtype=float)
    tau = np.asarray(curve_data.tau, dtype=float)

    dx = float(np.ptp(r[0, :]))
    dy = float(np.ptp(r[1, :]))
    max_dim = float(max(dx, dy))
    span = max_dim if max_dim > 1e-4 else 1.0
    L_vec = float(np.clip(0.15 * span, 0.05, 5.0))
    L_tan = 2.0 * L_vec

    M_frames = min(N_pts, 200)
    frame_indices = np.unique(
        np.round(np.linspace(0, N_pts - 1, M_frames)).astype(int)
    )
    M_frames = len(frame_indices)

    dist_matrix = np.abs(frame_indices[:, None] - np.arange(N_pts))
    closest_frame_idx = np.argmin(dist_matrix, axis=0)

    customdata = [
        [
            float(s[j]),
            int(closest_frame_idx[j]),
            float(kappa[j]),
            float(tau[j]),
        ]
        for j in range(N_pts)
    ]

    trace_curve = go.Scatter(
        x=r[0, :].tolist(),
        y=r[1, :].tolist(),
        mode="lines+markers",
        name="Curva r(s)",
        line=dict(color=COLOR_CURVE, width=_LIGHT_TRACES["curve"]["width"]),
        marker=dict(size=3, color=COLOR_CURVE),
        customdata=customdata,
        hovertemplate=(
            "<b>Curva r(s)</b><br>"
            "s: %{customdata[0]:.3f}<br>"
            "x: %{x:.3f}<br>"
            "y: %{y:.3f}<br>"
            "κ: %{customdata[2]:.3f}<extra></extra>"
        ),
    )

    idx0 = int(frame_indices[0])
    init_apparatus = _build_apparatus_traces_2d(
        P=r[:, idx0],
        T=T_mat[:, idx0],
        N=N_mat[:, idx0],
        L_vec=L_vec,
        L_tan=L_tan,
        k_val=float(kappa[idx0]),
        span=span,
        is_initial=True,
    )

    fig_data = [
        trace_curve,
        *init_apparatus,
        *_build_associated_curve_traces(r, T_mat, N_mat, kappa, s, span, 2),
    ]

    frames: list[go.Frame] = []
    slider_steps: list[dict[str, Any]] = []
    hud_metrics: list[dict[str, Any]] = []
    assoc = _associated_curve_invariants(curve_data, True)

    for f_idx in range(M_frames):
        pt_idx = int(frame_indices[f_idx])
        k_val = float(kappa[pt_idx])
        rho_val = float(1.0 / abs(k_val)) if abs(k_val) > 1e-5 else None

        # Evolute E(s) = r(s) + (1/kappa) * N(s)
        if abs(k_val) > 1e-5:
            Ex_val = float(r[0, pt_idx] + (1.0 / k_val) * N_mat[0, pt_idx])
            Ey_val = float(r[1, pt_idx] + (1.0 / k_val) * N_mat[1, pt_idx])
        else:
            Ex_val = None
            Ey_val = None

        # Involute I(s) = r(s) + (s1 - s) * T(s)
        s_rem = float(s[-1] - s[pt_idx])
        Ix_val = float(r[0, pt_idx] + s_rem * T_mat[0, pt_idx])
        Iy_val = float(r[1, pt_idx] + s_rem * T_mat[1, pt_idx])

        hud_metrics.append(
            {
                "s": float(s[pt_idx]),
                "x": float(r[0, pt_idx]),
                "y": float(r[1, pt_idx]),
                "z": 0.0,
                "kappa": k_val,
                "tau": 0.0,
                "rho": rho_val,
                "sigma": None,
                "is_planar": True,
                "Tx": float(T_mat[0, pt_idx]),
                "Ty": float(T_mat[1, pt_idx]),
                "Tz": 0.0,
                "Nx": float(N_mat[0, pt_idx]),
                "Ny": float(N_mat[1, pt_idx]),
                "Nz": 0.0,
                "Bx": 0.0,
                "By": 0.0,
                "Bz": 1.0,
                "Ex": Ex_val,
                "Ey": Ey_val,
                "Ez": 0.0,
                "Ix": Ix_val,
                "Iy": Iy_val,
                "Iz": 0.0,
                **{key: _opt_float(assoc[key], pt_idx) for key in _ASSOC_KEYS},
            }
        )

        frame_traces = _build_apparatus_traces_2d(
            P=r[:, pt_idx],
            T=T_mat[:, pt_idx],
            N=N_mat[:, pt_idx],
            L_vec=L_vec,
            L_tan=L_tan,
            k_val=k_val,
            span=span,
            is_initial=False,
        )

        frame_name = f"frame_{f_idx}"
        frames.append(
            go.Frame(
                name=frame_name,
                data=frame_traces,
                traces=[1, 2, 3, 4, 5, 6],
            )
        )

        slider_steps.append(
            dict(
                method="animate",
                args=[
                    [frame_name],
                    {
                        "mode": "immediate",
                        "frame": {"duration": 0, "redraw": False},
                        "transition": {"duration": 0},
                    },
                ],
                label=f"{s[pt_idx]:.2f}",
                value=f_idx,
            )
        )

    sliders = [
        dict(
            active=0,
            currentvalue={
                "prefix": "s = ",
                "visible": True,
                "xanchor": "center",
                "font": {"size": 13, "color": COLOR_CURVE},
            },
            steps=slider_steps,
            pad={"b": 10, "t": 20},
            len=0.88,
            x=0.06,
            y=0.03,
            tickcolor=_LIGHT_LAYOUT["font"]["color"],
            font={"color": _LIGHT_LAYOUT["font"]["color"], "size": 10},
            activebgcolor=COLOR_CURVE,
            borderwidth=1,
        )
    ]

    play_pause_menu = dict(
        type="buttons",
        direction="left",
        showactive=False,
        x=0.06,
        y=0.10,
        xanchor="left",
        yanchor="top",
        pad={"r": 10, "t": 10},
        font={"color": _LIGHT_LAYOUT["hoverlabel"]["font"]["color"], "size": 12},
        buttons=[
            dict(
                label="▶ Play",
                method="animate",
                args=[
                    None,
                    {
                        "frame": {"duration": 35, "redraw": False},
                        "fromcurrent": True,
                        "transition": {"duration": 0},
                        "mode": "immediate",
                    },
                ],
            ),
            dict(
                label="⏸ Pause",
                method="animate",
                args=[
                    [None],
                    {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    },
                ],
            ),
        ],
    )

    # Stable 2D bounding box covering the entire curve plus apparatus
    x_min_c, x_max_c = float(np.min(r[0, :])), float(np.max(r[0, :]))
    y_min_c, y_max_c = float(np.min(r[1, :])), float(np.max(r[1, :]))
    init_xs = [x_min_c, x_max_c, float(r[0, idx0] - L_tan), float(r[0, idx0] + L_tan)]
    init_ys = [y_min_c, y_max_c, float(r[1, idx0] - L_tan), float(r[1, idx0] + L_tan)]

    k0 = float(kappa[idx0])
    if abs(k0) > 1e-5:
        rho0 = 1.0 / abs(k0)
        if rho0 <= 3.0 * span:
            c0 = r[:2, idx0] + (1.0 / k0) * N_mat[:2, idx0]
            init_xs.extend([float(c0[0] - rho0), float(c0[0] + rho0)])
            init_ys.extend([float(c0[1] - rho0), float(c0[1] + rho0)])

    x_min_all = min(init_xs)
    x_max_all = max(init_xs)
    y_min_all = min(init_ys)
    y_max_all = max(init_ys)
    span_x = x_max_all - x_min_all
    span_y = y_max_all - y_min_all
    max_span = max(span_x, span_y, 0.1)
    pad = 0.15 * max_span
    x_mid = 0.5 * (x_min_all + x_max_all)
    y_mid = 0.5 * (y_min_all + y_max_all)
    half_len = 0.5 * max_span + pad
    x_range = [float(x_mid - half_len), float(x_mid + half_len)]
    y_range = [float(y_mid - half_len), float(y_mid + half_len)]

    fig = go.Figure(data=fig_data, frames=frames)
    fig.update_layout(
        **_themed_base_layout(),
        uirevision="constant",
        xaxis=dict(
            title="X",
            range=x_range,
            autorange=False,
            uirevision="constant",
            showgrid=True,
            zeroline=True,
            **{k: v for k, v in _LIGHT_LAYOUT["xaxis_2d"].items() if not k.startswith("scale")},
        ),
        yaxis=dict(
            title="Y",
            range=y_range,
            autorange=False,
            uirevision="constant",
            showgrid=True,
            zeroline=True,
            scaleanchor="x",  # isotropic 1:1 scale
            scaleratio=1,
            **_LIGHT_LAYOUT["yaxis_2d"],
        ),
        margin=dict(l=45, r=25, t=20, b=_DOCK_CLEARANCE),
        showlegend=False,
        sliders=sliders,
        updatemenus=[play_pause_menu],
    )

    fig._curve_result = curve_data  # type: ignore[attr-defined]
    fig._hud_metrics = hud_metrics  # type: ignore[attr-defined]
    fig._is_planar = True  # type: ignore[attr-defined]

    return fig


def _build_spatial_3d_figure(
    curve_data: CurveResult, title: str | None = None
) -> go.Figure:
    """
    Construct a complete 10-trace interactive 3D Plotly figure.

    Traces:
        0: Curva r(s) (with customdata for click snapping)
        1: Ponto Ativo r(s)
        2: Vetor Tangente T
        3: Vetor Normal N
        4: Vetor Binormal B
        5: Reta Tangente L_T
        6: Plano Osculador (T, N)
        7: Plano Normal (N, B)
        8: Plano Retificante (T, B)
        9: Círculo Osculador

    Parameters:
        curve_data: CurveResult dataclass instance containing curve invariants.
        title: Optional custom figure title.

    Returns:
        go.Figure: Full Plotly figure with selective frames, slider, and controls.
    """
    s = np.asarray(curve_data.s, dtype=float)
    N_pts = len(s)
    if N_pts < 2:
        raise ValueError("CurveResult must contain at least 2 points.")

    r = np.asarray(curve_data.r, dtype=float)
    T_mat = np.asarray(curve_data.T, dtype=float)
    N_mat = np.asarray(curve_data.N, dtype=float)
    B_mat = np.asarray(curve_data.B, dtype=float)
    kappa = np.asarray(curve_data.kappa, dtype=float)
    tau = np.asarray(curve_data.tau, dtype=float)

    # Planar curve detection
    is_planar = bool(
        np.all(np.abs(tau) < 1e-5)
        or curve_data.classification
        in (
            "circulo",
            "reta",
            "espiral_de_cornu",
            "espiral_logaritmica",
            "curva_plana",
        )
    )

    # Characteristic scale for visual apparatus
    dx = float(np.ptp(r[0, :]))
    dy = float(np.ptp(r[1, :]))
    dz = float(np.ptp(r[2, :]))
    max_dim = float(max(dx, dy, dz))
    span = max_dim if max_dim > 1e-4 else 1.0
    L_vec = float(np.clip(0.15 * span, 0.05, 5.0))
    L_tan = 2.0 * L_vec
    W = 1.2 * L_vec

    # Subsample frames for slider animation (up to 200 frames for responsiveness)
    M_frames = min(N_pts, 200)
    frame_indices = np.unique(
        np.round(np.linspace(0, N_pts - 1, M_frames)).astype(int)
    )
    M_frames = len(frame_indices)

    # For each trajectory vertex, find the closest frame index for snapping
    # Matrix of distances: (M_frames, N_pts)
    dist_matrix = np.abs(frame_indices[:, None] - np.arange(N_pts))
    closest_frame_idx = np.argmin(dist_matrix, axis=0)

    # Build customdata for Trace 0: [s, frameIdx, kappa, tau]
    customdata = [
        [
            float(s[j]),
            int(closest_frame_idx[j]),
            float(kappa[j]),
            float(tau[j]),
        ]
        for j in range(N_pts)
    ]

    # Trace 0: Curva r(s)
    trace_curve = go.Scatter3d(
        x=r[0, :].tolist(),
        y=r[1, :].tolist(),
        z=r[2, :].tolist(),
        mode="lines+markers",
        name="Curva r(s)",
        line=dict(color=COLOR_CURVE, width=_LIGHT_TRACES["curve"]["width"]),
        marker=dict(size=3, color=COLOR_CURVE),
        customdata=customdata,
        hovertemplate=(
            "<b>Curva r(s)</b><br>"
            "s: %{customdata[0]:.3f}<br>"
            "x: %{x:.3f}<br>"
            "y: %{y:.3f}<br>"
            "z: %{z:.3f}<br>"
            "κ: %{customdata[2]:.3f}<br>"
            "τ: %{customdata[3]:.3f}<extra></extra>"
        ),
    )

    # Initial apparatus at first frame
    idx0 = int(frame_indices[0])
    init_apparatus = _build_apparatus_traces(
        P=r[:, idx0],
        T=T_mat[:, idx0],
        N=N_mat[:, idx0],
        B=B_mat[:, idx0],
        L_vec=L_vec,
        L_tan=L_tan,
        W=W,
        k_val=float(kappa[idx0]),
        span=span,
        is_planar=is_planar,
        is_initial=True,
    )

    # Initial data: Trace 0 + Traces 1..9
    assoc_traces = _build_associated_curve_traces(r, T_mat, N_mat, kappa, s, span, 3)
    fig_data = [trace_curve, *init_apparatus, *assoc_traces]

    # Build animation frames (selective update of traces 1..9)
    frames: list[go.Frame] = []
    slider_steps: list[dict[str, Any]] = []
    hud_metrics: list[dict[str, Any]] = []
    assoc = _associated_curve_invariants(curve_data, is_planar)

    for f_idx in range(M_frames):
        pt_idx = int(frame_indices[f_idx])
        k_val = float(kappa[pt_idx])
        t_val = float(tau[pt_idx])
        rho_val = float(1.0 / abs(k_val)) if abs(k_val) > 1e-5 else None
        sigma_val = float(1.0 / abs(t_val)) if abs(t_val) > 1e-5 else None

        # Evolute E(s) = r(s) + (1/kappa) * N(s)
        if abs(k_val) > 1e-5:
            Ex_val = float(r[0, pt_idx] + (1.0 / k_val) * N_mat[0, pt_idx])
            Ey_val = float(r[1, pt_idx] + (1.0 / k_val) * N_mat[1, pt_idx])
            Ez_val = float(r[2, pt_idx] + (1.0 / k_val) * N_mat[2, pt_idx])
        else:
            Ex_val = None
            Ey_val = None
            Ez_val = None

        # Involute I(s) = r(s) + (s1 - s) * T(s)
        s_rem = float(s[-1] - s[pt_idx])
        Ix_val = float(r[0, pt_idx] + s_rem * T_mat[0, pt_idx])
        Iy_val = float(r[1, pt_idx] + s_rem * T_mat[1, pt_idx])
        Iz_val = float(r[2, pt_idx] + s_rem * T_mat[2, pt_idx])

        # Collect HUD metrics
        hud_metrics.append(
            {
                "s": float(s[pt_idx]),
                "x": float(r[0, pt_idx]),
                "y": float(r[1, pt_idx]),
                "z": float(r[2, pt_idx]),
                "kappa": k_val,
                "tau": t_val,
                "rho": rho_val,
                "sigma": sigma_val,
                "is_planar": is_planar,
                "Tx": float(T_mat[0, pt_idx]),
                "Ty": float(T_mat[1, pt_idx]),
                "Tz": float(T_mat[2, pt_idx]),
                "Nx": float(N_mat[0, pt_idx]),
                "Ny": float(N_mat[1, pt_idx]),
                "Nz": float(N_mat[2, pt_idx]),
                "Bx": float(B_mat[0, pt_idx]),
                "By": float(B_mat[1, pt_idx]),
                "Bz": float(B_mat[2, pt_idx]),
                "Ex": Ex_val,
                "Ey": Ey_val,
                "Ez": Ez_val,
                "Ix": Ix_val,
                "Iy": Iy_val,
                "Iz": Iz_val,
                **{key: _opt_float(assoc[key], pt_idx) for key in _ASSOC_KEYS},
            }
        )

        # Build frame data for traces 1..9
        frame_traces = _build_apparatus_traces(
            P=r[:, pt_idx],
            T=T_mat[:, pt_idx],
            N=N_mat[:, pt_idx],
            B=B_mat[:, pt_idx],
            L_vec=L_vec,
            L_tan=L_tan,
            W=W,
            k_val=k_val,
            span=span,
            is_planar=is_planar,
            is_initial=False,
        )

        frame_name = f"frame_{f_idx}"
        frames.append(
            go.Frame(
                name=frame_name,
                data=frame_traces,
                traces=[1, 2, 3, 4, 5, 6, 7, 8, 9],
            )
        )

        slider_steps.append(
            dict(
                method="animate",
                args=[
                    [frame_name],
                    {
                        "mode": "immediate",
                        "frame": {"duration": 0, "redraw": True},
                        "transition": {"duration": 0},
                    },
                ],
                label=f"{s[pt_idx]:.2f}",
                value=f_idx,
            )
        )

    # Slider configuration
    sliders = [
        dict(
            active=0,
            currentvalue={
                "prefix": "s = ",
                "visible": True,
                "xanchor": "center",
                "font": {"size": 13, "color": COLOR_CURVE},
            },
            steps=slider_steps,
            pad={"b": 10, "t": 20},
            len=0.88,
            x=0.06,
            y=0.03,
            tickcolor=_LIGHT_LAYOUT["font"]["color"],
            font={"color": _LIGHT_LAYOUT["font"]["color"], "size": 10},
            activebgcolor=COLOR_CURVE,
            borderwidth=1,
        )
    ]

    # Controls: Play/Pause and Camera buttons
    play_pause_menu = dict(
        type="buttons",
        direction="left",
        showactive=False,
        x=0.06,
        y=0.10,
        xanchor="left",
        yanchor="top",
        pad={"r": 10, "t": 10},
        font={"color": _LIGHT_LAYOUT["hoverlabel"]["font"]["color"], "size": 12},
        buttons=[
            dict(
                label="▶ Play",
                method="animate",
                args=[
                    None,
                    {
                        "frame": {"duration": 35, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 0},
                        "mode": "immediate",
                    },
                ],
            ),
            dict(
                label="⏸ Pause",
                method="animate",
                args=[
                    [None],
                    {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    },
                ],
            ),
        ],
    )

    camera_menu = dict(
        type="buttons",
        direction="down",
        showactive=True,
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        font={"color": _LIGHT_LAYOUT["hoverlabel"]["font"]["color"], "size": 11},
        buttons=[
            dict(
                label="Vista 3D",
                method="relayout",
                args=[
                    {
                        "scene.camera": dict(
                            eye=dict(x=1.6, y=1.6, z=1.3),
                            up=dict(x=0, y=0, z=1),
                            center=dict(x=0, y=0, z=0),
                        )
                    }
                ],
            ),
            dict(
                label="Vista 2D (XY)",
                method="relayout",
                args=[
                    {
                        "scene.camera": dict(
                            eye=dict(x=0, y=0, z=2.5),
                            up=dict(x=0, y=1, z=0),
                            center=dict(x=0, y=0, z=0),
                        )
                    }
                ],
            ),
        ],
    )

    updatemenus = [play_pause_menu, camera_menu]

    # Initial camera setup
    if is_planar:
        init_camera = dict(
            eye=dict(x=0, y=0, z=2.5),
            up=dict(x=0, y=1, z=0),
            center=dict(x=0, y=0, z=0),
        )
    else:
        init_camera = dict(
            eye=dict(x=1.6, y=1.6, z=1.3),
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0),
        )

    # Stable 3D bounding box covering the entire curve plus apparatus
    x_min_c, x_max_c = float(np.min(r[0, :])), float(np.max(r[0, :]))
    y_min_c, y_max_c = float(np.min(r[1, :])), float(np.max(r[1, :]))
    z_min_c, z_max_c = float(np.min(r[2, :])), float(np.max(r[2, :]))

    init_xs = [x_min_c, x_max_c, float(r[0, idx0] - W), float(r[0, idx0] + W)]
    init_ys = [y_min_c, y_max_c, float(r[1, idx0] - W), float(r[1, idx0] + W)]
    init_zs = [z_min_c, z_max_c, float(r[2, idx0] - W), float(r[2, idx0] + W)]

    k0 = float(kappa[idx0])
    if abs(k0) > 1e-5:
        rho0 = 1.0 / abs(k0)
        if rho0 <= 2.5 * span:
            c0 = r[:, idx0] + (1.0 / k0) * N_mat[:, idx0]
            init_xs.extend([float(c0[0] - rho0), float(c0[0] + rho0)])
            init_ys.extend([float(c0[1] - rho0), float(c0[1] + rho0)])
            init_zs.extend([float(c0[2] - rho0), float(c0[2] + rho0)])

    # The 3D box cannot be panned or zoomed open (zoom only moves the camera), so it must
    # contain the whole evolute and involute or Plotly clips them at its walls.
    for trace in assoc_traces:
        for coords, axis_vals in zip((trace.x, trace.y, trace.z), (init_xs, init_ys, init_zs)):
            finite = [v for v in coords if v is not None]
            if finite:
                axis_vals.extend([min(finite), max(finite)])

    sides = [(min(v), max(v)) for v in (init_xs, init_ys, init_zs)]
    x_mid, y_mid, z_mid = (0.5 * (lo + hi) for lo, hi in sides)
    max_span = max(max(hi - lo for lo, hi in sides), 0.1)
    pad = 0.15 * max_span
    half_len = 0.5 * max_span + pad
    x_range = [float(x_mid - half_len), float(x_mid + half_len)]
    y_range = [float(y_mid - half_len), float(y_mid + half_len)]
    z_range = [float(z_mid - half_len), float(z_mid + half_len)]

    fig = go.Figure(data=fig_data, frames=frames)
    fig.update_layout(
        **_themed_base_layout(),
        uirevision="constant",
        scene=dict(
            uirevision="constant",
            aspectmode="cube",
            camera=init_camera,
            bgcolor=_LIGHT_LAYOUT["scene"]["bgcolor"],
            xaxis=_themed_axis_3d("X", x_range),
            yaxis=_themed_axis_3d("Y", y_range),
            zaxis=_themed_axis_3d("Z", z_range),
        ),
        margin=dict(l=0, r=0, t=20, b=_DOCK_CLEARANCE_3D),
        showlegend=False,
        sliders=sliders,
        updatemenus=updatemenus,
    )

    # Attach internal metadata for HTML exporter
    fig._curve_result = curve_data  # type: ignore[attr-defined]
    fig._hud_metrics = hud_metrics  # type: ignore[attr-defined]
    fig._is_planar = False  # type: ignore[attr-defined]

    return fig


def build_curve_figure(
    curve_data: CurveResult, title: str | None = None
) -> go.Figure:
    """
    Construct an interactive Plotly figure representing the curve and differential apparatus.

    For planar curves (tau == 0), generates a pure 2D Cartesian figure (go.Scatter) with
    the complete 2D differential geometry apparatus (trajectory, active point, tangent vector,
    normal vector, tangent line, normal line, and osculating circle) with equal-aspect axes (1:1).

    For space curves (tau != 0), generates a full 10-trace 3D WebGL figure (go.Scatter3d and
    go.Mesh3d) with the complete moving Frenet frame {T, N, B}, tangent line, osculating plane,
    normal plane, rectifying plane, and 3D osculating circle.
    """
    s = np.asarray(curve_data.s, dtype=float)
    N_pts = len(s)
    if N_pts < 2:
        raise ValueError("CurveResult must contain at least 2 points.")

    tau = np.asarray(curve_data.tau, dtype=float)
    is_planar = bool(
        getattr(curve_data, "is_planar", False)
        or np.all(np.abs(tau) < 1e-5)
        or curve_data.classification
        in (
            "circulo",
            "reta",
            "espiral_de_cornu",
            "espiral_logaritmica",
            "curva_plana",
        )
    )

    if is_planar:
        return _build_planar_2d_figure(curve_data, title=title)
    return _build_spatial_3d_figure(curve_data, title=title)


def _clothoid_formulas(kappa_expr: str) -> dict[str, str]:
    """
    Closed-form formulas for the clothoid kappa(s) = c*s + d (theta(0) = 0, r(0) = 0).

    With theta(s) = c s^2/2 + d s, completing the square gives
        r(s) = R(phi0) * sqrt(pi/c) * (C(x(s)) - C(x0), S(x(s)) - S(x0)),
    where C, S are the Fresnel integrals, x(s) = sqrt(c/pi) (s + d/c), x0 = x(0)
    and phi0 = -d^2/(2c). For d = 0 this reduces to sqrt(pi/c) (C(x), S(x)).
    """
    s_sym = sp.Symbol("s")
    try:
        poly = sp.Poly(sp.sympify(kappa_expr), s_sym)
        c = poly.coeff_monomial(s_sym)
        d = poly.coeff_monomial(1)
        if c == 0 or not (c.is_number and d.is_number):
            raise ValueError
    except Exception:
        c = sp.Symbol("c", positive=True)
        d = sp.Integer(0)
        symbolic = True
    else:
        symbolic = False

    kap_l = sp.latex(c * s_sym + d)
    theta_l = sp.latex(c * s_sym**2 / 2 + d * s_sym)
    pref_l = sp.latex(sp.sqrt(sp.pi / c))
    # Definitions of the special functions used by r(s), shown as a second formula line.
    curve_aux = (
        r"C(x) = \int_0^x \cos\frac{\pi t^2}{2}\,dt,\quad S(x) = \int_0^x \sin\frac{\pi t^2}{2}\,dt"
    )

    if d == 0:
        arg_l = sp.latex(sp.sqrt(c / sp.pi) * s_sym)
        curve_r = (
            rf"r(s) = {pref_l}\left( C\!\left({arg_l}\right),\, S\!\left({arg_l}\right) \right)"
        )
    else:
        curve_aux += (
            r",\quad R_\varphi = \begin{pmatrix} \cos\varphi & -\sin\varphi \\ \sin\varphi & \cos\varphi \end{pmatrix}"
        )
        arg_l = sp.latex(sp.sqrt(c / sp.pi) * (s_sym + d / c))
        x0_l = sp.latex(sp.sqrt(c / sp.pi) * d / c)
        phi_l = sp.latex(-d**2 / (2 * c))
        curve_r = (
            rf"r(s) = R_{{{phi_l}}}\, {pref_l}\left( C\!\left({arg_l}\right) - C\!\left({x0_l}\right),\,"
            rf" S\!\left({arg_l}\right) - S\!\left({x0_l}\right) \right)"
        )

    return {
        "curve_r": curve_r,
        "curve_aux": curve_aux,
        "vec_t": rf"T(s) = \left( \cos\left({theta_l}\right),\, \sin\left({theta_l}\right) \right)",
        "vec_n": rf"N(s) = \left( -\sin\left({theta_l}\right),\, \cos\left({theta_l}\right) \right)",
        "vec_b": "",
        "evolute": rf"E(s) = r(s) + \frac{{1}}{{{kap_l}}} N(s)" if not symbolic else r"E(s) = r(s) + \frac{1}{c\,s} N(s)",
        "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
        "radii": rf"\rho(s) = \frac{{1}}{{|{kap_l}|}}, \quad \sigma(s) = \infty",
    }


def _build_curve_formulas(
    curve_res: CurveResult | None, is_planar: bool
) -> dict[str, str]:
    """
    Construct LaTeX formulas and descriptions for the curve r(s), Frenet frame
    {T, N, B}, evolute E(s), involute I(s), and differential geometric properties
    based on the Fundamental Theorem of Curves and the curve classification.
    """
    cls = getattr(curve_res, "classification", "") if curve_res else ""
    kappa_expr = getattr(curve_res, "kappa_expr", "1") if curve_res else "1"
    tau_expr = getattr(curve_res, "tau_expr", "0") if curve_res else "0"
    s0 = float(getattr(curve_res, "s0", 0.0)) if curve_res else 0.0
    s1 = float(getattr(curve_res, "s1", 6.28)) if curve_res else 6.28

    if cls == "circulo":
        return {
            "curve_r": r"r(s) = \left( \frac{\sin(\kappa s)}{\kappa},\, \frac{1 - \cos(\kappa s)}{\kappa} \right)",
            "vec_t": r"T(s) = \left( \cos(\kappa s),\, \sin(\kappa s) \right) = \frac{dr}{ds}",
            "vec_n": r"N(s) = \left( -\sin(\kappa s),\, \cos(\kappa s) \right) = J \cdot T(s)",
            "vec_b": "",
            "evolute": r"E(s) = \left( 0,\, \frac{1}{\kappa} \right)",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "radii": r"\rho(s) = \frac{1}{\kappa} = R, \quad \sigma(s) = \infty",
        }
    elif cls == "reta":
        return {
            "curve_r": r"r(s) = r(s_0) + s\,T_0",
            "vec_t": r"T(s) = T_0 = \text{const}",
            "vec_n": r"N(s) = N_0 = \text{const}",
            "vec_b": r"B(s) = B_0 = \text{const}" if not is_planar else "",
            "evolute": r"E(s) \to \infty",
            "involute": r"I(s) = r(s_1) = \text{const}",
            "radii": r"\rho(s) = \infty" + (r", \quad \sigma(s) = \infty" if not is_planar else ""),
        }
    elif cls == "helice_circular":
        return {
            "curve_r": r"r(s) = \left( \frac{\kappa}{\omega^2}\big(1 - \cos(\omega s)\big),\, \frac{\kappa}{\omega^2}\sin(\omega s),\, \frac{\tau}{\omega} s \right)",
            "vec_t": r"T(s) = \left( \frac{\kappa}{\omega}\sin(\omega s),\, \frac{\kappa}{\omega}\cos(\omega s),\, \frac{\tau}{\omega} \right)",
            "vec_n": r"N(s) = \left( \cos(\omega s),\, -\sin(\omega s),\, 0 \right)",
            "vec_b": r"B(s) = \left( \frac{\tau}{\omega}\sin(\omega s),\, \frac{\tau}{\omega}\cos(\omega s),\, -\frac{\kappa}{\omega} \right)",
            "evolute": r"E(s) = r(s) + \frac{1}{\kappa} N(s)",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "radii": r"\rho = \frac{1}{\kappa}, \quad \sigma = \frac{1}{\tau} \quad (\text{constantes})",
        }
    elif cls == "helice_cilindrica_geral":
        return {
            "curve_r": r"r(s) = r(s_0) + \int_{s_0}^s T(u)\,du",
            "vec_t": r"T'(s) = \kappa(s) N(s), \quad \langle T(s), u_0 \rangle = \cos\alpha",
            "vec_n": r"N(s) = \frac{T'(s)}{\kappa(s)} = \frac{1}{\kappa(s)} \frac{dT}{ds}",
            "vec_b": r"B(s) = T(s) \times N(s)",
            "evolute": r"E(s) = r(s) + \frac{1}{\kappa(s)} N(s)",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "radii": r"\rho(s) = \frac{1}{|\kappa(s)|}, \quad \sigma(s) = \frac{1}{|\tau(s)|}, \quad \frac{\sigma}{\rho} = \text{const}",
        }
    elif cls == "espiral_de_cornu":
        return _clothoid_formulas(kappa_expr)
    elif cls == "espiral_logaritmica":
        return {
            "curve_r": r"r(s) = r(s_0) + \int_{s_0}^s (\cos\theta(u),\, \sin\theta(u))\,du",
            "vec_t": r"T(s) = \left( \cos\theta(s),\, \sin\theta(s) \right), \quad \theta(s) = \int \kappa\,du",
            "vec_n": r"N(s) = \left( -\sin\theta(s),\, \cos\theta(s) \right)",
            "vec_b": "",
            "evolute": r"E(s) = r(s) + (a s + b) N(s)",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "radii": r"\rho(s) = |a s + b|, \quad \sigma(s) = \infty",
        }
    elif is_planar:
        return {
            "curve_r": r"r(s) = r(s_0) + \int_{s_0}^s (\cos\theta(u),\, \sin\theta(u))\,du",
            "vec_t": r"T(s) = \left( \cos\theta(s),\, \sin\theta(s) \right) = \frac{dr}{ds}",
            "vec_n": r"N(s) = \left( -\sin\theta(s),\, \cos\theta(s) \right) = J \cdot T(s)",
            "vec_b": "",
            "evolute": r"E(s) = r(s) + \frac{1}{\kappa(s)} N(s)",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "radii": r"\rho(s) = \frac{1}{|\kappa(s)|}, \quad \sigma(s) = \infty",
        }
    else:
        return {
            "curve_r": r"r(s) = r(s_0) + \int_{s_0}^s T(u)\,du",
            "vec_t": r"\frac{dT}{ds} = \kappa(s) N(s), \quad T(s) = \frac{dr}{ds}",
            "vec_n": r"\frac{dN}{ds} = -\kappa(s) T(s) + \tau(s) B(s)",
            "vec_b": r"\frac{dB}{ds} = -\tau(s) N(s), \quad B(s) = T(s) \times N(s)",
            "evolute": r"E(s) = r(s) + \frac{1}{\kappa(s)} N(s)",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "radii": r"\rho(s) = \frac{1}{|\kappa(s)|}, \quad \sigma(s) = \frac{1}{|\tau(s)|}",
        }


def export_interactive_html(
    curve_data: CurveResult | go.Figure,
    output_path: str,
    title: str | None = None,
    include_plotlyjs: bool | str = "cdn",
) -> str:
    """
    Export the interactive curve visualization to a responsive HTML file.

    For planar curves (tau == 0), generates a purely 2D Cartesian interactive view.
    For space curves (tau != 0), generates a 3D WebGL interactive view.

    Injects fullscreen responsive CSS reset (100vw, 100vh, 100dvh, overflow: hidden),
    client-side JavaScript listeners (plotly_click curve snapping, slider tracking,
    window resize), and a floating glassmorphic HUD card with live parameters.

    Parameters:
        curve_data: CurveResult instance or pre-built go.Figure.
        output_path: Target HTML file path.
        title: Optional custom page and plot title.
        include_plotlyjs: 'cdn' (default) or True/False for bundling.

    Returns:
        str: Absolute path of the exported HTML file.
    """
    if isinstance(curve_data, go.Figure):
        fig = curve_data
        curve_res = getattr(fig, "_curve_result", None)
        hud_metrics = getattr(fig, "_hud_metrics", None)
        is_planar = getattr(fig, "_is_planar", False)
    else:
        curve_res = curve_data
        is_planar = bool(getattr(curve_res, "is_planar", False))
        fig = build_curve_figure(curve_data, title=title)
        hud_metrics = getattr(fig, "_hud_metrics", None)

    # Compute default title and metadata
    if curve_res is not None:
        is_planar = bool(getattr(curve_res, "is_planar", False)) or getattr(fig, "_is_planar", False)
        class_name = curve_res.classification
        class_label = _CLASS_DISPLAY_NAMES.get(
            class_name, class_name.replace("_", " ").title()
        )
        init_s = float(curve_res.s[0])
        init_x = float(curve_res.r[0, 0])
        init_y = float(curve_res.r[1, 0])
        init_z = float(curve_res.r[2, 0])
        init_k = float(curve_res.kappa[0])
        init_t = float(curve_res.tau[0])
        init_rho = f"{1.0 / abs(init_k):.3f}" if abs(init_k) > 1e-5 else "∞"
    else:
        is_planar = getattr(fig, "_is_planar", False)
        class_label = "Curva Reconstruída"
        init_s = 0.0
        init_x, init_y, init_z = 0.0, 0.0, 0.0
        init_k, init_t = 0.0, 0.0
        init_rho = "—"

    if is_planar:
        mode_label = "2D"
        init_pos_str = f"({init_x:.2f}, {init_y:.2f})"
        init_t_str = "0.000 (plana)"
        hint_str = "Diedro de Frenet (T, N): clique na curva ou arraste o controle."
        page_title = title or f"Teorema Fundamental das Curvas Planas — {class_label} (2D)"
    else:
        mode_label = "3D"
        init_pos_str = f"({init_x:.2f}, {init_y:.2f}, {init_z:.2f})"
        init_t_str = f"{init_t:.3f}"
        hint_str = "Triedro de Frenet (T, N, B): clique na curva ou arraste o controle."
        page_title = title or f"Teorema Fundamental de Curvas — {class_label} (3D)"

    # Prepare HUD metrics JSON
    metrics_json = json.dumps(hud_metrics or [])
    num_frames = len(hud_metrics) if hud_metrics else 1

    s_arr = getattr(curve_res, "s", [0.0, 6.28]) if curve_res else [0.0, 6.28]
    s0 = float(s_arr[0])
    s1 = float(s_arr[-1])
    kappa_expr = getattr(curve_res, "kappa_expr", "1") if curve_res else "1"
    tau_expr = getattr(curve_res, "tau_expr", "0") if curve_res else "0"
    kappa_tex = _format_katex(str(kappa_expr))
    tau_tex = _format_katex(str(tau_expr)) if not is_planar else "0"

    init_tx, init_ty, init_tz = 1.0, 0.0, 0.0
    init_nx, init_ny, init_nz = 0.0, 1.0, 0.0
    init_bx, init_by, init_bz = 0.0, 0.0, 1.0
    if curve_res is not None and getattr(curve_res, "T", None) is not None:
        init_tx = float(curve_res.T[0, 0])
        init_ty = float(curve_res.T[1, 0])
        init_tz = float(curve_res.T[2, 0]) if not is_planar else 0.0
        init_nx = float(curve_res.N[0, 0])
        init_ny = float(curve_res.N[1, 0])
        init_nz = float(curve_res.N[2, 0]) if not is_planar else 0.0
        if not is_planar and getattr(curve_res, "B", None) is not None:
            init_bx = float(curve_res.B[0, 0])
            init_by = float(curve_res.B[1, 0])
            init_bz = float(curve_res.B[2, 0])

    init_ex = None
    init_ey = None
    init_ez = None
    init_ix = None
    init_iy = None
    init_iz = None
    init_sigma_str = "∞"

    if hud_metrics and len(hud_metrics) > 0:
        m0 = hud_metrics[0]
        init_ex = m0.get("Ex")
        init_ey = m0.get("Ey")
        init_ez = m0.get("Ez")
        init_ix = m0.get("Ix")
        init_iy = m0.get("Iy")
        init_iz = m0.get("Iz")
        sig_val = m0.get("sigma")
        if sig_val is not None:
            init_sigma_str = f"{sig_val:.3f}"
        elif not is_planar and abs(init_t) > 1e-5:
            init_sigma_str = f"{1.0 / abs(init_t):.3f}"
        else:
            init_sigma_str = "∞"
    else:
        if abs(init_k) > 1e-5:
            init_ex = init_x + (1.0 / init_k) * init_nx
            init_ey = init_y + (1.0 / init_k) * init_ny
            init_ez = init_z + (1.0 / init_k) * init_nz
        s_rem0 = s1 - s0
        init_ix = init_x + s_rem0 * init_tx
        init_iy = init_y + s_rem0 * init_ty
        init_iz = init_z + s_rem0 * init_tz
        if not is_planar and abs(init_t) > 1e-5:
            init_sigma_str = f"{1.0 / abs(init_t):.3f}"
        else:
            init_sigma_str = "∞"

    if init_ex is not None and init_ey is not None:
        init_evo_str = (
            f"({init_ex:.2f}, {init_ey:.2f})"
            if is_planar
            else f"({init_ex:.2f}, {init_ey:.2f}, {init_ez:.2f})"
        )
    else:
        init_evo_str = "—"

    if init_ix is not None and init_iy is not None:
        init_inv_str = (
            f"({init_ix:.2f}, {init_iy:.2f})"
            if is_planar
            else f"({init_ix:.2f}, {init_iy:.2f}, {init_iz:.2f})"
        )
    else:
        init_inv_str = "—"

    formulas = _build_curve_formulas(curve_res, is_planar)

    binormal_formula_html = ""
    sigma_hud_row = ""
    if not is_planar:
        binormal_formula_html = f"""
            <div class="formula-row">
              <div class="formula-title"><span>Vetor Binormal</span> <span class="formula-badge badge-b">B(s)</span></div>
              <div class="formula-math" id="math-vec-b">${formulas["vec_b"]}$</div>
            </div>
        """
        sigma_hud_row = f'<div class="hud-row"><span class="hud-label">Raio Torção σ(s):</span><span class="hud-value" id="hud-sigma">{init_sigma_str}</span></div>'

    if is_planar:
        vec_html = f"""
        <div class="vec-item"><span class="vec-tag vec-t">T</span><span class="vec-val" id="hud-vec-t">[{init_tx:.3f}, {init_ty:.3f}]</span></div>
        <div class="vec-item"><span class="vec-tag vec-n">N</span><span class="vec-val" id="hud-vec-n">[{init_nx:.3f}, {init_ny:.3f}]</span></div>
        """
        switches = [
            ("Curva r(s)", COLOR_CURVE, 0, True),
            ("Ponto Ativo r(s)", COLOR_POINT, 1, True),
            ("Vetor Tangente T", COLOR_TANGENT, 2, True),
            ("Vetor Normal N", COLOR_NORMAL, 3, True),
            ("Reta Tangente L_T", "rgba(16, 185, 129, 0.7)", 4, True),
            ("Reta Normal L_N", "rgba(239, 68, 68, 0.7)", 5, True),
            ("Círculo Osculador", COLOR_CIRCLE, 6, True),
        ]
        theory_summary = (
            r"Pelo <b>Teorema Fundamental das Curvas Planas</b>, a curvatura com sinal "
            r"$\kappa(s)$ determina a curva de modo único a menos de rotações e translações "
            r"no plano $\mathbb{R}^2$. A reconstrução é calculada diretamente pelo ângulo "
            r"tangente $\theta(s) = \int_{s_0}^s \kappa(u)\,du$ via quadratura direta."
        )
    else:
        vec_html = f"""
        <div class="vec-item"><span class="vec-tag vec-t">T</span><span class="vec-val" id="hud-vec-t">[{init_tx:.3f}, {init_ty:.3f}, {init_tz:.3f}]</span></div>
        <div class="vec-item"><span class="vec-tag vec-n">N</span><span class="vec-val" id="hud-vec-n">[{init_nx:.3f}, {init_ny:.3f}, {init_nz:.3f}]</span></div>
        <div class="vec-item"><span class="vec-tag vec-b">B</span><span class="vec-val" id="hud-vec-b">[{init_bx:.3f}, {init_by:.3f}, {init_bz:.3f}]</span></div>
        """
        switches = [
            ("Curva r(s)", COLOR_CURVE, 0, True),
            ("Ponto Ativo r(s)", COLOR_POINT, 1, True),
            ("Vetor Tangente T", COLOR_TANGENT, 2, True),
            ("Vetor Normal N", COLOR_NORMAL, 3, True),
            ("Vetor Binormal B", COLOR_BINORMAL, 4, True),
            ("Reta Tangente L_T", "rgba(16, 185, 129, 0.7)", 5, True),
            ("Plano Osculador (T, N)", "rgba(37, 99, 235, 0.7)", 6, True),
            ("Plano Normal (N, B)", "rgba(239, 68, 68, 0.7)", 7, True),
            ("Plano Retificante (T, B)", "rgba(99, 102, 241, 0.7)", 8, True),
            ("Círculo Osculador", COLOR_CIRCLE, 9, True),
        ]
        theory_summary = (
            r"Pelo <b>Teorema Fundamental das Curvas no $\mathbb{R}^3$</b>, funções de curvatura "
            r"$\kappa(s) > 0$ e torção $\tau(s)$ determinam a curva de modo único a menos "
            r"de movimentos rígidos euclidianos ($\mathrm{SE}(3)$). A solução é integrada a partir "
            r"do sistema diferencial linear de Frenet-Serret em $\mathrm{SO}(3)$."
        )

    switches_html = []
    for name, col, idx, chk in switches:
        checked_attr = "checked" if chk else ""
        switches_html.append(
            f'<label class="switch-row">'
            f'<div class="switch-left"><span class="color-badge" style="background-color: {col};"></span><span class="switch-name">{name}</span></div>'
            f'<div class="toggle-wrap"><input type="checkbox" {checked_attr} onchange="toggleTraceVisibility({idx}, this.checked)"><span class="toggle-slider"></span></div>'
            f'</label>'
        )
    switches_markup = "\n".join(switches_html)

    formulas = _build_curve_formulas(curve_res, is_planar)

    assoc_formulas: dict[str, list[str]] = {"evolute": [], "involute": []}
    if getattr(curve_res, "classification", "") not in ("circulo", "reta"):
        if is_planar:
            assoc_formulas["evolute"] = [r"\kappa_E = \frac{\kappa^3}{|\kappa'|},\quad \tau_E = 0"]
            assoc_formulas["involute"] = [r"\kappa_I = \frac{1}{s_1 - s},\quad \tau_I = 0"]
        else:
            assoc_formulas["evolute"] = [r"E'(s) = -\frac{\kappa'}{\kappa^2} N + \frac{\tau}{\kappa} B"]
            assoc_formulas["involute"] = [
                r"\kappa_I = \frac{\sqrt{\kappa^2 + \tau^2}}{(s_1 - s)\,\kappa},\quad "
                r"\tau_I = \frac{\kappa\tau' - \kappa'\tau}{(s_1 - s)\,\kappa\,(\kappa^2 + \tau^2)}"
            ]

    def _formula(title: str, tag: str, tag_cls: str, math_id: str, tex: str, *aux: str) -> str:
        aux_html = "".join(f'<div class="tf-formula-math">${a}$</div>' for a in aux if a)
        return (
            f'<div class="tf-formula">'
            f'<div class="tf-formula-head"><span>{title}</span><span class="tf-tag {tag_cls}">{tag}</span></div>'
            f'<div class="tf-formula-math" id="{math_id}">${tex}$</div>'
            f"{aux_html}</div>"
        )

    binormal_formula_html = ""
    sigma_hud_row = ""
    if not is_planar:
        binormal_formula_html = _formula(
            "Vetor binormal", "B", "tf-tag--b", "math-vec-b", formulas["vec_b"]
        )
        sigma_hud_row = (
            '<div class="tf-readout"><span class="tf-readout-label">Raio de torção <em>σ</em>(<em>s</em>)</span>'
            f'<span class="tf-readout-value" id="hud-sigma">{init_sigma_str}</span></div>'
        )

    def _vecrow(tag: str, tag_cls: str, elem_id: str, comps: list[float]) -> str:
        val = "(" + ", ".join(f"{c:.3f}" for c in comps) + ")"
        return (
            f'<div class="tf-vecrow"><span class="tf-tag {tag_cls}">{tag}</span>'
            f'<span class="tf-readout-value" id="{elem_id}">{val}</span></div>'
        )

    if is_planar:
        vec_html = (
            _vecrow("T", "tf-tag--t", "hud-vec-t", [init_tx, init_ty])
            + _vecrow("N", "tf-tag--n", "hud-vec-n", [init_nx, init_ny])
        )
        # (label, dot class, trace index, visible by default)
        switches = [
            ("Curva r(s)", "", 0, True),
            ("Ponto ativo r(s)", "tf-dot--p", 1, True),
            ("Vetor tangente T", "tf-dot--t", 2, True),
            ("Vetor normal N", "tf-dot--n", 3, True),
            ("Reta tangente L_T", "tf-dot--t", 4, True),
            ("Reta normal L_N", "tf-dot--n", 5, True),
            ("Círculo osculador", "tf-dot--p", 6, True),
            ("Evoluta E(s)", "tf-dot--e", 7, True),
            ("Involuta I(s)", "tf-dot--i", 8, True),
        ]
        legend_items = [
            ("", "r(s)"), ("tf-dot--t", "T"), ("tf-dot--n", "N"), ("tf-dot--p", "círculo osculador"),
            ("tf-dot--e", "evoluta"), ("tf-dot--i", "involuta"),
        ]
        theory_summary = (
            r"Pelo <b>Teorema Fundamental das Curvas Planas</b>, a curvatura com sinal "
            r"$\kappa(s)$ determina a curva de modo único a menos de rotações e translações "
            r"no plano $\mathbb{R}^2$. A reconstrução é calculada diretamente pelo ângulo "
            r"tangente $\theta(s) = \int_{s_0}^s \kappa(u)\,du$ via quadratura direta."
        )
    else:
        vec_html = (
            _vecrow("T", "tf-tag--t", "hud-vec-t", [init_tx, init_ty, init_tz])
            + _vecrow("N", "tf-tag--n", "hud-vec-n", [init_nx, init_ny, init_nz])
            + _vecrow("B", "tf-tag--b", "hud-vec-b", [init_bx, init_by, init_bz])
        )
        # Planes take the hue of the vector they are perpendicular to.
        switches = [
            ("Curva r(s)", "", 0, True),
            ("Ponto ativo r(s)", "tf-dot--p", 1, True),
            ("Vetor tangente T", "tf-dot--t", 2, True),
            ("Vetor normal N", "tf-dot--n", 3, True),
            ("Vetor binormal B", "tf-dot--b", 4, not is_planar),
            ("Reta tangente L_T", "tf-dot--t", 5, True),
            ("Plano osculador (T, N)", "tf-dot--b", 6, True),
            ("Plano normal (N, B)", "tf-dot--t", 7, not is_planar),
            ("Plano retificante (T, B)", "tf-dot--n", 8, not is_planar),
            ("Círculo osculador", "tf-dot--p", 9, True),
            ("Evoluta E(s)", "tf-dot--e", 10, True),
            ("Involuta I(s)", "tf-dot--i", 11, True),
        ]
        legend_items = [
            ("", "r(s)"), ("tf-dot--t", "T"), ("tf-dot--n", "N"), ("tf-dot--b", "B"),
            ("tf-dot--p", "círculo osculador"), ("tf-dot--e", "evoluta"), ("tf-dot--i", "involuta"),
        ]
        theory_summary = (
            r"Pelo <b>Teorema Fundamental das Curvas no $\mathbb{R}^3$</b>, funções de curvatura "
            r"$\kappa(s) > 0$ e torção $\tau(s)$ determinam a curva de modo único a menos "
            r"de movimentos rígidos euclidianos ($\mathrm{SE}(3)$). A solução é integrada a partir "
            r"do sistema diferencial linear de Frenet-Serret em $\mathrm{SO}(3)$."
        )

    switches_markup = "\n".join(
        f'<label class="tf-toggle"><span class="tf-toggle-left"><span class="tf-dot {dot}"></span>{name}</span>'
        f'<span class="tf-switch"><input type="checkbox" {"checked" if chk else ""} aria-label="{name}" '
        f'onchange="toggleTraceVisibility({idx}, this.checked)"><span class="tf-switch-track"></span></span></label>'
        for name, dot, idx, chk in switches
    )
    legend_markup = "".join(
        f'<span><span class="tf-dot {dot}"></span>{label}</span>' for dot, label in legend_items
    )

    m0_assoc = hud_metrics[0] if hud_metrics else {}

    def _assoc_value(key: str) -> str:
        v = m0_assoc.get(key)
        return "—" if v is None else f"{v:.3f}"

    def _assoc_rho(key: str) -> str:
        v = m0_assoc.get(key)
        if v is None:
            return "—"
        return "∞" if abs(v) < 1e-5 else f"{1.0 / abs(v):.3f}"

    def _assoc_block(tag: str, tag_cls: str, name: str, suffix: str, pos_id: str, pos_str: str) -> str:
        torsion_init = "0.000 (plana)" if is_planar else _assoc_value(f"t{suffix}")
        sigma_row = ""
        if not is_planar:
            sigma_row = (
                f'<div class="tf-readout"><span class="tf-readout-label">Raio de torção <em>σ</em><sub>{tag}</sub></span>'
                f'<span class="tf-readout-value" id="hud-sigma-{suffix.lower()}">{_assoc_rho(f"t{suffix}")}</span></div>'
            )
        return (
            f'<div class="tf-vecrow"><span class="tf-tag {tag_cls}">{tag}</span>'
            f'<span class="tf-readout-label">{name}</span></div>'
            '<div class="tf-readouts">'
            f'<div class="tf-readout"><span class="tf-readout-label">Posição <em>{tag}</em>(<em>s</em>)</span><span class="tf-readout-value" id="{pos_id}">{pos_str}</span></div>'
            f'<div class="tf-readout"><span class="tf-readout-label">Curvatura <em>κ</em><sub>{tag}</sub></span><span class="tf-readout-value" id="hud-kappa-{suffix.lower()}">{_assoc_value(f"k{suffix}")}</span></div>'
            f'<div class="tf-readout"><span class="tf-readout-label">Torção <em>τ</em><sub>{tag}</sub></span><span class="tf-readout-value" id="hud-tau-{suffix.lower()}">{torsion_init}</span></div>'
            f'<div class="tf-readout"><span class="tf-readout-label">Raio de curvatura <em>ρ</em><sub>{tag}</sub></span><span class="tf-readout-value" id="hud-rho-{suffix.lower()}">{_assoc_rho(f"k{suffix}")}</span></div>'
            f"{sigma_row}"
            f'<div class="tf-readout"><span class="tf-readout-label">Rapidez |<em>{tag}</em>′(<em>s</em>)|</span><span class="tf-readout-value" id="hud-speed-{suffix.lower()}">{_assoc_value(f"v{suffix}")}</span></div>'
            "</div>"
        )

    assoc_panel = _assoc_block("E", "tf-tag--e", "Evoluta", "E", "hud-evolute", init_evo_str) + _assoc_block(
        "I", "tf-tag--i", "Involuta", "I", "hud-involute", init_inv_str
    )

    kappa_math = rf"$\kappa(s) = {kappa_tex}$"
    tau_math = rf"$\tau(s) = {tau_tex}$"
    interval_math = rf"$s \in [{s0:.2f}, {s1:.2f}]$"
    subtitle = title or "Teorema Fundamental de Curvas"

    theme_json = json.dumps(
        {name: {"traces": t["traces"], "layout": t["layout"]} for name, t in _THEME.items()}
    )
    roles_json = json.dumps(_TRACE_ROLES_2D if is_planar else _TRACE_ROLES_3D)
    tokens_css = _read_design_asset("tokens.css")
    bundle_css = _read_design_asset("components/bundle.css")

    # Post-script JavaScript to inject inside Plotly.newPlot.then(...)
    post_script_js = f"""
window.CURVE_METRICS = {metrics_json};
var isPlanar = {"true" if is_planar else "false"};
var totalFrames = {num_frames};
var curFrame = 0;
var isPlaying = false;
var playTimer = null;
var lastTick = null;
var animSpeed = 1.0;
var ICON_PLAY = '<path d="M4.5 2.6v10.8L13 8z"/>';
var ICON_PAUSE = '<path d="M4 2.8h2.8v10.4H4zM9.2 2.8H12v10.4H9.2z"/>';
var ICON_MOON = '<path d="M13 9.6A5.4 5.4 0 0 1 6.4 3a5.4 5.4 0 1 0 6.6 6.6z"/>';
var ICON_SUN = '<circle cx="8" cy="8" r="2.6"/><path d="M8 1.8v1.6M8 12.6v1.6M1.8 8h1.6M12.6 8h1.6M3.6 3.6l1.1 1.1M11.3 11.3l1.1 1.1M3.6 12.4l1.1-1.1M11.3 4.7l1.1-1.1"/>';
var TRIEDRO_THEME = {theme_json};
var TRACE_ROLES = {roles_json};

function updateHUDMetrics(idx) {{
  if (!window.CURVE_METRICS || !window.CURVE_METRICS[idx]) return;
  curFrame = idx;
  var m = window.CURVE_METRICS[idx];
  var sElem = document.getElementById("hud-s");
  var rElem = document.getElementById("hud-r");
  var kElem = document.getElementById("hud-kappa");
  var tElem = document.getElementById("hud-tau");
  var rhoElem = document.getElementById("hud-rho");
  var sigElem = document.getElementById("hud-sigma");
  var evoElem = document.getElementById("hud-evolute");
  var invElem = document.getElementById("hud-involute");

  if (sElem) sElem.innerText = m.s.toFixed(3);
  if (rElem) {{
    if (m.is_planar) {{
      rElem.innerText = "(" + m.x.toFixed(2) + ", " + m.y.toFixed(2) + ")";
    }} else {{
      rElem.innerText = "(" + m.x.toFixed(2) + ", " + m.y.toFixed(2) + ", " + m.z.toFixed(2) + ")";
    }}
  }}
  if (kElem) kElem.innerText = m.kappa.toFixed(3);
  if (tElem) {{
    tElem.innerText = m.is_planar ? "0.000 (plana)" : m.tau.toFixed(3);
  }}
  if (rhoElem) rhoElem.innerText = m.rho === null ? "∞" : m.rho.toFixed(3);
  if (sigElem && !m.is_planar) {{
    sigElem.innerText = m.sigma === null ? "∞" : m.sigma.toFixed(3);
  }}

  if (evoElem) {{
    if (m.Ex === null || m.Ex === undefined) {{
      evoElem.innerText = "—";
    }} else if (m.is_planar) {{
      evoElem.innerText = "(" + m.Ex.toFixed(2) + ", " + m.Ey.toFixed(2) + ")";
    }} else {{
      evoElem.innerText = "(" + m.Ex.toFixed(2) + ", " + m.Ey.toFixed(2) + ", " + m.Ez.toFixed(2) + ")";
    }}
  }}

  if (invElem) {{
    if (m.Ix === null || m.Ix === undefined) {{
      invElem.innerText = "—";
    }} else if (m.is_planar) {{
      invElem.innerText = "(" + m.Ix.toFixed(2) + ", " + m.Iy.toFixed(2) + ")";
    }} else {{
      invElem.innerText = "(" + m.Ix.toFixed(2) + ", " + m.Iy.toFixed(2) + ", " + m.Iz.toFixed(2) + ")";
    }}
  }}

  // Evolute / involute as curves in their own right
  function fmtOpt(v) {{ return v === null || v === undefined ? "\u2014" : v.toFixed(3); }}
  function fmtRho(v) {{
    if (v === null || v === undefined) return "\u2014";
    return Math.abs(v) < 1e-5 ? "\u221e" : (1 / Math.abs(v)).toFixed(3);
  }}
  [["e", "E"], ["i", "I"]].forEach(function(p) {{
    var sfx = p[0], up = p[1];
    var set = function(id, txt) {{ var el = document.getElementById(id); if (el) el.innerText = txt; }};
    set("hud-kappa-" + sfx, fmtOpt(m["k" + up]));
    set("hud-tau-" + sfx, m.is_planar ? "0.000 (plana)" : fmtOpt(m["t" + up]));
    set("hud-rho-" + sfx, fmtRho(m["k" + up]));
    set("hud-sigma-" + sfx, fmtRho(m["t" + up]));
    set("hud-speed-" + sfx, fmtOpt(m["v" + up]));
  }});

  // Update vectors
  var vt = document.getElementById("hud-vec-t");
  var vn = document.getElementById("hud-vec-n");
  var vb = document.getElementById("hud-vec-b");
  if (vt && m.Tx !== undefined) {{
    vt.innerText = m.is_planar
      ? "(" + m.Tx.toFixed(3) + ", " + m.Ty.toFixed(3) + ")"
      : "(" + m.Tx.toFixed(3) + ", " + m.Ty.toFixed(3) + ", " + m.Tz.toFixed(3) + ")";
  }}
  if (vn && m.Nx !== undefined) {{
    vn.innerText = m.is_planar
      ? "(" + m.Nx.toFixed(3) + ", " + m.Ny.toFixed(3) + ")"
      : "(" + m.Nx.toFixed(3) + ", " + m.Ny.toFixed(3) + ", " + m.Nz.toFixed(3) + ")";
  }}
  if (vb && m.Bx !== undefined && !m.is_planar) {{
    vb.innerText = "(" + m.Bx.toFixed(3) + ", " + m.By.toFixed(3) + ", " + m.Bz.toFixed(3) + ")";
  }}

  // Update dock slider and readout
  var slider = document.getElementById("dock-slider");
  var sVal = document.getElementById("dock-s-val");
  var sPct = document.getElementById("dock-pct");
  var trackFill = document.getElementById("dock-track-fill");
  if (slider) slider.value = idx;
  if (sVal) sVal.innerText = m.s.toFixed(3);
  var pct = totalFrames > 1 ? Math.round((idx / (totalFrames - 1)) * 100) : 0;
  if (sPct) sPct.innerText = pct + "%";
  if (trackFill) trackFill.style.width = pct + "%";
}}

// Frame data (moving traces 1..n) indexed by frame name, read once from Plotly.
var frameCache = null;
function getFrameCache(gd) {{
  if (frameCache) return frameCache;
  var list = (gd._transitionData && gd._transitionData._frames) || [];
  frameCache = {{}};
  list.forEach(function(f) {{ frameCache[f.name] = f; }});
  return frameCache;
}}

// Move the active point and apparatus with ONE lightweight restyle of the moving
// traces. Plotly.animate + relayout redrew the whole scene on every tick, which kept
// the main thread busy and rebuilt the scene under the cursor while dragging.
function applyFrame(gd, idx) {{
  var f = getFrameCache(gd)["frame_" + idx];
  if (!f) {{
    Plotly.animate(gd, ["frame_" + idx], {{
      mode: "immediate",
      frame: {{ duration: 0, redraw: !isPlanar }},
      transition: {{ duration: 0 }}
    }}).catch(function() {{}});
    return;
  }}
  var upd = {{ x: [], y: [] }};
  if (!isPlanar) upd.z = [];
  f.data.forEach(function(tr) {{
    upd.x.push(tr.x);
    upd.y.push(tr.y);
    if (!isPlanar) upd.z.push(tr.z);
  }});
  syncLiveView(gd);
  Plotly.restyle(gd, upd, f.traces);
}}

// Every update re-applies the view stored in the layout (3D camera, 2D axis ranges), which
// only changes on mouse-up; mid-drag that snapped the view back on each playback tick.
// Copy the live view into the layout first so updates keep what the user is dragging.
function syncLiveView(gd) {{
  try {{
    if (isPlanar) {{
      ["xaxis", "yaxis"].forEach(function(k) {{
        var ax = gd._fullLayout[k];
        if (ax && ax.range) gd.layout[k].range = ax.range.slice();
      }});
    }} else {{
      var scene = gd._fullLayout.scene._scene;
      if (scene && scene.getCamera) gd.layout.scene.camera = scene.getCamera();
    }}
  }} catch (e) {{}}
}}

function goToFrame(frameIdx) {{
  var gd = document.getElementById("fundamental_curve_plot");
  if (!gd) return;
  frameIdx = Math.max(0, Math.min(totalFrames - 1, frameIdx));
  curFrame = frameIdx;
  applyFrame(gd, frameIdx);
  updateHUDMetrics(frameIdx);
}}

// Playback advances by elapsed time (45 ms per frame at 1x) on requestAnimationFrame,
// so a slow frame never queues extra work behind the user's drag.
function playLoop(now) {{
  if (!isPlaying) return;
  if (lastTick === null) lastTick = now;
  var stepMs = 45 / animSpeed;
  var steps = Math.floor((now - lastTick) / stepMs);
  if (steps >= 1) {{
    lastTick += steps * stepMs;
    goToFrame((curFrame + steps) % totalFrames);
  }}
  playTimer = requestAnimationFrame(playLoop);
}}

function togglePlay() {{
  var btn = document.getElementById("btn-dock-play");
  var icon = document.getElementById("play-icon");
  if (isPlaying) {{
    isPlaying = false;
    cancelAnimationFrame(playTimer);
    playTimer = null;
    if (icon) icon.innerHTML = ICON_PLAY;
    if (btn) btn.classList.remove("active");
  }} else {{
    isPlaying = true;
    lastTick = null;
    if (icon) icon.innerHTML = ICON_PAUSE;
    if (btn) btn.classList.add("active");
    playTimer = requestAnimationFrame(playLoop);
  }}
}}

function setPlaybackSpeed(btn) {{
  var speeds = [0.5, 1.0, 1.5, 2.0];
  var currIdx = speeds.indexOf(animSpeed);
  var nextIdx = (currIdx + 1) % speeds.length;
  animSpeed = speeds[nextIdx];
  if (btn) btn.innerText = animSpeed + "×";
}}

function toggleTraceVisibility(traceIdx, isVisible) {{
  var gd = document.getElementById("fundamental_curve_plot");
  if (!gd) return;
  Plotly.restyle(gd, {{ visible: isVisible ? true : "legendonly" }}, [traceIdx]);
}}
// This script runs inside Plotly's .then() closure; the switches' inline onchange
// handlers can only see globals, so expose the function explicitly.
window.toggleTraceVisibility = toggleTraceVisibility;

function parseRGBA(c) {{
  var m = /^rgba?\\(([^)]+)\\)$/.exec(c);
  if (!m) return {{ color: c, alpha: 1 }};
  var p = m[1].split(",").map(function(x) {{ return x.trim(); }});
  return {{
    color: "rgb(" + p[0] + ", " + p[1] + ", " + p[2] + ")",
    alpha: p.length > 3 ? parseFloat(p[3]) : 1
  }};
}}

function restyleRole(gd, idx, role, t) {{
  var u = {{}};
  if (role === "curve" || role === "tangent" || role === "normal" || role === "binormal") {{
    u["line.color"] = t.color;
    u["marker.color"] = t.color;
  }} else if (role === "active_point") {{
    u["marker.color"] = t.color;
    u["marker.line.color"] = t.outline;
  }} else if (role === "tangent_line" || role === "normal_line" || role === "osculating_circle" || role === "evolute" || role === "involute") {{
    u["line.color"] = t.color;
  }} else if (role.indexOf("plane_") === 0) {{
    var c = parseRGBA(t.color);
    u["color"] = c.color;
    u["opacity"] = c.alpha;
  }} else {{
    return;
  }}
  Plotly.restyle(gd, u, [idx]);
}}

function applyTheme(name) {{
  var th = TRIEDRO_THEME[name];
  if (!th) return;
  document.documentElement.setAttribute("data-theme", name);
  var icon = document.getElementById("theme-icon");
  if (icon) icon.innerHTML = name === "dark" ? ICON_SUN : ICON_MOON;
  try {{ localStorage.setItem("triedro-theme", name); }} catch (e) {{}}

  var gd = document.getElementById("fundamental_curve_plot");
  if (!gd || !gd.data) return;
  var L = th.layout;
  var rel = {{
    "font.color": L.font.color,
    "hoverlabel.bgcolor": L.hoverlabel.bgcolor,
    "hoverlabel.bordercolor": L.hoverlabel.bordercolor,
    "hoverlabel.font.color": L.hoverlabel.font.color,
    "modebar.color": L.modebar.color,
    "modebar.activecolor": L.modebar.activecolor
  }};
  function axisUpdate(prefix, a) {{
    rel[prefix + ".gridcolor"] = a.gridcolor;
    rel[prefix + ".zerolinecolor"] = a.zerolinecolor;
    rel[prefix + ".linecolor"] = a.linecolor;
    rel[prefix + ".tickfont.color"] = a.tickfont.color;
  }}
  if (isPlanar) {{
    axisUpdate("xaxis", L.xaxis_2d);
    axisUpdate("yaxis", L.yaxis_2d);
  }} else {{
    ["xaxis", "yaxis", "zaxis"].forEach(function(k) {{ axisUpdate("scene." + k, L.scene.axis); }});
  }}
  Plotly.relayout(gd, rel);
  TRACE_ROLES.forEach(function(role, idx) {{ restyleRole(gd, idx, role, th.traces[role]); }});
}}

function toggleTheme() {{
  var current = document.documentElement.getAttribute("data-theme") || "light";
  applyTheme(current === "light" ? "dark" : "light");
}}

function restoreSavedTheme() {{
  try {{
    if (localStorage.getItem("triedro-theme") === "dark") applyTheme("dark");
  }} catch (e) {{}}
}}

function toggleSidebar() {{
  var sb = document.getElementById("sidebar");
  var openBtn = document.getElementById("sidebar-expand-btn");
  if (!sb) return;
  sb.classList.toggle("collapsed");
  var isCollapsed = sb.classList.contains("collapsed");
  if (openBtn) openBtn.style.display = isCollapsed ? "flex" : "none";
  var startTime = performance.now();
  var duration = 320;
  function stepResize(now) {{
    var gd = document.getElementById("fundamental_curve_plot");
    if (gd) Plotly.Plots.resize(gd);
    if (now - startTime < duration) {{
      requestAnimationFrame(stepResize);
    }}
  }}
  requestAnimationFrame(stepResize);
}}

var gd = document.getElementById("fundamental_curve_plot");
if (gd) {{
  // 1. plotly_click: snap slider and apparatus immediately to clicked curve vertex
  gd.on("plotly_click", function(eventData) {{
    if (!eventData || !eventData.points || eventData.points.length === 0) return;
    var pt = eventData.points[0];
    if (pt.curveNumber === 0) {{
      var frameIdx = (pt.customdata && pt.customdata[1] !== undefined)
        ? parseInt(pt.customdata[1], 10)
        : pt.pointNumber;
      goToFrame(frameIdx);
    }}
  }});

  // 2. plotly_sliderchange: update HUD when user scrubs the slider
  gd.on("plotly_sliderchange", function(e) {{
    if (e && e.slider) {{
      updateHUDMetrics(e.slider.active);
    }}
  }});

  // 3. plotly_animatingframe: update HUD during automatic play animation
  gd.on("plotly_animatingframe", function(e) {{
    if (e && e.name) {{
      var idx = parseInt(e.name.replace("frame_", ""), 10);
      if (!isNaN(idx)) updateHUDMetrics(idx);
    }}
  }});

  // 4. window.resize: ensure 100vw x 100vh responsiveness
  window.addEventListener("resize", function() {{
    Plotly.Plots.resize(gd);
  }});
}}

function initDockAndSidebar() {{
  var slider = document.getElementById("dock-slider");
  if (slider) {{
    slider.addEventListener("input", function() {{
      goToFrame(parseInt(this.value, 10));
    }});
  }}
  var btnFirst = document.getElementById("btn-dock-first");
  if (btnFirst) btnFirst.addEventListener("click", function() {{ goToFrame(0); }});
  var btnPrev = document.getElementById("btn-dock-prev");
  if (btnPrev) btnPrev.addEventListener("click", function() {{ goToFrame(curFrame - 1); }});
  var btnPlay = document.getElementById("btn-dock-play");
  if (btnPlay) btnPlay.addEventListener("click", togglePlay);
  var btnNext = document.getElementById("btn-dock-next");
  if (btnNext) btnNext.addEventListener("click", function() {{ goToFrame(curFrame + 1); }});
  var btnLast = document.getElementById("btn-dock-last");
  if (btnLast) btnLast.addEventListener("click", function() {{ goToFrame(totalFrames - 1); }});
  var btnSpeed = document.getElementById("btn-dock-speed");
  if (btnSpeed) btnSpeed.addEventListener("click", function() {{ setPlaybackSpeed(this); }});

  var themeBtn = document.getElementById("theme-toggle-btn");
  if (themeBtn) themeBtn.addEventListener("click", toggleTheme);
  var sbCloseBtn = document.getElementById("sidebar-toggle-btn");
  if (sbCloseBtn) sbCloseBtn.addEventListener("click", toggleSidebar);
  var sbOpenBtn = document.getElementById("sidebar-expand-btn");
  if (sbOpenBtn) sbOpenBtn.addEventListener("click", toggleSidebar);

  restoreSavedTheme();

  if (typeof renderAllKaTeX === "function") {{
    renderAllKaTeX();
  }} else if (window.renderMathInElement) {{
    renderMathInElement(document.body, {{
      delimiters: [
        {{ left: "$$", right: "$$", display: true }},
        {{ left: "$", right: "$", display: false }}
      ],
      throwOnError: false
    }});
  }}
}}

restoreSavedTheme();

if (document.readyState === "loading") {{
  document.addEventListener("DOMContentLoaded", initDockAndSidebar);
}} else {{
  initDockAndSidebar();
}}
"""

    # Generate inner Plotly HTML snippet
    plotly_snippet = fig.to_html(
        include_plotlyjs=include_plotlyjs,
        full_html=False,
        div_id="fundamental_curve_plot",
        post_script=post_script_js,
        auto_play=False,  # playback starts only from the dock's play button
    )

    # Fullscreen responsive HTML template: Triedro design system (tokens + tf-* components)
    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <!-- KaTeX for mathematical rendering -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" onload="renderAllKaTeX()"></script>
  <!-- Copying a rendered formula yields its TeX source instead of one fragment per line -->
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/copy-tex.min.js"></script>
  <script>
    function renderAllKaTeX() {{
      if (typeof renderMathInElement === "function") {{
        renderMathInElement(document.body, {{
          delimiters: [
            {{ left: "$$", right: "$$", display: true }},
            {{ left: "$", right: "$", display: false }}
          ],
          throwOnError: false
        }});
      }}
    }}
    if (document.readyState === "loading") {{
      document.addEventListener("DOMContentLoaded", renderAllKaTeX);
    }} else {{
      renderAllKaTeX();
    }}
    window.addEventListener("load", renderAllKaTeX);
    var katexTries = 0;
    var katexTimer = setInterval(function() {{
      katexTries++;
      if (typeof renderMathInElement === "function") {{
        renderAllKaTeX();
        clearInterval(katexTimer);
      }} else if (katexTries > 50) {{
        clearInterval(katexTimer);
      }}
    }}, 80);
  </script>
  <!-- Triedro design system: component classes (bundle.css) and theme tokens (tokens.css) -->
  <style>
{bundle_css}
  </style>
  <style>
{tokens_css}
  </style>
  <style>
    /* Page frame: full-viewport shell around the Triedro components */
    html, body {{
      width: 100vw;
      height: 100vh;
      height: 100dvh;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background-color: var(--canvas);
      user-select: none;
    }}
    #app-layout {{
      display: flex;
      flex-direction: row;
      width: 100vw;
      height: 100vh;
      height: 100dvh;
      position: relative;
      overflow: hidden;
    }}
    /* Main plot container (left); the sidebar pushes it when open */
    #plot-container {{
      flex: 1 1 0%;
      min-width: 0;
      height: 100%;
      position: relative;
      overflow: hidden;
      background: var(--canvas);
    }}
    .plotly-graph-div {{
      width: 100% !important;
      height: 100% !important;
    }}
    @media (max-width: 768px) {{
      .plotly-graph-div {{
        width: 100vw !important;
        height: 100vh !important;
      }}
      .tf-speed {{ display: none; }}
    }}
    /* Collapsible sidebar (right): 300ms slide */
    #sidebar {{
      transition: margin-right 300ms cubic-bezier(.4, 0, .2, 1);
    }}
    #sidebar.collapsed {{
      margin-right: -380px;
    }}
    #hud-card {{
      flex: 1;
      min-height: 0;
      user-select: text;
      -webkit-user-select: text;
    }}
    #sidebar-expand-btn {{
      display: none;
    }}
    .tf-legend {{
      z-index: 5;
      pointer-events: none;
    }}
    /* The dock is the only transport: hide Plotly's native slider and updatemenus */
    .slider-container, .updatemenu-container {{
      display: none !important;
    }}
    .modebar-container {{
      top: 44px !important;
      left: 12px !important;
      right: auto !important;
      opacity: 0.65;
      transition: opacity 150ms cubic-bezier(.4, 0, .2, 1);
    }}
    .modebar-container:hover {{
      opacity: 1;
    }}
    .tf-scrub {{
      width: 190px;
    }}
    .tf-s-pct {{
      margin-left: 4px;
      font-size: 11px;
      color: var(--ink-muted);
    }}
  </style>
</head>
<body>
  <div id="app-layout" class="tf-root">
    <!-- Main Plot Canvas on the Left -->
    <main id="plot-container" class="tf-stage">
      <!-- Floating expand button when the sidebar is collapsed -->
      <div class="tf-expand-slot">
        <button id="sidebar-expand-btn" class="tf-expand" title="Expandir painel" aria-label="Expandir painel">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="12" height="10" rx="2"/><path d="M10 3v10"/></svg>
          <span>Painel</span>
        </button>
      </div>

      {plotly_snippet}

      <div class="tf-legend">{legend_markup}</div>

      <!-- Floating control dock, bottom centre -->
      <div class="tf-dock-slot">
        <div id="control-dock" class="tf-dock">
          <div class="tf-transport">
            <button id="btn-dock-first" class="tf-dockbtn" aria-label="Início" title="Início (s₀)"><svg viewBox="0 0 16 16"><path d="M3 3h1.8v10H3zM13 3v10L5.8 8z"/></svg></button>
            <button id="btn-dock-prev" class="tf-dockbtn" aria-label="Passo anterior" title="Passo anterior"><svg viewBox="0 0 16 16"><path d="M11.5 3v10L4.5 8z"/></svg></button>
            <button id="btn-dock-play" class="tf-dockbtn tf-dockbtn--play" aria-label="Reproduzir ou pausar" title="Reproduzir ou pausar"><svg id="play-icon" viewBox="0 0 16 16"><path d="M4.5 2.6v10.8L13 8z"/></svg></button>
            <button id="btn-dock-next" class="tf-dockbtn" aria-label="Próximo passo" title="Próximo passo"><svg viewBox="0 0 16 16"><path d="M4.5 3v10l7-5z"/></svg></button>
            <button id="btn-dock-last" class="tf-dockbtn" aria-label="Fim" title="Fim (s₁)"><svg viewBox="0 0 16 16"><path d="M11.2 3H13v10h-1.8zM3 3l7.2 5L3 13z"/></svg></button>
          </div>

          <div class="tf-scrub">
            <span class="tf-rail"></span><span class="tf-fill" id="dock-track-fill"></span>
            <span class="tf-ticks"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span>
            <input type="range" id="dock-slider" min="0" max="{num_frames - 1}" value="0" step="1" aria-label="Comprimento de arco s">
          </div>

          <div class="tf-sread">
            <span class="tf-s-var">s</span><span>=</span>
            <span class="tf-s-val" id="dock-s-val">{init_s:.3f}</span>
            <span class="tf-s-max">/ {s1:.3f}</span>
            <span class="tf-s-pct" id="dock-pct">0%</span>
          </div>

          <button id="btn-dock-speed" class="tf-speed" aria-label="Velocidade da reprodução" title="Velocidade da reprodução">1×</button>
        </div>
      </div>
    </main>

    <!-- Collapsible sidebar on the Right -->
    <aside id="sidebar" class="tf-sidebar">
      <header class="tf-sidebar-head">
        <div class="tf-head-row">
          <div class="tf-brand">
            <span class="tf-mark">∫</span>
            <div>
              <h1 class="tf-title">Triedro</h1>
              <p class="tf-subtitle">{subtitle}</p>
            </div>
          </div>
          <div class="tf-actions">
            <button id="theme-toggle-btn" class="tf-iconbtn" title="Alternar tema" aria-label="Alternar tema">
              <svg id="theme-icon" viewBox="0 0 16 16"><path d="M13 9.6A5.4 5.4 0 0 1 6.4 3a5.4 5.4 0 1 0 6.6 6.6z"/></svg>
            </button>
            <button id="sidebar-toggle-btn" class="tf-iconbtn" title="Recolher painel" aria-label="Recolher painel">
              <svg viewBox="0 0 16 16"><rect x="2" y="3" width="12" height="10" rx="2"/><path d="M10 3v10"/></svg>
            </button>
          </div>
        </div>
        <div class="tf-badges">
          <span class="tf-badge tf-badge--class" id="hud-class">{class_label}</span>
          <span class="tf-badge tf-badge--dim">{mode_label}</span>
        </div>
      </header>

      <!-- Scrollable content (id="hud-card" preserved for test compatibility) -->
      <div id="hud-card" class="tf-sidebar-body">
        <section class="tf-panel">
          <h3 class="tf-overline"><span class="tf-sec">§1</span>Fórmulas intrínsecas</h3>
          <div class="tf-formula">
            <div class="tf-formula-head"><span>Curvatura</span><span class="tf-tag tf-tag--r">κ</span></div>
            <div class="tf-formula-math" id="math-kappa">{kappa_math}</div>
          </div>
          <div class="tf-formula">
            <div class="tf-formula-head"><span>Torção</span><span class="tf-tag tf-tag--r">τ</span></div>
            <div class="tf-formula-math" id="math-tau">{tau_math}</div>
          </div>
          <div class="tf-formula">
            <div class="tf-formula-head"><span>Intervalo</span><span class="tf-tag tf-tag--r">s</span></div>
            <div class="tf-formula-math">{interval_math}</div>
          </div>
        </section>

        <section class="tf-panel">
          <h3 class="tf-overline"><span class="tf-sec">§2</span>Reconstrução e curvas associadas</h3>
          {_formula("Curva reconstruída", "r", "tf-tag--r", "math-curve-r", formulas["curve_r"], formulas.get("curve_aux", ""))}
          {_formula("Vetor tangente", "T", "tf-tag--t", "math-vec-t", formulas["vec_t"])}
          {_formula("Vetor normal principal", "N", "tf-tag--n", "math-vec-n", formulas["vec_n"])}
          {binormal_formula_html}
          {_formula("Evoluta (centros de curvatura)", "E", "tf-tag--e", "math-evolute", formulas["evolute"], *assoc_formulas["evolute"])}
          {_formula("Involuta (evolvente de corda)", "I", "tf-tag--i", "math-involute", formulas["involute"], *assoc_formulas["involute"])}
          {_formula("Raios característicos", "ρ", "tf-tag--p", "math-radii", formulas["radii"])}
        </section>

        <section class="tf-panel">
          <h3 class="tf-overline"><span class="tf-sec">§3</span>Grandezas instantâneas</h3>
          <div class="tf-readouts">
            <div class="tf-readout"><span class="tf-readout-label">Comprimento de arco <em>s</em></span><span class="tf-readout-value" id="hud-s">{init_s:.3f}</span></div>
            <div class="tf-readout"><span class="tf-readout-label">Posição <em>r</em>(<em>s</em>)</span><span class="tf-readout-value" id="hud-r">{init_pos_str}</span></div>
            <div class="tf-readout"><span class="tf-readout-label">Curvatura <em>κ</em>(<em>s</em>)</span><span class="tf-readout-value" id="hud-kappa">{init_k:.3f}</span></div>
            <div class="tf-readout"><span class="tf-readout-label">Torção <em>τ</em>(<em>s</em>)</span><span class="tf-readout-value" id="hud-tau">{init_t_str}</span></div>
            <div class="tf-readout"><span class="tf-readout-label">Raio de curvatura <em>ρ</em>(<em>s</em>)</span><span class="tf-readout-value" id="hud-rho">{init_rho}</span></div>
            {sigma_hud_row}
          </div>
          {vec_html}
        </section>

        <section class="tf-panel">
          <h3 class="tf-overline"><span class="tf-sec">§4</span>Evoluta e involuta</h3>
          {assoc_panel}
        </section>

        <section class="tf-panel">
          <h3 class="tf-overline"><span class="tf-sec">§5</span>Visibilidade do aparato</h3>
          {switches_markup}
        </section>

        <section class="tf-panel">
          <h3 class="tf-overline"><span class="tf-sec">§6</span>Fundamentação teórica</h3>
          <p class="tf-prose">{theory_summary}</p>
          <p class="tf-hint">{hint_str}</p>
        </section>
      </div>
    </aside>
  </div>
</body>
</html>
"""

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(full_html, encoding="utf-8")

    return str(out_file)
