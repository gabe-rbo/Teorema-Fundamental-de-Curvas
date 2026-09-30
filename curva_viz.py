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

if TYPE_CHECKING:
    from curva_engine import CurveResult

# ---------------------------------------------------------------------------
# Quad topology for Mesh3d planes
# ---------------------------------------------------------------------------
_QUAD_I = [0, 0]
_QUAD_J = [1, 2]
_QUAD_K = [2, 3]

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
        marker=dict(size=8, color="#ffea00", symbol="circle"),
        hovertemplate="<b>Ponto Ativo r(s)</b><br>x: %{x:.3f}<br>y: %{y:.3f}<br>z: %{z:.3f}<extra></extra>",
    )
    # Trace 2: Vetor Tangente T
    t2 = go.Scatter3d(
        x=[float(P[0]), float(P[0] + L_vec * T[0])],
        y=[float(P[1]), float(P[1] + L_vec * T[1])],
        z=[float(P[2]), float(P[2] + L_vec * T[2])],
        mode="lines+markers",
        name="Vetor Tangente T",
        line=dict(color="#00e676", width=7),
        marker=dict(size=[0, 8], color="#00e676"),
        hovertemplate="<b>Vetor Tangente T</b><extra></extra>",
    )
    # Trace 3: Vetor Normal N
    t3 = go.Scatter3d(
        x=[float(P[0]), float(P[0] + L_vec * N[0])],
        y=[float(P[1]), float(P[1] + L_vec * N[1])],
        z=[float(P[2]), float(P[2] + L_vec * N[2])],
        mode="lines+markers",
        name="Vetor Normal N",
        line=dict(color="#ff1744", width=7),
        marker=dict(size=[0, 8], color="#ff1744"),
        hovertemplate="<b>Vetor Normal N</b><extra></extra>",
    )
    # Trace 4: Vetor Binormal B
    t4 = go.Scatter3d(
        x=[float(P[0]), float(P[0] + L_vec * B[0])],
        y=[float(P[1]), float(P[1] + L_vec * B[1])],
        z=[float(P[2]), float(P[2] + L_vec * B[2])],
        mode="lines+markers",
        name="Vetor Binormal B",
        line=dict(color="#2979ff", width=7),
        marker=dict(size=[0, 8], color="#2979ff"),
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
        line=dict(color="rgba(0, 230, 118, 0.65)", width=3, dash="dash"),
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
        color="rgba(255, 213, 79, 0.28)",
        opacity=0.28,
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
        color="rgba(255, 82, 82, 0.20)",
        opacity=0.20,
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
        color="rgba(68, 138, 255, 0.20)",
        opacity=0.20,
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
        line=dict(color="#ffd600", width=4),
        hovertemplate="<b>Círculo Osculador</b><extra></extra>",
    )

    return [t1, t2, t3, t4, t5, t6, t7, t8, t9]


def build_curve_figure(
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
        line=dict(color="#00e5ff", width=5),
        marker=dict(size=3, color="#00e5ff"),
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
                "font": {"size": 13, "color": "#38bdf8"},
            },
            steps=slider_steps,
            pad={"b": 10, "t": 20},
            len=0.88,
            x=0.06,
            y=0.03,
            tickcolor="#64748b",
            font={"color": "#94a3b8", "size": 10},
            bgcolor="rgba(15, 23, 42, 0.6)",
            activebgcolor="#0284c7",
            bordercolor="rgba(255, 255, 255, 0.1)",
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
        bgcolor="rgba(15, 23, 42, 0.7)",
        bordercolor="rgba(255, 255, 255, 0.15)",
        font={"color": "#f1f5f9", "size": 12},
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
        bgcolor="rgba(15, 23, 42, 0.7)",
        bordercolor="rgba(255, 255, 255, 0.15)",
        font={"color": "#f1f5f9", "size": 11},
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

    fig = go.Figure(data=fig_data, frames=frames)
    fig.update_layout(
        title=dict(
            text=final_title,
            font=dict(color="#f8fafc", size=15),
            x=0.5,
            y=0.98,
            xanchor="center",
        ),
        uirevision="constant",
        scene=dict(
            uirevision="constant",
            aspectmode="data",
            camera=init_camera,
            xaxis=dict(
                title="X",
                color="#94a3b8",
                gridcolor="rgba(255, 255, 255, 0.1)",
                zerolinecolor="rgba(255, 255, 255, 0.2)",
                backgroundcolor="rgba(11, 15, 25, 0.8)",
                showbackground=True,
            ),
            yaxis=dict(
                title="Y",
                color="#94a3b8",
                gridcolor="rgba(255, 255, 255, 0.1)",
                zerolinecolor="rgba(255, 255, 255, 0.2)",
                backgroundcolor="rgba(11, 15, 25, 0.8)",
                showbackground=True,
            ),
            zaxis=dict(
                title="Z",
                color="#94a3b8",
                gridcolor="rgba(255, 255, 255, 0.1)",
                zerolinecolor="rgba(255, 255, 255, 0.2)",
                backgroundcolor="rgba(11, 15, 25, 0.8)",
                showbackground=True,
            ),
        ),
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0b0f19",
        margin=dict(l=0, r=0, t=35, b=0),
        legend=dict(
            x=0.98,
            y=0.85,
            xanchor="right",
            yanchor="top",
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.1)",
            borderwidth=1,
            font=dict(color="#f1f5f9", size=11),
        ),
        sliders=sliders,
        updatemenus=updatemenus,
    )

    # Attach internal metadata for HTML exporter
    fig._curve_result = curve_data  # type: ignore[attr-defined]
    fig._hud_metrics = hud_metrics  # type: ignore[attr-defined]

    return fig


def export_interactive_html(
    curve_data: CurveResult | go.Figure,
    output_path: str,
    title: str | None = None,
    include_plotlyjs: bool | str = "cdn",
) -> str:
    """
    Export the interactive 3D curve visualization to a responsive HTML file.

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
    else:
        curve_res = curve_data
        fig = build_curve_figure(curve_data, title=title)
        hud_metrics = getattr(fig, "_hud_metrics", None)

    # Compute default title and metadata
    if curve_res is not None:
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
        class_label = "Curva Reconstruída"
        init_s = 0.0
        init_x, init_y, init_z = 0.0, 0.0, 0.0
        init_k, init_t = 0.0, 0.0
        init_rho = "—"

    page_title = title or f"Teorema Fundamental de Curvas — {class_label}"

    # Prepare HUD metrics JSON
    metrics_json = json.dumps(hud_metrics or [])

    # Post-script JavaScript to inject inside Plotly.newPlot.then(...)
    post_script_js = f"""
window.CURVE_METRICS = {metrics_json};

function updateHUDMetrics(idx) {{
  if (!window.CURVE_METRICS || !window.CURVE_METRICS[idx]) return;
  var m = window.CURVE_METRICS[idx];
  var sElem = document.getElementById("hud-s");
  var rElem = document.getElementById("hud-r");
  var kElem = document.getElementById("hud-kappa");
  var tElem = document.getElementById("hud-tau");
  var rhoElem = document.getElementById("hud-rho");
  if (sElem) sElem.innerText = m.s.toFixed(3);
  if (rElem) rElem.innerText = "(" + m.x.toFixed(2) + ", " + m.y.toFixed(2) + ", " + m.z.toFixed(2) + ")";
  if (kElem) kElem.innerText = m.kappa.toFixed(3);
  if (tElem) tElem.innerText = m.tau.toFixed(3);
  if (rhoElem) rhoElem.innerText = m.rho === null ? "∞" : m.rho.toFixed(3);
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
      Plotly.animate(gd, ["frame_" + frameIdx], {{
        mode: "immediate",
        frame: {{ duration: 0, redraw: true }},
        transition: {{ duration: 0 }}
      }});
      Plotly.relayout(gd, {{
        "sliders[0].active": frameIdx
      }});
      updateHUDMetrics(frameIdx);
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
"""

    # Generate inner Plotly HTML snippet
    plotly_snippet = fig.to_html(
        include_plotlyjs=include_plotlyjs,
        full_html=False,
        div_id="fundamental_curve_plot",
        post_script=post_script_js,
    )

    # Fullscreen responsive HTML template with CSS reset & HUD
    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    html, body {{
      width: 100vw;
      height: 100vh;
      height: 100dvh;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background-color: #0b0f19;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      user-select: none;
    }}
    #plot-container {{
      width: 100vw;
      height: 100vh;
      position: absolute;
      top: 0;
      left: 0;
      overflow: hidden;
    }}
    .plotly-graph-div {{
      width: 100vw !important;
      height: 100vh !important;
    }}
    /* Glassmorphism HUD Card */
    #hud-card {{
      position: absolute;
      top: 18px;
      left: 18px;
      background: rgba(15, 23, 42, 0.88);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 12px;
      padding: 16px 20px;
      color: #f1f5f9;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
      z-index: 1000;
      min-width: 290px;
      pointer-events: auto;
    }}
    #hud-card h2 {{
      font-size: 15px;
      font-weight: 700;
      color: #38bdf8;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    #hud-class, .hud-badge {{
      font-size: 11px;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 4px;
      background: rgba(56, 189, 248, 0.2);
      color: #38bdf8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .hud-row {{
      display: flex;
      justify-content: space-between;
      margin: 4px 0;
      font-size: 13px;
    }}
    .hud-label {{
      color: #94a3b8;
    }}
    #hud-s, #hud-r, #hud-kappa, #hud-tau, #hud-rho, .hud-value {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-weight: 600;
      color: #f8fafc;
    }}
    .hud-hint {{
      margin-top: 10px;
      font-size: 11px;
      color: #64748b;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 6px;
    }}
  </style>
</head>
<body>
  <div id="hud-card">
    <h2>Teorema Fundamental de Curvas <span class="hud-badge" id="hud-class">{class_label}</span></h2>
    <div class="hud-row"><span class="hud-label">Comprimento de Arco (s):</span><span class="hud-value" id="hud-s">{init_s:.3f}</span></div>
    <div class="hud-row"><span class="hud-label">Posição r(s):</span><span class="hud-value" id="hud-r">({init_x:.2f}, {init_y:.2f}, {init_z:.2f})</span></div>
    <div class="hud-row"><span class="hud-label">Curvatura κ(s):</span><span class="hud-value" id="hud-kappa">{init_k:.3f}</span></div>
    <div class="hud-row"><span class="hud-label">Torção τ(s):</span><span class="hud-value" id="hud-tau">{init_t:.3f}</span></div>
    <div class="hud-row"><span class="hud-label">Raio Curvatura ρ(s):</span><span class="hud-value" id="hud-rho">{init_rho}</span></div>
    <div class="hud-hint">Triedro de Frenet, Planos e Círculo Osculador — clique na curva ou arraste o controle</div>
  </div>
  <div id="plot-container">
    {plotly_snippet}
  </div>
</body>
</html>
"""

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(full_html, encoding="utf-8")

    return str(out_file)
