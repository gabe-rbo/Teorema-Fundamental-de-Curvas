"""Empirical Stress, Boundary Condition, and Adversarial Challenge Suite for curva_viz.py.

Designed and executed by Empirical Challenger Agent (teamwork_preview_challenger_m2_fresh).
Empirically verifies:
  1. Multi-curve HTML generation and file size compactness (< 2MB) across all geometric classes.
  2. HTML syntactic validity, structure, doctype, and JSON integrity.
  3. Zero-curvature (kappa=0) straight line and inflection point osculating circle suppression.
  4. Near-zero curvature and excessive radius suppression safeguards.
  5. Responsive CSS rules (100vw, 100vh, 100dvh, overflow: hidden).
  6. Client-side JavaScript listeners (plotly_click, plotly_sliderchange, plotly_animatingframe, resize).
  7. Exact differential geometry apparatus traces (initial 10 traces, planar vs spatial visibility).
  8. Geometric accuracy of osculating plane, normal plane, rectifying plane, and osculating circle.
  9. High-resolution discretization scalability (N=2000 points) and minimum discretization (N=2 points).
  10. Dual-input API handling (CurveResult vs prebuilt go.Figure).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import curva_engine as ce
import curva_viz as cv


class TestHTMLGenerationAndFileSize:
    """Stress-tests HTML generation across diverse curve classes and verifies file size compactness."""

    @pytest.mark.parametrize(
        ("kappa_expr", "tau_expr", "s0", "s1", "expected_class"),
        [
            ("1", "0", 0.0, 6.283185307, "circulo"),
            ("1", "1", 0.0, 8.885765876, "helice_circular"),
            ("0", "0", 0.0, 10.0, "reta"),
            ("s", "0", 0.0, 5.0, "espiral_de_cornu"),
            ("1/(s + 1)", "0", 0.0, 10.0, "espiral_logaritmica"),
            ("1 + 0.1*sin(s)", "2*(1 + 0.1*sin(s))", 0.0, 6.283185307, "helice_cilindrica_geral"),
            ("1 + 0.1*sin(s)", "0", 0.0, 6.283185307, "curva_plana"),
            ("1 + 0.1*sin(s)", "0.5*cos(s)", 0.0, 6.283185307, "curva_espacial"),
        ],
    )
    def test_multi_curve_html_export_and_file_size(
        self, tmp_path, kappa_expr, tau_expr, s0, s1, expected_class
    ):
        """Verify HTML generation across all 8 geometric classes with file size strictly < 2MB."""
        res = ce.reconstruct_curve(
            kappa_expr, tau_expr, s0=s0, s1=s1, num_points=500
        )
        assert res.classification == expected_class

        out_html = tmp_path / f"curve_{expected_class}.html"
        result_path = cv.export_interactive_html(res, str(out_html))
        assert Path(result_path).exists()

        file_size_bytes = out_html.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        # Requirement: compact file size < 2MB (with CDN Plotly, typically 0.8 - 1.2 MB)
        assert file_size_mb < 2.0, (
            f"HTML file for {expected_class} size is {file_size_mb:.2f}MB, exceeding 2MB limit"
        )
        assert file_size_bytes > 10_000, "HTML file is suspiciously small"

    def test_high_resolution_discretization_scalability(self, tmp_path):
        """Stress-test N=2000 points. Frames must be capped at 200 and file size remain < 2MB."""
        res = ce.reconstruct_curve("1", "1", s0=0.0, s1=20.0, num_points=2000)
        out_html = tmp_path / "high_res_helix.html"
        cv.export_interactive_html(res, str(out_html))

        file_size_mb = out_html.stat().st_size / (1024 * 1024)
        assert file_size_mb < 2.0, (
            f"High-res N=2000 size {file_size_mb:.2f}MB exceeded 2MB"
        )

        fig = cv.build_curve_figure(res)
        assert len(fig.frames) <= 200, (
            f"Frame count {len(fig.frames)} exceeded subsampling cap of 200"
        )

    def test_minimum_points_boundary(self, tmp_path):
        """Verify minimum point count N=2 builds and exports cleanly."""
        res = ce.reconstruct_curve("1", "0", s0=0.0, s1=1.0, num_points=2)
        out_html = tmp_path / "min_points.html"
        cv.export_interactive_html(res, str(out_html))
        assert out_html.exists()


class TestHTMLSyntacticValidityAndCSS:
    """Verifies HTML structural syntax, responsive CSS reset rules, and HUD elements."""

    @pytest.fixture
    def sample_html(self, tmp_path) -> str:
        res = ce.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=100)
        out_html = tmp_path / "sample.html"
        cv.export_interactive_html(res, str(out_html))
        return out_html.read_text(encoding="utf-8")

    def test_html_doctype_and_tags(self, sample_html):
        """Verify HTML5 doctype, html, head, and body tags."""
        html_clean = sample_html.strip()
        assert html_clean.startswith("<!DOCTYPE html>")
        assert "<html" in html_clean and "</html>" in html_clean
        assert "<head>" in html_clean and "</head>" in html_clean
        assert "<body>" in html_clean and "</body>" in html_clean
        assert '<meta charset="utf-8">' in html_clean
        assert (
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            in html_clean
        )

    def test_responsive_css_reset(self, sample_html):
        """Verify responsive fullscreen CSS reset: 100vw, 100vh, 100dvh, overflow: hidden."""
        assert "100vw" in sample_html
        assert "100vh" in sample_html
        assert "100dvh" in sample_html
        assert "overflow: hidden" in sample_html
        assert "#plot-container" in sample_html
        assert ".plotly-graph-div" in sample_html
        assert "100vw !important" in sample_html
        assert "100vh !important" in sample_html

    def test_hud_card_elements_present(self, sample_html):
        """Verify HUD card markup and metric element IDs."""
        assert 'id="hud-card"' in sample_html
        assert 'id="hud-s"' in sample_html
        assert 'id="hud-r"' in sample_html
        assert 'id="hud-kappa"' in sample_html
        assert 'id="hud-tau"' in sample_html
        assert 'id="hud-rho"' in sample_html
        assert 'id="hud-class"' in sample_html

    def test_metrics_json_integrity(self, sample_html):
        """Verify injected window.CURVE_METRICS is syntactically valid JSON."""
        match = re.search(
            r"window\.CURVE_METRICS\s*=\s*(\[.*?\]);", sample_html, re.DOTALL
        )
        assert match is not None, "window.CURVE_METRICS not found in script"
        metrics_data = json.loads(match.group(1))
        assert isinstance(metrics_data, list)
        assert len(metrics_data) > 0
        for item in metrics_data:
            assert "s" in item
            assert "x" in item and "y" in item and "z" in item
            assert "kappa" in item
            assert "tau" in item
            assert "rho" in item


class TestZeroCurvatureAndEdgeCases:
    """Stress-tests kappa=0 straight line, inflection points, and zero-division suppression."""

    def test_straight_line_circle_suppression(self, tmp_path):
        """Verify kappa=0 straight line suppresses osculating circle without division-by-zero."""
        res = ce.reconstruct_curve("0", "0", s0=0.0, s1=10.0, num_points=100)
        fig = cv.build_curve_figure(res)

        # Osculating circle in initial traces
        circle_traces = [t for t in fig.data if t.name == "Círculo Osculador"]
        assert len(circle_traces) == 1
        circle_trace = circle_traces[0]
        assert len(circle_trace.x) == 0
        assert len(circle_trace.y) == 0

        # Osculating circle must be suppressed in all animation frames
        for frame in fig.frames:
            frame_circle = frame.data[-1]
            assert len(frame_circle.x) == 0
            assert len(frame_circle.y) == 0

        out_html = tmp_path / "straight_line.html"
        cv.export_interactive_html(res, str(out_html))
        content = out_html.read_text(encoding="utf-8")
        assert "∞" in content

    def test_inflection_point_clothoid_suppression(self):
        """Verify Clothoid (kappa=s) starting at s=0 suppresses circle at s=0 and renders at s>0."""
        res = ce.reconstruct_curve("s", "0", s0=0.0, s1=5.0, num_points=100)
        fig = cv.build_curve_figure(res)

        # Frame 0 is s=0, kappa=0 -> circle suppressed
        frame0_circle = fig.frames[0].data[-1]
        assert len(frame0_circle.x) == 0

        # Later frame where kappa is substantial and rho <= 10*span -> circle populated
        # Find a frame where circle is rendered
        rendered_count = 0
        for frame in fig.frames:
            if len(frame.data[-1].x) > 0:
                rendered_count += 1
        assert rendered_count > 0, "Osculating circle was never rendered for Clothoid at s>0"

    def test_compute_circle_coords_thresholds(self):
        """Adversarial stress-test of _compute_circle_coords cutoff logic."""
        P = np.array([0.0, 0.0, 0.0])
        T = np.array([1.0, 0.0, 0.0])
        N = np.array([0.0, 1.0, 0.0])
        span = 2.0

        # Exact zero
        cx, cy, cz = cv._compute_circle_coords(P, T, N, 0.0, span)
        assert cx == [] and cy == [] and cz == []

        # Below 1e-5 threshold
        cx, cy, cz = cv._compute_circle_coords(P, T, N, 1e-6, span)
        assert cx == [] and cy == [] and cz == []

        # Above 1e-5 but rho > 10*span (rho = 200, 10*span = 20)
        cx, cy, cz = cv._compute_circle_coords(P, T, N, 0.005, span)
        assert cx == [] and cy == [] and cz == []

        # Valid circle: kappa = 1.0, rho = 1.0 <= 20
        cx, cy, cz = cv._compute_circle_coords(P, T, N, 1.0, span)
        assert len(cx) == 65
        assert len(cy) == 65
        assert len(cz) == 65

        # Check contact order at theta=0: C(0) = P = (0, 0, 0)
        assert np.isclose(cx[0], 0.0, atol=1e-10)
        assert np.isclose(cy[0], 0.0, atol=1e-10)
        assert np.isclose(cz[0], 0.0, atol=1e-10)


class TestJavaScriptListenersAndInteractivity:
    """Verifies client-side JavaScript injection for curve snapping, slider, and resizing."""

    @pytest.fixture
    def html_content(self, tmp_path) -> str:
        res = ce.reconstruct_curve("1", "0", s0=0.0, s1=6.28, num_points=100)
        out_html = tmp_path / "interactive.html"
        cv.export_interactive_html(res, str(out_html))
        return out_html.read_text(encoding="utf-8")

    def test_plotly_click_listener_implementation(self, html_content):
        """Verify plotly_click handler uses curveNumber, customdata, Plotly.animate and relayout."""
        assert 'gd.on("plotly_click"' in html_content
        assert "pt.curveNumber === 0" in html_content
        assert "pt.customdata" in html_content
        assert "Plotly.animate(gd" in html_content
        assert '"sliders[0].active": frameIdx' in html_content
        assert "updateHUDMetrics(frameIdx)" in html_content

    def test_slider_and_animation_listeners(self, html_content):
        """Verify plotly_sliderchange and plotly_animatingframe listeners."""
        assert 'gd.on("plotly_sliderchange"' in html_content
        assert 'gd.on("plotly_animatingframe"' in html_content

    def test_window_resize_listener(self, html_content):
        """Verify window.resize listener calls Plotly.Plots.resize."""
        assert 'window.addEventListener("resize"' in html_content
        assert "Plotly.Plots.resize(gd)" in html_content

    def test_trace0_customdata_structure(self):
        """Verify Trace 0 customdata contains [s, frameIdx, kappa, tau] for all vertices."""
        res = ce.reconstruct_curve("2", "1", s0=0.0, s1=5.0, num_points=100)
        fig = cv.build_curve_figure(res)
        trace0 = fig.data[0]
        assert trace0.name == "Curva r(s)"
        assert len(trace0.customdata) == 100
        for pt_data in trace0.customdata:
            assert len(pt_data) == 4
            s_val, frame_idx, k_val, t_val = pt_data
            assert isinstance(s_val, float)
            assert isinstance(frame_idx, int)
            assert 0 <= frame_idx < len(fig.frames)
            assert np.isclose(k_val, 2.0)
            assert np.isclose(t_val, 1.0)


class TestDifferentialApparatusAndGeometry:
    """Verifies trace composition, geometric plane orthogonality, and planar curve adaptations."""

    def test_trace_composition_and_names(self):
        """Verify the 10-trace composite differential apparatus at active point."""
        res = ce.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=50)
        fig = cv.build_curve_figure(res)
        assert len(fig.data) == 10

        expected_names = [
            "Curva r(s)",
            "Ponto Ativo r(s)",
            "Vetor Tangente T",
            "Vetor Normal N",
            "Vetor Binormal B",
            "Reta Tangente L_T",
            "Plano Osculador (T, N)",
            "Plano Normal (N, B)",
            "Plano Retificante (T, B)",
            "Círculo Osculador",
        ]
        actual_names = [trace.name for trace in fig.data]
        assert actual_names == expected_names

    def test_selective_frame_updates_trace_count(self):
        """Verify selective animation frames update only traces 1..9, keeping trace 0 static."""
        res = ce.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=50)
        fig = cv.build_curve_figure(res)

        for frame in fig.frames:
            assert list(frame.traces) == [1, 2, 3, 4, 5, 6, 7, 8, 9]
            assert len(frame.data) == 9

    def test_planar_curve_camera_and_visibility(self):
        """Verify planar curves (tau=0) are rendered in pure 2D with equal aspect ratio and 2D apparatus."""
        res = ce.reconstruct_curve("1", "0", s0=0.0, s1=6.28, num_points=50)
        fig = cv.build_curve_figure(res)

        # Planar curve is pure 2D Scatter
        assert fig.data[0].type == "scatter"
        assert fig.layout.yaxis.scaleanchor == "x"
        assert fig.layout.yaxis.scaleratio == 1

        trace_names = [t.name for t in fig.data]
        assert "Curva r(s)" in trace_names
        assert "Vetor Tangente T" in trace_names
        assert "Vetor Normal N" in trace_names
        assert "Reta Tangente L_T" in trace_names
        assert "Reta Normal L_N" in trace_names
        assert "Círculo Osculador" in trace_names
        assert "Vetor Binormal B" not in trace_names

    def test_planes_geometric_orthogonality(self):
        """Verify quad vertices for osculating, normal, and rectifying planes satisfy normal equations."""
        res = ce.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=50)
        P = res.r[:, 0]
        T = res.T[:, 0]
        N = res.N[:, 0]
        B = res.B[:, 0]
        W = 1.0

        # Osculating plane: spanned by T, N -> normal to B
        ox, oy, oz = cv._compute_quad_coords(P, T, N, W)
        for i in range(4):
            vertex = np.array([ox[i], oy[i], oz[i]])
            dot_val = np.dot(vertex - P, B)
            assert np.isclose(dot_val, 0.0, atol=1e-12), (
                f"Osculating vertex {i} not orthogonal to B"
            )

        # Normal plane: spanned by N, B -> normal to T
        nx, ny, nz = cv._compute_quad_coords(P, N, B, W)
        for i in range(4):
            vertex = np.array([nx[i], ny[i], nz[i]])
            dot_val = np.dot(vertex - P, T)
            assert np.isclose(dot_val, 0.0, atol=1e-12), (
                f"Normal plane vertex {i} not orthogonal to T"
            )

        # Rectifying plane: spanned by T, B -> normal to N
        rx, ry, rz = cv._compute_quad_coords(P, T, B, W)
        for i in range(4):
            vertex = np.array([rx[i], ry[i], rz[i]])
            dot_val = np.dot(vertex - P, N)
            assert np.isclose(dot_val, 0.0, atol=1e-12), (
                f"Rectifying plane vertex {i} not orthogonal to N"
            )

    def test_osculating_circle_center_and_radius(self):
        """Verify osculating circle points have center r + (1/kappa)*N and radius 1/kappa."""
        res = ce.reconstruct_curve("2", "0", s0=0.0, s1=3.14, num_points=50)
        P = res.r[:, 0]
        T = res.T[:, 0]
        N = res.N[:, 0]
        B = res.B[:, 0]
        k_val = 2.0
        expected_radius = 0.5
        expected_center = P + (1.0 / k_val) * N

        cx, cy, cz = cv._compute_circle_coords(P, T, N, k_val, span=1.0)
        circle_mat = np.array([cx, cy, cz])

        # Distance of all circle points from center must equal expected_radius
        dists = np.linalg.norm(circle_mat - expected_center[:, None], axis=0)
        assert np.allclose(dists, expected_radius, atol=1e-10)

        # All circle points must lie in osculating plane (orthogonal to B)
        plane_offsets = np.dot(B, circle_mat - P[:, None])
        assert np.allclose(plane_offsets, 0.0, atol=1e-10)


class TestDualInputAndRobustness:
    """Tests dual-input API in export_interactive_html and figure construction robustness."""

    def test_export_accepts_prebuilt_figure(self, tmp_path):
        """Verify export_interactive_html accepts prebuilt go.Figure directly."""
        res = ce.reconstruct_curve("1", "1", s0=0.0, s1=3.0, num_points=50)
        fig = cv.build_curve_figure(res)

        out_html = tmp_path / "prebuilt.html"
        cv.export_interactive_html(fig, str(out_html))
        assert out_html.exists()
        assert out_html.stat().st_size > 10_000

    def test_build_curve_figure_rejects_single_point(self):
        """Verify build_curve_figure raises ValueError if points < 2."""
        dummy_res = ce.CurveResult(
            s=np.array([0.0]),
            r=np.zeros((3, 1)),
            T=np.ones((3, 1)),
            N=np.ones((3, 1)),
            B=np.ones((3, 1)),
            kappa=np.array([1.0]),
            tau=np.array([0.0]),
            classification="curva_plana",
            s0=0.0,
            s1=0.0,
        )
        with pytest.raises(ValueError, match="at least 2 points"):
            cv.build_curve_figure(dummy_res)

    def test_extreme_intervals_and_oscillations(self, tmp_path):
        """Stress-test very small intervals, large intervals, and high frequency oscillation."""
        # 1. Very small interval (tests span <= 1e-4 fallback)
        res_small = ce.reconstruct_curve("1", "0", s0=0.0, s1=1e-4, num_points=50)
        p_small = tmp_path / "small.html"
        cv.export_interactive_html(res_small, str(p_small))
        assert p_small.exists()

        # 2. Large interval
        res_large = ce.reconstruct_curve("1", "1", s0=0.0, s1=100.0, num_points=500)
        p_large = tmp_path / "large.html"
        cv.export_interactive_html(res_large, str(p_large))
        assert p_large.exists()

        # 3. High frequency oscillation
        res_osc = ce.reconstruct_curve("5 + 4*sin(20*s)", "1", s0=0.0, s1=3.14, num_points=500)
        p_osc = tmp_path / "osc.html"
        cv.export_interactive_html(res_osc, str(p_osc))
        assert p_osc.exists()


class TestModernUIComponents:
    """Verifies the modern redesign: collapsible sidebar, KaTeX, light/dark themes, custom switches, and floating dock."""

    @pytest.fixture
    def planar_html(self, tmp_path) -> str:
        res = ce.reconstruct_curve("1", "0", s0=0.0, s1=6.28, num_points=100)
        p = tmp_path / "planar_ui.html"
        cv.export_interactive_html(res, str(p))
        return p.read_text(encoding="utf-8")

    @pytest.fixture
    def space_html(self, tmp_path) -> str:
        res = ce.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=100)
        p = tmp_path / "space_ui.html"
        cv.export_interactive_html(res, str(p))
        return p.read_text(encoding="utf-8")

    def test_sidebar_and_layout_structure(self, planar_html):
        assert 'id="app-layout"' in planar_html
        assert 'id="sidebar"' in planar_html
        assert 'id="sidebar-toggle-btn"' in planar_html
        assert 'id="sidebar-expand-btn"' in planar_html
        assert "toggleSidebar()" in planar_html

    def test_katex_integration_and_formulas(self, planar_html):
        assert "katex.min.css" in planar_html
        assert "katex.min.js" in planar_html
        assert "renderMathInElement" in planar_html
        assert 'id="math-kappa"' in planar_html
        assert 'id="math-tau"' in planar_html

    def test_theme_system_elements(self, planar_html):
        assert 'data-theme="light"' in planar_html
        assert 'id="theme-toggle-btn"' in planar_html
        assert 'id="theme-icon"' in planar_html
        assert "toggleTheme()" in planar_html

    def test_floating_dock_elements(self, planar_html):
        assert 'id="control-dock"' in planar_html
        assert 'id="dock-slider"' in planar_html
        assert 'id="dock-track-fill"' in planar_html
        assert 'id="btn-dock-play"' in planar_html
        assert 'id="btn-dock-prev"' in planar_html
        assert 'id="btn-dock-next"' in planar_html
        assert 'id="btn-dock-speed"' in planar_html
        assert 'id="dock-s-val"' in planar_html
        assert 'id="dock-pct"' in planar_html

    def test_custom_apparatus_switches(self, planar_html, space_html):
        assert "toggleTraceVisibility(" in planar_html
        assert "toggleTraceVisibility(" in space_html
        assert "Reta Normal L_N" in planar_html
        assert "Vetor Binormal B" in space_html

    def test_vector_displays_in_hud(self, planar_html, space_html):
        assert 'id="hud-vec-t"' in planar_html
        assert 'id="hud-vec-n"' in planar_html
        assert 'id="hud-vec-b"' in space_html

    def test_fixed_axis_ranges_and_zoom_stability(self):
        """Verify 2D and 3D figures set fixed ranges, autorange=False, and uirevision to avoid frame jumping."""
        res_2d = ce.reconstruct_curve("1", "0", s0=0.0, s1=6.28, num_points=50)
        fig_2d = cv.build_curve_figure(res_2d)
        assert fig_2d.layout.uirevision == "constant"
        assert fig_2d.layout.xaxis.autorange is False
        assert fig_2d.layout.yaxis.autorange is False
        assert len(fig_2d.layout.xaxis.range) == 2
        assert len(fig_2d.layout.yaxis.range) == 2
        assert fig_2d.layout.xaxis.range[0] < fig_2d.layout.xaxis.range[1]

        res_3d = ce.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=50)
        fig_3d = cv.build_curve_figure(res_3d)
        assert fig_3d.layout.uirevision == "constant"
        assert fig_3d.layout.scene.uirevision == "constant"
        assert fig_3d.layout.scene.aspectmode == "cube"
        assert fig_3d.layout.scene.xaxis.autorange is False
        assert fig_3d.layout.scene.yaxis.autorange is False
        assert fig_3d.layout.scene.zaxis.autorange is False
        assert len(fig_3d.layout.scene.xaxis.range) == 2
        assert len(fig_3d.layout.scene.yaxis.range) == 2
        assert len(fig_3d.layout.scene.zaxis.range) == 2

    def test_sidebar_right_push_layout(self, planar_html):
        """Verify sidebar is positioned on the right and pushes plot container on the left."""
        plot_idx = planar_html.find('id="plot-container"')
        sidebar_idx = planar_html.find('id="sidebar"')
        dock_idx = planar_html.find('id="control-dock"')
        # Plot container comes before sidebar in DOM (flex row: plot on left, sidebar on right)
        assert plot_idx < sidebar_idx
        # Control dock is inside plot-container before sidebar
        assert plot_idx < dock_idx < sidebar_idx
        # CSS checks
        assert "margin-right: -360px" in planar_html
        assert "border-left: 1px solid var(--border-ui)" in planar_html
