"""
Tests for the Fundamental Theorem of Plane Curves (Teorema Fundamental das Curvas Planas)
and Pure 2D Interactive Plotly Visualizations.

Verifies:
  1. For planar curves (tau == 0), reconstruction is done directly via quadrature
     theta(s) = int kappa(u) du, r(s) = int T(u) du without solving the 12-state ODEs.
  2. scipy.integrate.solve_ivp is NEVER invoked when tau == 0.
  3. Machine-precision orthonormality (drift < 1e-15) and exact analytical matching.
  4. Pure 2D Plotly visualization (go.Scatter, scaleanchor='x', scaleratio=1, no 3D scene).
  5. Space curves (tau != 0) continue to solve the 3D ODE system and render in 3D WebGL.
"""

from unittest.mock import patch
import numpy as np
import pytest
from scipy.special import fresnel

import curva_engine
import curva_viz


class TestTeoremaFundamentalCurvasPlanas:
    """Verifies direct quadrature engine for plane curves without ODE integration."""

    def test_solve_ivp_bypassed_for_planar_curves(self):
        """Verify that scipy.integrate.solve_ivp is NEVER invoked for tau == 0."""
        with patch("curva_engine.solve_ivp") as mock_solve_ivp:
            mock_solve_ivp.side_effect = RuntimeError(
                "solve_ivp should not be called for planar curves (tau == 0)!"
            )
            # Both explicit "0" and default tau should bypass solve_ivp
            res1 = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=3.14, num_points=100)
            assert res1.is_planar is True
            assert mock_solve_ivp.call_count == 0

            res2 = curva_engine.reconstruct_curve("1", s0=0.0, s1=6.28, num_points=100)
            assert res2.is_planar is True
            assert mock_solve_ivp.call_count == 0

            res3 = curva_engine.reconstruct_curve("s", "0", s0=0.0, s1=4.0, num_points=100)
            assert res3.is_planar is True
            assert mock_solve_ivp.call_count == 0

    def test_solve_ivp_invoked_for_spatial_curves(self):
        """Verify that solve_ivp IS invoked when tau != 0."""
        with patch("curva_engine.solve_ivp", wraps=curva_engine.solve_ivp) as spy_solve_ivp:
            res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=50)
            assert res.is_planar is False
            assert spy_solve_ivp.call_count >= 1

    def test_circle_quadrature_exactness_machine_precision(self):
        """For circle (kappa=2, tau=0), verify agreement with analytical formula and closure < 1e-14."""
        res = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=np.pi, num_points=200)
        # Analytical circle trajectory: x(s) = 0.5*sin(2s), y(s) = 0.5*(1 - cos(2s))
        x_true = 0.5 * np.sin(2.0 * res.s)
        y_true = 0.5 * (1.0 - np.cos(2.0 * res.s))

        assert np.allclose(res.r[0, :], x_true, atol=1e-12)
        assert np.allclose(res.r[1, :], y_true, atol=1e-12)

        # Full circle at s = pi: x = 0.0, y = 0.0 (endpoint error < 1e-14)
        endpoint_err = np.linalg.norm(res.r[:, -1])
        assert endpoint_err < 1e-14

        # Verify radius 0.5 everywhere relative to center (0, 0.5)
        radii = np.sqrt(res.r[0, :] ** 2 + (res.r[1, :] - 0.5) ** 2)
        assert np.allclose(radii, 0.5, atol=1e-12)

    def test_straight_line_quadrature(self):
        """For straight line (kappa=0, tau=0), verify x(s) = s - s0, y(s) = 0."""
        res = curva_engine.reconstruct_curve("0", "0", s0=2.0, s1=7.0, num_points=100)
        assert res.classification == "reta"
        assert res.is_planar is True
        assert np.allclose(res.r[0, :], res.s - 2.0, atol=1e-14)
        assert np.allclose(res.r[1, :], 0.0, atol=1e-14)
        assert np.allclose(res.r[2, :], 0.0, atol=1e-14)

    def test_clothoid_fresnel_quadrature_analytical_match(self):
        """For Cornu spiral (kappa(s)=s, tau=0), verify agreement with Fresnel integrals."""
        s_eval = np.linspace(0.0, 4.0, 200)
        res = curva_engine.reconstruct_curve("s", "0", s0=0.0, s1=4.0, num_points=200)
        assert res.classification == "espiral_de_cornu"

        # Analytical Fresnel integrals: x = sqrt(pi)*C(s/sqrt(pi)), y = sqrt(pi)*S(s/sqrt(pi))
        S, C = fresnel(s_eval / np.sqrt(np.pi))
        x_true = np.sqrt(np.pi) * C
        y_true = np.sqrt(np.pi) * S

        max_err_x = np.max(np.abs(res.r[0, :] - x_true))
        max_err_y = np.max(np.abs(res.r[1, :] - y_true))
        assert max_err_x < 1e-7
        assert max_err_y < 1e-7

    def test_machine_precision_frame_orthonormality(self):
        """Verify ||T||=1, ||N||=1, T . N = 0 to machine precision (< 1e-15)."""
        res = curva_engine.reconstruct_curve("1 + 0.5*cos(s)", "0", s0=0.0, s1=6.28, num_points=150)
        # Norms
        assert np.allclose(np.linalg.norm(res.T, axis=0), 1.0, atol=1e-15)
        assert np.allclose(np.linalg.norm(res.N, axis=0), 1.0, atol=1e-15)
        assert np.allclose(np.linalg.norm(res.B, axis=0), 1.0, atol=1e-15)

        # Dot product T . N == 0
        dot_TN = np.sum(res.T * res.N, axis=0)
        assert np.allclose(dot_TN, 0.0, atol=1e-15)

        # Determinant det([T, N, B]) == +1
        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        dets = np.linalg.det(frames)
        assert np.allclose(dets, 1.0, atol=1e-15)


class TestVisualizacaoCurvasPlanas2D:
    """Verifies pure 2D Plotly visualization for planar curves."""

    def test_pure_2d_figure_traces_and_layout(self):
        """Verify planar curves create 2D Scatter traces, scaleanchor='x', and no 3D scene camera."""
        res = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=np.pi, num_points=80)
        fig = curva_viz.build_curve_figure(res)

        # Must be pure 2D Scatter traces (type == 'scatter')
        for i, trace in enumerate(fig.data):
            assert trace.type == "scatter", f"Trace {i} ({trace.name}) must be 2D scatter, not {trace.type}"

        # Layout must define 2D Cartesian axes with equal aspect ratio
        assert fig.layout.xaxis.title.text == "X"
        assert fig.layout.yaxis.title.text == "Y"
        assert fig.layout.yaxis.scaleanchor == "x"
        assert fig.layout.yaxis.scaleratio == 1

        # Camera eye in scene should not be configured
        assert fig.layout.scene.camera.eye.x is None

        # Traces present in 2D apparatus
        trace_names = [t.name for t in fig.data]
        assert "Curva r(s)" in trace_names
        assert "Ponto Ativo r(s)" in trace_names
        assert "Vetor Tangente T" in trace_names
        assert "Vetor Normal N" in trace_names
        assert "Reta Tangente L_T" in trace_names
        assert "Reta Normal L_N" in trace_names
        assert "Círculo Osculador" in trace_names

        # Out-of-plane 3D traces must not exist
        assert "Vetor Binormal B" not in trace_names
        assert "Plano Osculador (T, N)" not in trace_names
        assert "Plano Normal (N, B)" not in trace_names
        assert "Plano Retificante (T, B)" not in trace_names

    def test_spatial_curves_still_render_in_3d(self):
        """Verify space curves (tau != 0) continue to render in full 3D with 10 traces."""
        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=80)
        fig = curva_viz.build_curve_figure(res)

        # Space curve uses Scatter3d and Mesh3d
        assert fig.data[0].type == "scatter3d"
        assert len(fig.data) == 10

        # 3D camera is configured
        assert fig.layout.scene.camera.eye.x == 1.6
        assert fig.layout.scene.camera.eye.y == 1.6
        assert fig.layout.scene.camera.eye.z == 1.3

    def test_export_interactive_html_planar_2d(self, tmp_path):
        """Verify exported HTML for planar curves contains 2D badges and 2D coordinates."""
        res = curva_engine.reconstruct_curve("1", "0", s0=0.0, s1=6.28, num_points=60)
        out_html = tmp_path / "circle_2d.html"
        curva_viz.export_interactive_html(res, str(out_html))
        assert out_html.exists()

        content = out_html.read_text(encoding="utf-8")
        assert "Teorema Fundamental das Curvas Planas" in content
        assert ">2D</span>" in content
        assert "0.000 (Plana)" in content
        assert "Diedro de Frenet" in content
