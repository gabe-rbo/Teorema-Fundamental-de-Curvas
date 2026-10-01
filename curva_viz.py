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
# Refined scientific color palette (Accessible, elegant, high-contrast)
# ---------------------------------------------------------------------------
COLOR_CURVE = "#2563eb"        # Sapphire Blue
COLOR_POINT = "#f59e0b"        # Amber
COLOR_TANGENT = "#10b981"      # Emerald Green
COLOR_NORMAL = "#ef4444"       # Ruby / Coral Red
COLOR_BINORMAL = "#6366f1"     # Violet / Indigo
COLOR_CIRCLE = "#f59e0b"       # Amber
COLOR_LT_LINE = "rgba(16, 185, 129, 0.45)"
COLOR_LN_LINE = "rgba(239, 68, 68, 0.35)"
COLOR_PLANE_OSC = "rgba(37, 99, 235, 0.22)"
COLOR_PLANE_NORM = "rgba(239, 68, 68, 0.18)"
COLOR_PLANE_RECT = "rgba(99, 102, 241, 0.18)"

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
        marker=dict(size=8, color=COLOR_POINT, symbol="circle"),
        hovertemplate="<b>Ponto Ativo r(s)</b><br>x: %{x:.3f}<br>y: %{y:.3f}<br>z: %{z:.3f}<extra></extra>",
    )
    # Trace 2: Vetor Tangente T
    t2 = go.Scatter3d(
        x=[float(P[0]), float(P[0] + L_vec * T[0])],
        y=[float(P[1]), float(P[1] + L_vec * T[1])],
        z=[float(P[2]), float(P[2] + L_vec * T[2])],
        mode="lines+markers",
        name="Vetor Tangente T",
        line=dict(color=COLOR_TANGENT, width=6),
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
        line=dict(color=COLOR_NORMAL, width=6),
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
        line=dict(color=COLOR_BINORMAL, width=6),
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
        line=dict(color=COLOR_LT_LINE, width=2.5, dash="dash"),
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
        opacity=0.22,
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
        opacity=0.18,
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
        opacity=0.18,
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
        line=dict(color=COLOR_CIRCLE, width=3.5),
        hovertemplate="<b>Círculo Osculador</b><extra></extra>",
    )

    return [t1, t2, t3, t4, t5, t6, t7, t8, t9]


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
        marker=dict(size=10, color=COLOR_POINT, symbol="circle"),
        hovertemplate="<b>Ponto Ativo r(s)</b><br>x: %{x:.3f}<br>y: %{y:.3f}<extra></extra>",
    )
    # Trace 2: Vetor Tangente T
    t2 = go.Scatter(
        x=[float(P[0]), float(P[0] + L_vec * T[0])],
        y=[float(P[1]), float(P[1] + L_vec * T[1])],
        mode="lines+markers",
        name="Vetor Tangente T",
        line=dict(color=COLOR_TANGENT, width=5),
        marker=dict(size=[0, 8], color=COLOR_TANGENT),
        hovertemplate="<b>Vetor Tangente T</b><extra></extra>",
    )
    # Trace 3: Vetor Normal N
    t3 = go.Scatter(
        x=[float(P[0]), float(P[0] + L_vec * N[0])],
        y=[float(P[1]), float(P[1] + L_vec * N[1])],
        mode="lines+markers",
        name="Vetor Normal N",
        line=dict(color=COLOR_NORMAL, width=5),
        marker=dict(size=[0, 8], color=COLOR_NORMAL),
        hovertemplate="<b>Vetor Normal N</b><extra></extra>",
    )
    # Trace 4: Reta Tangente L_T
    t4 = go.Scatter(
        x=lt_x,
        y=lt_y,
        mode="lines",
        name="Reta Tangente L_T",
        line=dict(color=COLOR_LT_LINE, width=2, dash="dash"),
        hovertemplate="<b>Reta Tangente L_T</b><extra></extra>",
    )
    # Trace 5: Reta Normal L_N
    t5 = go.Scatter(
        x=ln_x,
        y=ln_y,
        mode="lines",
        name="Reta Normal L_N",
        line=dict(color=COLOR_LN_LINE, width=2, dash="dot"),
        hovertemplate="<b>Reta Normal L_N</b><extra></extra>",
    )
    # Trace 6: Círculo Osculador
    t6 = go.Scatter(
        x=cx,
        y=cy,
        mode="lines",
        name="Círculo Osculador",
        line=dict(color=COLOR_CIRCLE, width=3),
        hovertemplate="<b>Círculo Osculador</b><extra></extra>",
    )

    return [t1, t2, t3, t4, t5, t6]


def _build_planar_2d_figure(
    curve_data: CurveResult, title: str | None = None
) -> go.Figure:
    """
    Construct a pure 2D interactive Plotly figure for planar curves (tau == 0).
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
        line=dict(color=COLOR_CURVE, width=3.5),
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

    fig_data = [trace_curve, *init_apparatus]

    frames: list[go.Frame] = []
    slider_steps: list[dict[str, Any]] = []
    hud_metrics: list[dict[str, Any]] = []

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
                "font": {"size": 13, "color": "#2563eb"},
            },
            steps=slider_steps,
            pad={"b": 10, "t": 20},
            len=0.88,
            x=0.06,
            y=0.03,
            tickcolor="#64748b",
            font={"color": "#64748b", "size": 10},
            bgcolor="rgba(241, 245, 249, 0.6)",
            activebgcolor="#2563eb",
            bordercolor="rgba(0, 0, 0, 0.1)",
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
        bgcolor="rgba(241, 245, 249, 0.7)",
        bordercolor="rgba(0, 0, 0, 0.15)",
        font={"color": "#0f172a", "size": 12},
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

    class_title = _CLASS_DISPLAY_NAMES.get(
        curve_data.classification,
        curve_data.classification.replace("_", " ").title(),
    )
    final_title = title or f"Teorema Fundamental das Curvas Planas — {class_title} (2D)"

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
        title=dict(
            text=final_title,
            font=dict(color="#0f172a", size=14),
            x=0.5,
            y=0.98,
            xanchor="center",
        ),
        uirevision="constant",
        xaxis=dict(
            title="X",
            range=x_range,
            autorange=False,
            uirevision="constant",
            color="#64748b",
            gridcolor="rgba(0, 0, 0, 0.06)",
            zerolinecolor="rgba(0, 0, 0, 0.15)",
            showgrid=True,
            zeroline=True,
        ),
        yaxis=dict(
            title="Y",
            range=y_range,
            autorange=False,
            uirevision="constant",
            color="#64748b",
            gridcolor="rgba(0, 0, 0, 0.06)",
            zerolinecolor="rgba(0, 0, 0, 0.15)",
            showgrid=True,
            zeroline=True,
            scaleanchor="x",
            scaleratio=1,
        ),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(l=45, r=25, t=35, b=45),
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
        line=dict(color=COLOR_CURVE, width=4),
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
    fig_data = [trace_curve, *init_apparatus]

    # Build animation frames (selective update of traces 1..9)
    frames: list[go.Frame] = []
    slider_steps: list[dict[str, Any]] = []
    hud_metrics: list[dict[str, Any]] = []

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
                "font": {"size": 13, "color": "#2563eb"},
            },
            steps=slider_steps,
            pad={"b": 10, "t": 20},
            len=0.88,
            x=0.06,
            y=0.03,
            tickcolor="#64748b",
            font={"color": "#64748b", "size": 10},
            bgcolor="rgba(241, 245, 249, 0.6)",
            activebgcolor="#2563eb",
            bordercolor="rgba(0, 0, 0, 0.1)",
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
        bgcolor="rgba(241, 245, 249, 0.7)",
        bordercolor="rgba(0, 0, 0, 0.15)",
        font={"color": "#0f172a", "size": 12},
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
        bgcolor="rgba(241, 245, 249, 0.7)",
        bordercolor="rgba(0, 0, 0, 0.15)",
        font={"color": "#0f172a", "size": 11},
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

    class_title = _CLASS_DISPLAY_NAMES.get(
        curve_data.classification,
        curve_data.classification.replace("_", " ").title(),
    )
    final_title = title or f"Teorema Fundamental de Curvas — {class_title}"

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

    x_min_all = min(init_xs)
    x_max_all = max(init_xs)
    y_min_all = min(init_ys)
    y_max_all = max(init_ys)
    z_min_all = min(init_zs)
    z_max_all = max(init_zs)

    span_x = x_max_all - x_min_all
    span_y = y_max_all - y_min_all
    span_z = z_max_all - z_min_all
    max_span = max(span_x, span_y, span_z, 0.1)
    pad = 0.15 * max_span
    x_mid = 0.5 * (x_min_all + x_max_all)
    y_mid = 0.5 * (y_min_all + y_max_all)
    z_mid = 0.5 * (z_min_all + z_max_all)
    half_len = 0.5 * max_span + pad
    x_range = [float(x_mid - half_len), float(x_mid + half_len)]
    y_range = [float(y_mid - half_len), float(y_mid + half_len)]
    z_range = [float(z_mid - half_len), float(z_mid + half_len)]

    fig = go.Figure(data=fig_data, frames=frames)
    fig.update_layout(
        title=dict(
            text=final_title,
            font=dict(color="#0f172a", size=14),
            x=0.5,
            y=0.98,
            xanchor="center",
        ),
        uirevision="constant",
        scene=dict(
            uirevision="constant",
            aspectmode="cube",
            camera=init_camera,
            xaxis=dict(
                title="X",
                range=x_range,
                autorange=False,
                color="#64748b",
                gridcolor="rgba(0, 0, 0, 0.08)",
                zerolinecolor="rgba(0, 0, 0, 0.2)",
                backgroundcolor="rgba(248, 250, 252, 0.5)",
                showbackground=True,
            ),
            yaxis=dict(
                title="Y",
                range=y_range,
                autorange=False,
                color="#64748b",
                gridcolor="rgba(0, 0, 0, 0.08)",
                zerolinecolor="rgba(0, 0, 0, 0.2)",
                backgroundcolor="rgba(248, 250, 252, 0.5)",
                showbackground=True,
            ),
            zaxis=dict(
                title="Z",
                range=z_range,
                autorange=False,
                color="#64748b",
                gridcolor="rgba(0, 0, 0, 0.08)",
                zerolinecolor="rgba(0, 0, 0, 0.2)",
                backgroundcolor="rgba(248, 250, 252, 0.5)",
                showbackground=True,
            ),
        ),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(l=0, r=0, t=20, b=0),
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
            "curve_desc": r"Círculo euclidiano no plano $\mathbb{R}^2$ de raio constante $R = 1/\kappa$.",
            "vec_t": r"T(s) = \left( \cos(\kappa s),\, \sin(\kappa s) \right) = \frac{dr}{ds}",
            "vec_n": r"N(s) = \left( -\sin(\kappa s),\, \cos(\kappa s) \right) = J \cdot T(s)",
            "vec_b": "",
            "evolute": r"E(s) = \left( 0,\, \frac{1}{\kappa} \right)",
            "evolute_desc": r"A evoluta colapsa em um ponto fixo: o centro de curvatura da circunferência.",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "involute_desc": r"Evolvente da circunferência gerada pelo desenrolamento de corda a partir de $s_1$.",
            "radii": r"\rho(s) = \frac{1}{\kappa} = R, \quad \sigma(s) = \infty",
        }
    elif cls == "reta":
        return {
            "curve_r": r"r(s) = r(s_0) + s\,T_0",
            "curve_desc": r"Reta euclidiana gerada por curvatura identicamente nula ($\kappa \equiv 0$).",
            "vec_t": r"T(s) = T_0 = \text{const}",
            "vec_n": r"N(s) = N_0 = \text{const}",
            "vec_b": r"B(s) = B_0 = \text{const}" if not is_planar else "",
            "evolute": r"E(s) \to \infty",
            "evolute_desc": r"Para retas ($\kappa = 0$), o raio de curvatura é infinito e a evoluta é imprópria.",
            "involute": r"I(s) = r(s_1) = \text{const}",
            "involute_desc": r"A involuta da reta colapsa na extremidade final $r(s_1)$.",
            "radii": r"\rho(s) = \infty" + (r", \quad \sigma(s) = \infty" if not is_planar else ""),
        }
    elif cls == "helice_circular":
        return {
            "curve_r": r"r(s) = \left( \frac{\kappa}{\omega^2}\big(1 - \cos(\omega s)\big),\, \frac{\kappa}{\omega^2}\sin(\omega s),\, \frac{\tau}{\omega} s \right)",
            "curve_desc": r"Hélice circular enrolada sobre cilindro de raio $R = \frac{\kappa}{\kappa^2 + \tau^2}$ e passo $P = \frac{2\pi\tau}{\kappa^2 + \tau^2}$, com $\omega = \sqrt{\kappa^2 + \tau^2}$.",
            "vec_t": r"T(s) = \left( \frac{\kappa}{\omega}\sin(\omega s),\, \frac{\kappa}{\omega}\cos(\omega s),\, \frac{\tau}{\omega} \right)",
            "vec_n": r"N(s) = \left( \cos(\omega s),\, -\sin(\omega s),\, 0 \right)",
            "vec_b": r"B(s) = \left( \frac{\tau}{\omega}\sin(\omega s),\, \frac{\tau}{\omega}\cos(\omega s),\, -\frac{\kappa}{\omega} \right)",
            "evolute": r"E(s) = r(s) + \frac{1}{\kappa} N(s)",
            "evolute_desc": r"Evoluta da hélice é outra hélice circular coaxial com raio $R_E = \frac{\tau^2}{\kappa(\kappa^2 + \tau^2)}$.",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "involute_desc": r"Involuta (evolvente) gerada pelo desenrolamento da curva espacial a partir de $s_1$.",
            "radii": r"\rho = \frac{1}{\kappa}, \quad \sigma = \frac{1}{\tau} \quad (\text{constantes})",
        }
    elif cls == "helice_cilindrica_geral":
        return {
            "curve_r": r"r(s) = r(s_0) + \int_{s_0}^s T(u)\,du",
            "curve_desc": r"Hélice cilíndrica geral satisfazendo o Teorema de Lancret: $\frac{\tau(s)}{\kappa(s)} = c = \text{const} \iff$ reta tangente forma ângulo constante com geratriz fixa.",
            "vec_t": r"T'(s) = \kappa(s) N(s), \quad \langle T(s), u_0 \rangle = \cos\alpha",
            "vec_n": r"N(s) = \frac{T'(s)}{\kappa(s)} = \frac{1}{\kappa(s)} \frac{dT}{ds}",
            "vec_b": r"B(s) = T(s) \times N(s)",
            "evolute": r"E(s) = r(s) + \frac{1}{\kappa(s)} N(s)",
            "evolute_desc": r"Locus dos centros dos círculos osculadores no espaço.",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "involute_desc": r"Involuta espacial cujas retas tangentes a $r(s)$ são normais a $I(s)$.",
            "radii": r"\rho(s) = \frac{1}{|\kappa(s)|}, \quad \sigma(s) = \frac{1}{|\tau(s)|}, \quad \frac{\sigma}{\rho} = \text{const}",
        }
    elif cls == "espiral_de_cornu":
        return {
            "curve_r": r"r(s) = \left( \int_0^s \cos\left(\frac{c u^2}{2}\right)du,\, \int_0^s \sin\left(\frac{c u^2}{2}\right)du \right)",
            "curve_desc": r"Clotoide (Espiral de Cornu) com $\kappa(s) = c \cdot s$. O ângulo de direção cresce quadraticamente: $\theta(s) = \frac{c s^2}{2}$.",
            "vec_t": r"T(s) = \left( \cos\left(\frac{c s^2}{2}\right),\, \sin\left(\frac{c s^2}{2}\right) \right)",
            "vec_n": r"N(s) = \left( -\sin\left(\frac{c s^2}{2}\right),\, \cos\left(\frac{c s^2}{2}\right) \right)",
            "vec_b": "",
            "evolute": r"E(s) = r(s) + \frac{1}{c\,s} N(s)",
            "evolute_desc": r"A evoluta da clotoide é o envelope das normais com raio $\rho(s) = \frac{1}{c\,s}$.",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "involute_desc": r"Involuta (evolvente) gerada pelo desenrolamento a partir de $s_1$.",
            "radii": r"\rho(s) = \frac{1}{|c \cdot s|}, \quad \sigma(s) = \infty",
        }
    elif cls == "espiral_logaritmica":
        return {
            "curve_r": r"r(s) = r(s_0) + \int_{s_0}^s (\cos\theta(u),\, \sin\theta(u))\,du",
            "curve_desc": r"Espiral Logarítmica com $\kappa(s) = \frac{1}{a s + b}$ e raio $\rho(s) = |a s + b|$. Ângulo constante com o raio vetor.",
            "vec_t": r"T(s) = \left( \cos\theta(s),\, \sin\theta(s) \right), \quad \theta(s) = \int \kappa\,du",
            "vec_n": r"N(s) = \left( -\sin\theta(s),\, \cos\theta(s) \right)",
            "vec_b": "",
            "evolute": r"E(s) = r(s) + (a s + b) N(s)",
            "evolute_desc": r"A evoluta de uma espiral logarítmica é outra espiral logarítmica congruente.",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "involute_desc": r"A involuta da espiral logarítmica também é uma espiral logarítmica congruente.",
            "radii": r"\rho(s) = |a s + b|, \quad \sigma(s) = \infty",
        }
    elif is_planar:
        return {
            "curve_r": r"r(s) = r(s_0) + \int_{s_0}^s (\cos\theta(u),\, \sin\theta(u))\,du",
            "curve_desc": r"Curva plana integrada pelo Teorema Fundamental das Curvas Planas via ângulo de direção $\theta(s) = \int_{s_0}^s \kappa(u)\,du$.",
            "vec_t": r"T(s) = \left( \cos\theta(s),\, \sin\theta(s) \right) = \frac{dr}{ds}",
            "vec_n": r"N(s) = \left( -\sin\theta(s),\, \cos\theta(s) \right) = J \cdot T(s)",
            "vec_b": "",
            "evolute": r"E(s) = r(s) + \frac{1}{\kappa(s)} N(s)",
            "evolute_desc": r"Evoluta: locus dos centros de curvatura e envelope de todas as retas normais.",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "involute_desc": r"Involuta (evolvente): trajetória da extremidade de corda desenrolada a partir de $s_1$.",
            "radii": r"\rho(s) = \frac{1}{|\kappa(s)|}, \quad \sigma(s) = \infty",
        }
    else:
        return {
            "curve_r": r"r(s) = r(s_0) + \int_{s_0}^s T(u)\,du",
            "curve_desc": r"Curva espacial $\mathbb{R}^3$ reconstruída pelo Teorema Fundamental integrando o sistema de Frenet-Serret em $\mathrm{SO}(3)$.",
            "vec_t": r"\frac{dT}{ds} = \kappa(s) N(s), \quad T(s) = \frac{dr}{ds}",
            "vec_n": r"\frac{dN}{ds} = -\kappa(s) T(s) + \tau(s) B(s)",
            "vec_b": r"\frac{dB}{ds} = -\tau(s) N(s), \quad B(s) = T(s) \times N(s)",
            "evolute": r"E(s) = r(s) + \frac{1}{\kappa(s)} N(s)",
            "evolute_desc": r"Evoluta espacial: linha dos centros dos círculos osculadores no espaço tridimensional.",
            "involute": r"I(s) = r(s) + (s_1 - s) T(s)",
            "involute_desc": r"Involuta espacial cujas retas tangentes a $r(s)$ são normais a $I(s)$.",
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
        dim_badge_style = "background: rgba(56, 189, 248, 0.2); color: #38bdf8;"
        init_pos_str = f"({init_x:.2f}, {init_y:.2f})"
        init_t_str = "0.000 (Plana)"
        hint_str = "Diedro de Frenet {T, N}, Retas Tangente/Normal e Círculo Osculador — clique na curva ou arraste o controle"
        page_title = title or f"Teorema Fundamental das Curvas Planas — {class_label} (2D)"
    else:
        mode_label = "3D"
        dim_badge_style = "background: rgba(168, 85, 247, 0.2); color: #c084fc;"
        init_pos_str = f"({init_x:.2f}, {init_y:.2f}, {init_z:.2f})"
        init_t_str = f"{init_t:.3f}"
        hint_str = "Triedro de Frenet {T, N, B}, Planos e Círculo Osculador — clique na curva ou arraste o controle"
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
        init_evo_str = "∞ (κ ≈ 0)"

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

    # Post-script JavaScript to inject inside Plotly.newPlot.then(...)
    post_script_js = f"""
window.CURVE_METRICS = {metrics_json};
var isPlanar = {"true" if is_planar else "false"};
var totalFrames = {num_frames};
var curFrame = 0;
var isPlaying = false;
var playTimer = null;
var animSpeed = 1.0;

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
    tElem.innerText = m.is_planar ? "0.000 (Plana)" : m.tau.toFixed(3);
  }}
  if (rhoElem) rhoElem.innerText = m.rho === null ? "∞" : m.rho.toFixed(3);
  if (sigElem && !m.is_planar) {{
    sigElem.innerText = m.sigma === null ? "∞" : m.sigma.toFixed(3);
  }}

  if (evoElem) {{
    if (m.Ex === null || m.Ex === undefined) {{
      evoElem.innerText = "∞ (κ ≈ 0)";
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

  // Update vectors
  var vt = document.getElementById("hud-vec-t");
  var vn = document.getElementById("hud-vec-n");
  var vb = document.getElementById("hud-vec-b");
  if (vt && m.Tx !== undefined) {{
    vt.innerText = m.is_planar
      ? "[" + m.Tx.toFixed(3) + ", " + m.Ty.toFixed(3) + "]"
      : "[" + m.Tx.toFixed(3) + ", " + m.Ty.toFixed(3) + ", " + m.Tz.toFixed(3) + "]";
  }}
  if (vn && m.Nx !== undefined) {{
    vn.innerText = m.is_planar
      ? "[" + m.Nx.toFixed(3) + ", " + m.Ny.toFixed(3) + "]"
      : "[" + m.Nx.toFixed(3) + ", " + m.Ny.toFixed(3) + ", " + m.Nz.toFixed(3) + "]";
  }}
  if (vb && m.Bx !== undefined && !m.is_planar) {{
    vb.innerText = "[" + m.Bx.toFixed(3) + ", " + m.By.toFixed(3) + ", " + m.Bz.toFixed(3) + "]";
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

function goToFrame(frameIdx) {{
  var gd = document.getElementById("fundamental_curve_plot");
  if (!gd) return;
  frameIdx = Math.max(0, Math.min(totalFrames - 1, frameIdx));
  curFrame = frameIdx;
  Plotly.animate(gd, ["frame_" + frameIdx], {{
    mode: "immediate",
    frame: {{ duration: 0, redraw: !isPlanar }},
    transition: {{ duration: 0 }}
  }});
  Plotly.relayout(gd, {{
    "sliders[0].active": frameIdx
  }});
  updateHUDMetrics(frameIdx);
}}

function togglePlay() {{
  var btn = document.getElementById("btn-dock-play");
  var icon = document.getElementById("play-icon");
  if (isPlaying) {{
    isPlaying = false;
    clearInterval(playTimer);
    playTimer = null;
    if (icon) icon.innerText = "▶";
    if (btn) btn.classList.remove("active");
  }} else {{
    isPlaying = true;
    if (icon) icon.innerText = "⏸";
    if (btn) btn.classList.add("active");
    var intervalMs = Math.max(16, Math.round(45 / animSpeed));
    playTimer = setInterval(function() {{
      var next = (curFrame + 1) % totalFrames;
      goToFrame(next);
    }}, intervalMs);
  }}
}}

function setPlaybackSpeed(btn) {{
  var speeds = [0.5, 1.0, 1.5, 2.0];
  var currIdx = speeds.indexOf(animSpeed);
  var nextIdx = (currIdx + 1) % speeds.length;
  animSpeed = speeds[nextIdx];
  if (btn) btn.innerText = animSpeed + "x";
  if (isPlaying) {{
    clearInterval(playTimer);
    var intervalMs = Math.max(16, Math.round(45 / animSpeed));
    playTimer = setInterval(function() {{
      var next = (curFrame + 1) % totalFrames;
      goToFrame(next);
    }}, intervalMs);
  }}
}}

function toggleTraceVisibility(traceIdx, isVisible) {{
  var gd = document.getElementById("fundamental_curve_plot");
  if (!gd) return;
  Plotly.restyle(gd, {{ visible: isVisible ? true : "legendonly" }}, [traceIdx]);
}}

function toggleTheme() {{
  var currentTheme = document.documentElement.getAttribute("data-theme") || "light";
  var newTheme = currentTheme === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", newTheme);
  var icon = document.getElementById("theme-icon");
  if (icon) icon.innerText = newTheme === "dark" ? "☀️" : "🌙";

  var gd = document.getElementById("fundamental_curve_plot");
  if (!gd) return;
  var isDark = newTheme === "dark";
  var bg = isDark ? "#090d16" : "#ffffff";
  var grid = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)";
  var zeroline = isDark ? "rgba(255, 255, 255, 0.15)" : "rgba(0, 0, 0, 0.15)";
  var fontColor = isDark ? "#94a3b8" : "#64748b";

  if (isPlanar) {{
    Plotly.relayout(gd, {{
      paper_bgcolor: bg,
      plot_bgcolor: bg,
      "xaxis.gridcolor": grid,
      "xaxis.zerolinecolor": zeroline,
      "xaxis.color": fontColor,
      "yaxis.gridcolor": grid,
      "yaxis.zerolinecolor": zeroline,
      "yaxis.color": fontColor
    }});
  }} else {{
    Plotly.relayout(gd, {{
      paper_bgcolor: bg,
      plot_bgcolor: bg,
      "scene.xaxis.gridcolor": grid,
      "scene.xaxis.backgroundcolor": isDark ? "rgba(11, 15, 25, 0.8)" : "rgba(248, 250, 252, 0.5)",
      "scene.xaxis.color": fontColor,
      "scene.yaxis.gridcolor": grid,
      "scene.yaxis.backgroundcolor": isDark ? "rgba(11, 15, 25, 0.8)" : "rgba(248, 250, 252, 0.5)",
      "scene.yaxis.color": fontColor,
      "scene.zaxis.gridcolor": grid,
      "scene.zaxis.backgroundcolor": isDark ? "rgba(11, 15, 25, 0.8)" : "rgba(248, 250, 252, 0.5)",
      "scene.zaxis.color": fontColor
    }});
  }}
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

  if (typeof renderAllKaTeX === "function") {{
    renderAllKaTeX();
  }} else if (window.renderMathInElement) {{
    renderMathInElement(document.body, {{
      delimiters: [
        {{ left: "$$", right: "$$", display: true }},
        {{ left: "\\[", right: "\\]", display: true }},
        {{ left: "$", right: "$", display: false }},
        {{ left: "\\(", right: "\\)", display: false }}
      ],
      throwOnError: false
    }});
  }}
}}

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
    )

    # Fullscreen responsive HTML template with Collapsible Sidebar, KaTeX & Dock
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
  <script>
    function renderAllKaTeX() {{
      if (typeof renderMathInElement === "function") {{
        renderMathInElement(document.body, {{
          delimiters: [
            {{ left: "$$", right: "$$", display: true }},
            {{ left: "\\[", right: "\\]", display: true }},
            {{ left: "$", right: "$", display: false }},
            {{ left: "\\(", right: "\\)", display: false }}
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
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    :root, html[data-theme="light"] {{
      --bg-app: #f8fafc;
      --bg-canvas: #ffffff;
      --bg-sidebar: #ffffff;
      --text-title: #0f172a;
      --text-body: #334155;
      --text-muted: #64748b;
      --border-ui: #e2e8f0;
      --card-bg: #f8fafc;
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
      --dock-bg: rgba(255, 255, 255, 0.94);
      --dock-border: rgba(0, 0, 0, 0.08);
      --dock-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.10), 0 4px 12px -2px rgba(0, 0, 0, 0.05);
      --btn-bg: #f1f5f9;
      --btn-hover: #e2e8f0;
      --toggle-bg: #cbd5e1;
    }}
    html[data-theme="dark"] {{
      --bg-app: #060911;
      --bg-canvas: #090d16;
      --bg-sidebar: #0f172a;
      --text-title: #f8fafc;
      --text-body: #cbd5e1;
      --text-muted: #94a3b8;
      --border-ui: rgba(255, 255, 255, 0.08);
      --card-bg: #1e293b;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --dock-bg: rgba(15, 23, 42, 0.92);
      --dock-border: rgba(255, 255, 255, 0.12);
      --dock-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.6), 0 4px 12px -2px rgba(0, 0, 0, 0.4);
      --btn-bg: #1e293b;
      --btn-hover: #334155;
      --toggle-bg: #475569;
    }}
    html, body {{
      width: 100vw;
      height: 100vh;
      height: 100dvh;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background-color: var(--bg-app);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      user-select: none;
      color: var(--text-body);
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
    /* Collapsible Sidebar (Right Side) */
    #sidebar {{
      width: 360px;
      min-width: 360px;
      height: 100%;
      background: var(--bg-sidebar);
      border-left: 1px solid var(--border-ui);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      transition: margin-right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 50;
      box-shadow: -4px 0 24px rgba(0, 0, 0, 0.04);
    }}
    #sidebar.collapsed {{
      margin-right: -360px;
    }}
    .sidebar-header {{
      padding: 18px 20px 14px 20px;
      border-bottom: 1px solid var(--border-ui);
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .sidebar-title-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .sidebar-title-group {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .brand-icon {{
      font-size: 18px;
      font-weight: 700;
      color: var(--accent);
      background: rgba(37, 99, 235, 0.1);
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
    }}
    .sidebar-title {{
      font-size: 14px;
      font-weight: 700;
      color: var(--text-title);
      letter-spacing: -0.2px;
    }}
    .header-actions {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .icon-btn {{
      background: var(--btn-bg);
      border: 1px solid var(--border-ui);
      border-radius: 6px;
      width: 30px;
      height: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--text-title);
      font-size: 13px;
      transition: background 0.15s ease, transform 0.1s ease;
    }}
    .icon-btn:hover {{
      background: var(--btn-hover);
    }}
    .header-badges {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .hud-badge {{
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 5px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-class {{
      background: rgba(37, 99, 235, 0.12);
      color: var(--accent);
    }}
    .badge-dim {{
      {dim_badge_style}
    }}

    /* Scrollable HUD Container inside Sidebar (Preserving id="hud-card") */
    #hud-card {{
      flex: 1;
      overflow-y: auto;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    #hud-card::-webkit-scrollbar {{
      width: 5px;
    }}
    #hud-card::-webkit-scrollbar-thumb {{
      background: var(--border-ui);
      border-radius: 3px;
    }}
    .card-section {{
      background: var(--card-bg);
      border: 1px solid var(--border-ui);
      border-radius: 10px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .section-title {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--text-muted);
    }}
    .math-box {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 13px;
    }}
    .math-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 2px 0;
    }}
    .math-label {{
      color: var(--text-muted);
      font-size: 12px;
    }}
    .math-expr {{
      font-weight: 600;
      color: var(--text-title);
    }}
    .formula-card {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .formula-row {{
      display: flex;
      flex-direction: column;
      gap: 3px;
      padding: 6px 8px;
      background: rgba(0, 0, 0, 0.02);
      border-radius: 6px;
      border-left: 3px solid var(--accent);
    }}
    html[data-theme="dark"] .formula-row {{
      background: rgba(255, 255, 255, 0.03);
    }}
    .formula-title {{
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .formula-badge {{
      font-family: ui-monospace, "JetBrains Mono", Menlo, Consolas, monospace;
      font-size: 10px;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 4px;
      background: rgba(37, 99, 235, 0.1);
      color: var(--accent);
    }}
    .badge-t {{ background: rgba(16, 185, 129, 0.15); color: #10b981; }}
    .badge-n {{ background: rgba(239, 68, 68, 0.15); color: #ef4444; }}
    .badge-b {{ background: rgba(99, 102, 241, 0.15); color: #6366f1; }}
    .badge-evo {{ background: rgba(245, 158, 11, 0.15); color: #d97706; }}
    .badge-inv {{ background: rgba(168, 85, 247, 0.15); color: #9333ea; }}
    .formula-math {{
      font-size: 13px;
      color: var(--text-title);
      overflow-x: auto;
      overflow-y: hidden;
      padding: 2px 0;
    }}
    .formula-desc {{
      font-size: 10px;
      color: var(--text-muted);
      line-height: 1.4;
    }}
    .hud-grid {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .hud-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
      padding: 2px 0;
    }}
    .hud-label {{
      color: var(--text-muted);
    }}
    #hud-s, #hud-r, #hud-kappa, #hud-tau, #hud-rho, .hud-value {{
      font-family: ui-monospace, "JetBrains Mono", Menlo, Consolas, monospace;
      font-weight: 600;
      color: var(--text-title);
    }}
    .hud-vectors {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-top: 6px;
      padding-top: 8px;
      border-top: 1px solid var(--border-ui);
    }}
    .vec-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 12px;
    }}
    .vec-tag {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 11px;
    }}
    .vec-t {{ background: rgba(16, 185, 129, 0.15); color: #10b981; }}
    .vec-n {{ background: rgba(239, 68, 68, 0.15); color: #ef4444; }}
    .vec-b {{ background: rgba(99, 102, 241, 0.15); color: #6366f1; }}
    .vec-val {{
      font-family: ui-monospace, "JetBrains Mono", Menlo, Consolas, monospace;
      font-weight: 500;
      color: var(--text-body);
    }}
    .toggles-list {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .switch-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 4px 0;
      cursor: pointer;
    }}
    .switch-left {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .color-badge {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }}
    .switch-name {{
      font-size: 12px;
      color: var(--text-body);
    }}
    .toggle-wrap {{
      position: relative;
      width: 32px;
      height: 18px;
    }}
    .toggle-wrap input {{
      opacity: 0;
      width: 0;
      height: 0;
    }}
    .toggle-slider {{
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: var(--toggle-bg);
      transition: .2s;
      border-radius: 18px;
    }}
    .toggle-slider:before {{
      position: absolute;
      content: "";
      height: 14px;
      width: 14px;
      left: 2px;
      bottom: 2px;
      background-color: white;
      transition: .2s;
      border-radius: 50%;
    }}
    .toggle-wrap input:checked + .toggle-slider {{
      background-color: var(--accent);
    }}
    .toggle-wrap input:checked + .toggle-slider:before {{
      transform: translateX(14px);
    }}
    .theory-text {{
      font-size: 11px;
      line-height: 1.5;
      color: var(--text-muted);
    }}
    .hud-hint {{
      margin-top: 6px;
      font-size: 11px;
      color: var(--text-muted);
      border-top: 1px solid var(--border-ui);
      padding-top: 6px;
    }}

    /* Main Plot Container (Left Side) */
    #plot-container {{
      flex: 1 1 0%;
      min-width: 0;
      height: 100%;
      position: relative;
      overflow: hidden;
      background: var(--bg-canvas);
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
    }}
    /* Hide native Plotly slider and bulky buttons */
    .slider-container, .updatemenu-container {{
      display: none !important;
    }}
    .modebar-container {{
      top: 14px !important;
      left: 18px !important;
      right: auto !important;
      opacity: 0.65;
      transition: opacity 0.2s ease;
    }}
    .modebar-container:hover {{
      opacity: 1.0;
    }}

    /* Sidebar Floating Open Button (when collapsed) */
    .sidebar-expand-btn {{
      position: absolute;
      top: 16px;
      right: 16px;
      z-index: 95;
      background: var(--dock-bg);
      border: 1px solid var(--dock-border);
      border-radius: 8px;
      padding: 7px 12px;
      cursor: pointer;
      display: none;
      align-items: center;
      gap: 6px;
      box-shadow: var(--dock-shadow);
      color: var(--text-title);
      font-size: 12px;
      font-weight: 600;
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      transition: transform 0.15s ease, background 0.15s ease;
    }}
    .sidebar-expand-btn:hover {{
      background: var(--btn-hover);
      transform: scale(1.02);
    }}

    /* Modern Floating Control Dock */
    .control-dock {{
      position: absolute;
      bottom: 22px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--dock-bg);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid var(--dock-border);
      border-radius: 36px;
      padding: 8px 16px;
      display: flex;
      align-items: center;
      gap: 14px;
      box-shadow: var(--dock-shadow);
      z-index: 85;
      user-select: none;
    }}
    .dock-buttons {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .dock-btn {{
      width: 32px;
      height: 32px;
      border-radius: 50%;
      border: 1px solid var(--border-ui);
      background: var(--btn-bg);
      color: var(--text-title);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.15s ease;
    }}
    .dock-btn:hover {{
      background: var(--btn-hover);
      transform: scale(1.06);
    }}
    .dock-btn.btn-play {{
      width: 36px;
      height: 36px;
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff;
    }}
    .dock-btn.btn-play:hover {{
      background: var(--accent-hover);
    }}
    .dock-slider-wrap {{
      position: relative;
      width: 190px;
      display: flex;
      align-items: center;
    }}
    .dock-slider {{
      -webkit-appearance: none;
      appearance: none;
      width: 100%;
      height: 5px;
      border-radius: 3px;
      background: var(--border-ui);
      outline: none;
      cursor: pointer;
      position: relative;
      z-index: 2;
    }}
    .dock-slider::-webkit-slider-thumb {{
      -webkit-appearance: none;
      appearance: none;
      width: 15px;
      height: 15px;
      border-radius: 50%;
      background: var(--accent);
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
      transition: transform 0.1s ease;
    }}
    .dock-slider::-webkit-slider-thumb:hover {{
      transform: scale(1.2);
    }}
    .dock-slider::-moz-range-thumb {{
      width: 15px;
      height: 15px;
      border-radius: 50%;
      background: var(--accent);
      cursor: pointer;
      border: none;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
    }}
    .dock-track-fill {{
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      height: 5px;
      background: var(--accent);
      border-radius: 3px;
      pointer-events: none;
      z-index: 1;
      width: 0%;
    }}
    .dock-readout {{
      display: flex;
      align-items: center;
      gap: 4px;
      font-family: ui-monospace, "JetBrains Mono", Menlo, Consolas, monospace;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-body);
      white-space: nowrap;
    }}
    .dock-s-val {{
      color: var(--accent);
    }}
    .dock-s-max {{
      color: var(--text-muted);
      font-weight: 500;
    }}
    .dock-pct {{
      font-size: 11px;
      color: var(--text-muted);
      margin-left: 2px;
    }}
    .dock-btn-speed {{
      width: auto;
      padding: 4px 10px;
      border-radius: 16px;
      border: 1px solid var(--border-ui);
      background: var(--btn-bg);
      color: var(--text-title);
      font-weight: 700;
      font-size: 11px;
      cursor: pointer;
      transition: background 0.15s ease;
    }}
    .dock-btn-speed:hover {{
      background: var(--btn-hover);
    }}
  </style>
</head>
<body>
  <div id="app-layout">
    <!-- Main Plot Canvas on the Left -->
    <main id="plot-container">
      <!-- Floating Expand Button when Sidebar is Collapsed -->
      <button id="sidebar-expand-btn" class="sidebar-expand-btn" title="Expandir Painel Lateral">
        <span>Painel</span> <span>◀</span>
      </button>

      {plotly_snippet}

      <!-- Modern Floating Bottom Dock Centered in Canvas -->
      <div id="control-dock" class="control-dock">
        <div class="dock-buttons">
          <button id="btn-dock-first" class="dock-btn" title="Início (s₀)">⏮</button>
          <button id="btn-dock-prev" class="dock-btn" title="Passo Anterior">◀</button>
          <button id="btn-dock-play" class="dock-btn btn-play" title="Reproduzir / Pausar">
            <span id="play-icon">▶</span>
          </button>
          <button id="btn-dock-next" class="dock-btn" title="Próximo Passo">▶</button>
          <button id="btn-dock-last" class="dock-btn" title="Fim (s₁)">⏭</button>
        </div>

        <div class="dock-slider-wrap">
          <input type="range" id="dock-slider" min="0" max="{num_frames - 1}" value="0" step="1" class="dock-slider" aria-label="Comprimento de arco s">
          <div class="dock-track-fill" id="dock-track-fill"></div>
        </div>

        <div class="dock-readout">
          <span>s =</span>
          <span class="dock-s-val" id="dock-s-val">{init_s:.3f}</span>
          <span class="dock-s-max">/ {s1:.3f}</span>
          <span class="dock-pct" id="dock-pct">0%</span>
        </div>

        <button id="btn-dock-speed" class="dock-btn-speed" title="Velocidade da Reprodução">1x</button>
      </div>
    </main>

    <!-- Collapsible Modern Sidebar on the Right -->
    <aside id="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-title-row">
          <div class="sidebar-title-group">
            <span class="brand-icon">∫</span>
            <h1 class="sidebar-title">Teorema Fundamental de Curvas</h1>
          </div>
          <div class="header-actions">
            <button id="theme-toggle-btn" class="icon-btn" title="Alternar Modo Claro/Escuro" aria-label="Alternar Tema">
              <span id="theme-icon">🌙</span>
            </button>
            <button id="sidebar-toggle-btn" class="icon-btn" title="Recolher Painel" aria-label="Recolher Painel">
              <span>▶</span>
            </button>
          </div>
        </div>
        <div class="header-badges">
          <span class="hud-badge badge-class" id="hud-class">{class_label}</span>
          <span class="hud-badge badge-dim">{mode_label}</span>
        </div>
      </div>

      <!-- Main Scrollable Content Container (id="hud-card" preserved for test compatibility) -->
      <div id="hud-card">
        <!-- Section 1: Fórmulas Intrínsecas (KaTeX) -->
        <div class="card-section">
          <div class="section-title">Fórmulas Intrínsecas</div>
          <div class="math-box">
            <div class="math-row">
              <span class="math-label">Curvatura:</span>
              <span class="math-expr" id="math-kappa">$$\\kappa(s) = {kappa_tex}$$</span>
            </div>
            <div class="math-row">
              <span class="math-label">Torção:</span>
              <span class="math-expr" id="math-tau">$$\\tau(s) = {tau_tex}$$</span>
            </div>
            <div class="math-row">
              <span class="math-label">Intervalo:</span>
              <span class="math-expr">$$s \\in [{s0:.2f}, {s1:.2f}]$$</span>
            </div>
          </div>
        </div>

        <!-- Section 2: Teorema Fundamental — Equação e Triedro -->
        <div class="card-section">
          <div class="section-title">Teorema Fundamental — Equação e Triedro</div>
          <div class="formula-card">
            <div class="formula-row">
              <div class="formula-title"><span>Curva Reconstruída</span> <span class="formula-badge">r(s)</span></div>
              <div class="formula-math" id="math-curve-r">${formulas["curve_r"]}$</div>
              <div class="formula-desc">{formulas["curve_desc"]}</div>
            </div>
            <div class="formula-row">
              <div class="formula-title"><span>Vetor Tangente</span> <span class="formula-badge badge-t">T(s)</span></div>
              <div class="formula-math" id="math-vec-t">${formulas["vec_t"]}$</div>
            </div>
            <div class="formula-row">
              <div class="formula-title"><span>Vetor Normal Principal</span> <span class="formula-badge badge-n">N(s)</span></div>
              <div class="formula-math" id="math-vec-n">${formulas["vec_n"]}$</div>
            </div>
            {binormal_formula_html}
          </div>
        </div>

        <!-- Section 3: Curvas Associadas (Evoluta & Involuta) -->
        <div class="card-section">
          <div class="section-title">Curvas Associadas (Evoluta & Involuta)</div>
          <div class="formula-card">
            <div class="formula-row">
              <div class="formula-title"><span>Evoluta (Centros de Curvatura)</span> <span class="formula-badge badge-evo">E(s)</span></div>
              <div class="formula-math" id="math-evolute">${formulas["evolute"]}$</div>
              <div class="formula-desc">{formulas["evolute_desc"]}</div>
            </div>
            <div class="formula-row">
              <div class="formula-title"><span>Involuta / Evolvente de Corda</span> <span class="formula-badge badge-inv">I(s)</span></div>
              <div class="formula-math" id="math-involute">${formulas["involute"]}$</div>
              <div class="formula-desc">{formulas["involute_desc"]}</div>
            </div>
            <div class="formula-row">
              <div class="formula-title"><span>Raios Característicos</span> <span class="formula-badge">ρ, σ</span></div>
              <div class="formula-math" id="math-radii">${formulas["radii"]}$</div>
            </div>
          </div>
        </div>

        <!-- Section 4: Grandezas Instantâneas (Live HUD) -->
        <div class="card-section">
          <div class="section-title">Grandezas Instantâneas</div>
          <div class="hud-grid">
            <div class="hud-row"><span class="hud-label">Comprimento de Arco (s):</span><span class="hud-value" id="hud-s">{init_s:.3f}</span></div>
            <div class="hud-row"><span class="hud-label">Posição r(s):</span><span class="hud-value" id="hud-r">{init_pos_str}</span></div>
            <div class="hud-row"><span class="hud-label">Curvatura κ(s):</span><span class="hud-value" id="hud-kappa">{init_k:.3f}</span></div>
            <div class="hud-row"><span class="hud-label">Torção τ(s):</span><span class="hud-value" id="hud-tau">{init_t_str}</span></div>
            <div class="hud-row"><span class="hud-label">Raio Curvatura ρ(s):</span><span class="hud-value" id="hud-rho">{init_rho}</span></div>
            {sigma_hud_row}
            <div class="hud-row"><span class="hud-label">Evoluta E(s):</span><span class="hud-value" id="hud-evolute">{init_evo_str}</span></div>
            <div class="hud-row"><span class="hud-label">Involuta I(s):</span><span class="hud-value" id="hud-involute">{init_inv_str}</span></div>
          </div>
          <!-- Frame Vectors -->
          <div class="hud-vectors">
            {vec_html}
          </div>
        </div>

        <!-- Section 5: Visibilidade do Aparato -->
        <div class="card-section">
          <div class="section-title">Visibilidade do Aparato</div>
          <div class="toggles-list">
            {switches_markup}
          </div>
        </div>

        <!-- Section 6: Fundamentação Teórica -->
        <div class="card-section">
          <div class="section-title">Fundamentação Teórica</div>
          <p class="theory-text">{theory_summary}</p>
          <div class="hud-hint">{hint_str}</div>
        </div>
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
