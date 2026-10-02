"""Adversarial stress and edge-case verification for Milestone M2 (curva_viz.py).

Covers:
1. Zero curvature (straight line, kappa = 0) -> osculating circle handling and division by zero prevention.
2. Zero torsion (tau = 0, circle, plane curves) -> planar projection adaptation, camera, and diedro trace visibility.
3. Boundary point counts: N=2, N=3, and N=5000 -> frame subsampling, slider steps, and memory/performance stability.
4. Inflection points / zero crossings: kappa(s) touching zero -> frame-by-frame osculating circle transition and HUD infinity.
5. HTML file integrity & JavaScript syntax: HTML structure, 100vw/100vh/100dvh, HUD element IDs, and Node.js AST syntax check.
6. Osculating circle mathematical exactness & contact order: center, radius, coplanarity with osculating plane, and 0th/1st/2nd order contact.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import curva_engine
import curva_viz


# ==============================================================================
# 1. ZERO CURVATURE (STRAIGHT LINE, KAPPA = 0)
# ==============================================================================
class TestZeroCurvatureEdgeCases:
    """Stress tests for kappa(s) = 0 (straight line)."""

    def test_straight_line_figure_building(self):
        """Verifies build_curve_figure builds cleanly for a straight line with rho = inf."""
        res = curva_engine.reconstruct_curve("0", "0", s0=0.0, s1=10.0, num_points=100)
        assert res.classification == "reta"
        assert res.is_planar is True

        fig = curva_viz.build_curve_figure(res)
        assert fig is not None

        # Círculo Osculador - must have empty coordinates
        circle_traces = [t for t in fig.data if t.name == "Círculo Osculador"]
        assert len(circle_traces) == 1
        circle_trace = circle_traces[0]
        assert len(circle_trace.x) == 0
        assert len(circle_trace.y) == 0

        # All frames must also have empty circle coordinates
        for frame in fig.frames:
            frame_circle = frame.data[-1]  # last trace in frame is the circle
            assert len(frame_circle.x) == 0
            assert len(frame_circle.y) == 0

    def test_straight_line_html_export_and_hud(self, tmp_path):
        """Verifies HTML export for straight line shows infinite curvature radius in HUD and no NaNs."""
        res = curva_engine.reconstruct_curve("0", "0", s0=0.0, s1=5.0, num_points=50)
        out_html = tmp_path / "straight_line.html"
        curva_viz.export_interactive_html(res, str(out_html))
        assert out_html.exists()

        content = out_html.read_text(encoding="utf-8")
        # Ensure no numerical NaN was serialized into JSON data or HUD
        assert ": NaN" not in content
        assert "NaN," not in content
        assert "null" in content or "∞" in content
        assert 'id="hud-rho">∞</span>' in content


# ==============================================================================
# 2. ZERO TORSION (PLANAR CURVES, TAU = 0)
# ==============================================================================
class TestZeroTorsionEdgeCases:
    """Stress tests for planar curves (tau = 0)."""

    def test_planar_camera_and_diedro_visibility(self):
        """Verifies planar curves initialize in pure 2D with equal aspect ratio and 2D apparatus."""
        # 1. Circle (planar)
        res_circle = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=np.pi, num_points=60)
        assert res_circle.is_planar is True
        fig_circle = curva_viz.build_curve_figure(res_circle)

        # Must be pure 2D Scatter traces
        assert fig_circle.data[0].type == "scatter"
        # 2D equal aspect ratio
        assert fig_circle.layout.yaxis.scaleanchor == "x"
        assert fig_circle.layout.yaxis.scaleratio == 1

        # In-plane 2D traces must be visible
        trace_names = [t.name for t in fig_circle.data]
        assert "Curva r(s)" in trace_names
        assert "Ponto Ativo r(s)" in trace_names
        assert "Vetor Tangente T" in trace_names
        assert "Vetor Normal N" in trace_names
        assert "Reta Tangente L_T" in trace_names
        assert "Reta Normal L_N" in trace_names
        assert "Círculo Osculador" in trace_names

        # 3D out-of-plane traces (Binormal, Plano Normal, Plano Retificante) should not exist in 2D
        assert "Vetor Binormal B" not in trace_names
        assert "Plano Normal (N, B)" not in trace_names
        assert "Plano Retificante (T, B)" not in trace_names

    def test_spatial_curve_full_visibility(self):
        """Verifies 3D spatial curves (tau != 0) show all 10 traces and isometric camera."""
        res_helix = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=2.0 * np.pi, num_points=60)
        fig_helix = curva_viz.build_curve_figure(res_helix)

        scene = fig_helix.layout.scene
        cam_eye = scene.camera.eye
        # Initial 3D camera: eye=(1.6, 1.6, 1.3)
        assert np.isclose(cam_eye.x, 1.6, atol=1e-6)
        assert np.isclose(cam_eye.y, 1.6, atol=1e-6)
        assert np.isclose(cam_eye.z, 1.3, atol=1e-6)

        # All traces should be active (visible != 'legendonly')
        for i, trace in enumerate(fig_helix.data):
            assert trace.visible != "legendonly", f"Trace {i} ({trace.name}) should not be legendonly for space curve"


# ==============================================================================
# 3. BOUNDARY POINT COUNTS (N=2, N=3, N=5000)
# ==============================================================================
class TestPointLimitsAndSubsampling:
    """Stress tests on minimal and maximal discretization point counts."""

    def test_point_count_minimum_two(self):
        """Verifies N=2 points builds successfully without crashing and generates 2 frames."""
        res_2 = curva_engine.reconstruct_curve("1", "0", s0=0.0, s1=1.0, num_points=2)
        assert len(res_2.s) == 2

        fig_2 = curva_viz.build_curve_figure(res_2)
        assert len(fig_2.frames) == 2
        assert len(fig_2.layout.sliders[0].steps) == 2

        # Verify slider steps values and labels
        step0 = fig_2.layout.sliders[0].steps[0]
        step1 = fig_2.layout.sliders[0].steps[1]
        assert str(step0["value"]) == "0"
        assert str(step1["value"]) == "1"
        assert step0["label"] == f"{res_2.s[0]:.2f}"
        assert step1["label"] == f"{res_2.s[1]:.2f}"

    def test_point_count_three(self):
        """Verifies N=3 points builds successfully and generates 3 frames."""
        res_3 = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=2.0, num_points=3)
        assert len(res_3.s) == 3

        fig_3 = curva_viz.build_curve_figure(res_3)
        assert len(fig_3.frames) == 3
        assert len(fig_3.layout.sliders[0].steps) == 3

    def test_point_count_large_5000(self, tmp_path):
        """Verifies N=5000 points caps frames at 200, handles distance matrix correctly, and exports cleanly."""
        res_5000 = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=10.0, num_points=5000)
        assert len(res_5000.s) == 5000

        fig_5000 = curva_viz.build_curve_figure(res_5000)

        # Frames must be capped at 200
        assert len(fig_5000.frames) == 200
        assert len(fig_5000.layout.sliders[0].steps) == 200

        # Customdata on Trace 0 must have exactly 5000 elements
        trace_curve = fig_5000.data[0]
        assert len(trace_curve.customdata) == 5000

        # Each customdata entry: [s, frameIdx, kappa, tau]
        frame_indices = [row[1] for row in trace_curve.customdata]
        assert min(frame_indices) == 0
        assert max(frame_indices) == 199
        # Check monotonicity of frame snapping
        assert np.all(np.diff(frame_indices) >= 0)

        # Export HTML and verify size is compact (< 3MB)
        out_html = tmp_path / "large_5000.html"
        curva_viz.export_interactive_html(fig_5000, str(out_html))
        assert out_html.exists()
        file_size_mb = out_html.stat().st_size / (1024 * 1024)
        assert file_size_mb < 3.0, f"HTML file size too large: {file_size_mb:.2f} MB"


# ==============================================================================
# 4. INFLECTION POINTS & CURVATURE ZERO CROSSINGS
# ==============================================================================
class TestInflectionAndCurvatureZeroCrossings:
    """Stress tests for curves where curvature kappa(s) touches or approaches zero."""

    def test_curvature_touching_zero_isolated(self):
        """Verifies kappa(s) = (s - 2)^2 touches zero at s=2 without numerical issues."""
        res = curva_engine.reconstruct_curve("(s - 2)^2", "0", s0=0.0, s1=4.0, num_points=41)
        # Find index near s=2
        idx_zero = np.argmin(np.abs(res.s - 2.0))
        assert np.isclose(res.kappa[idx_zero], 0.0, atol=1e-12)

        fig = curva_viz.build_curve_figure(res)

        # Find frame corresponding to s=2
        hud_metrics = getattr(fig, "_hud_metrics")
        zero_frames = [f_i for f_i, m in enumerate(hud_metrics) if np.isclose(m["s"], 2.0, atol=1e-1)]
        assert len(zero_frames) > 0
        target_f = zero_frames[0]

        # The circle in the zero frame must be empty
        frame_circle = fig.frames[target_f].data[-1]
        assert len(frame_circle.x) == 0

        # While a frame away from zero (e.g. s=0, kappa=4) must have 65 circle points
        frame_nonzero = fig.frames[0].data[-1]
        assert len(frame_nonzero.x) == 65

    def test_tiny_curvature_suppressed_by_span(self):
        """Verifies that when kappa is tiny (> 1e-5 but rho > 10*span), circle is suppressed."""
        # kappa = 1e-4, span ~ 1 -> rho = 10,000 >> 10*span
        res = curva_engine.reconstruct_curve("1e-4", "0", s0=0.0, s1=1.0, num_points=20)
        fig = curva_viz.build_curve_figure(res)

        # Circle trace in initial apparatus must be empty
        circle_trace = [t for t in fig.data if t.name == "Círculo Osculador"][0]
        assert len(circle_trace.x) == 0

# ==============================================================================
# 5. OSCULATING CIRCLE EXACT GEOMETRY & CONTACT ORDER
# ==============================================================================
class TestOsculatingCircleMathematicalExactness:
    """Rigorous differential geometry tests for the osculating circle."""

    def test_circle_osculating_circle_exact_coincidence(self):
        """For a circle of kappa=2, the osculating circle at s=0 must have radius 0.5, center (0, 0.5)."""
        res = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=np.pi, num_points=100)
        fig = curva_viz.build_curve_figure(res)

        # Initial osculating circle at s=0
        circle_trace = [t for t in fig.data if t.name == "Círculo Osculador"][0]
        cx = np.array(circle_trace.x)
        cy = np.array(circle_trace.y)
        assert len(cx) == 65

        # Center must be at (0, 0.5) in 2D
        dist_to_center = np.sqrt(cx**2 + (cy - 0.5) ** 2)
        assert np.allclose(dist_to_center, 0.5, atol=1e-12)

        # First point of circle (theta=0) must be exactly active point r(0) = (0, 0)
        assert np.allclose([cx[0], cy[0]], [0.0, 0.0], atol=1e-12)

    def test_space_helix_osculating_circle_geometry_and_contact(self):
        """For circular helix kappa=1, tau=1:
        Verify osculating circle lies strictly in osculating plane and satisfies 2nd order contact.
        """
        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=2.0 * np.pi, num_points=100)
        fig = curva_viz.build_curve_figure(res)

        # Check at 5 different frames
        for frame_idx in [0, 20, 50, 80]:
            frame = fig.frames[frame_idx]
            # Active point
            P = np.array([frame.data[0].x[0], frame.data[0].y[0], frame.data[0].z[0]])
            # Unit vectors T, N, B
            T = np.array([frame.data[1].x[1] - P[0], frame.data[1].y[1] - P[1], frame.data[1].z[1] - P[2]])
            T = T / np.linalg.norm(T)
            N = np.array([frame.data[2].x[1] - P[0], frame.data[2].y[1] - P[1], frame.data[2].z[1] - P[2]])
            N = N / np.linalg.norm(N)
            B = np.array([frame.data[3].x[1] - P[0], frame.data[3].y[1] - P[1], frame.data[3].z[1] - P[2]])
            B = B / np.linalg.norm(B)

            # Osculating circle points
            circle_data = frame.data[8]
            pts = np.stack([circle_data.x, circle_data.y, circle_data.z], axis=0)  # (3, 65)

            # 1. 0th order contact: C(0) == P
            assert np.allclose(pts[:, 0], P, atol=1e-12)

            # 2. Coplanarity: All circle points must be orthogonal to B: (pts - P) . B == 0
            rel_pts = pts - P[:, None]
            dot_with_B = np.sum(rel_pts * B[:, None], axis=0)
            assert np.allclose(dot_with_B, 0.0, atol=1e-12)

            # 3. Radius and center: center c = P + N (since kappa=1)
            c = P + N
            dists = np.linalg.norm(pts - c[:, None], axis=0)
            assert np.allclose(dists, 1.0, atol=1e-12)

            # 4. 1st order contact: circle velocity at theta=0 is rho * T = 1.0 * T
            # Using finite differences on circle points:
            # theta steps: dtheta = 2*pi / 64
            dtheta = 2.0 * np.pi / 64.0
            tangent_approx = (pts[:, 1] - pts[:, -2]) / (2.0 * dtheta)
            assert np.allclose(tangent_approx, T, atol=1e-2)

            # 5. 2nd order contact: circle acceleration at theta=0 is (1/kappa) * N = N
            accel_approx = (pts[:, 1] - 2.0 * pts[:, 0] + pts[:, -2]) / (dtheta**2)
            assert np.allclose(accel_approx, N, atol=1e-2)


# ==============================================================================
# 6. HTML FILE INTEGRITY & JAVASCRIPT VALIDATION
# ==============================================================================
class TestHtmlIntegrityAndJavaScriptSyntax:
    """Stress tests on generated HTML file, CSS reset, and client-side JavaScript."""

    def test_html_css_and_dom_elements(self, tmp_path):
        """Verifies HTML contains all required DOM structure, styles, and HUD IDs."""
        res = curva_engine.reconstruct_curve("1", "0.5", s0=0.0, s1=4.0, num_points=80)
        out_html = tmp_path / "test_dom.html"
        curva_viz.export_interactive_html(res, str(out_html))
        assert out_html.exists()

        html_text = out_html.read_text(encoding="utf-8")

        # 1. DOCTYPE and viewport
        assert "<!DOCTYPE html>" in html_text
        assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in html_text

        # 2. Responsive CSS reset
        assert "width: 100vw;" in html_text
        assert "height: 100vh;" in html_text
        assert "height: 100dvh;" in html_text
        assert "overflow: hidden;" in html_text

        # 3. DOM Containers
        assert 'id="plot-container"' in html_text
        assert 'id="fundamental_curve_plot"' in html_text
        assert 'id="hud-card"' in html_text

        # 4. HUD metric fields
        assert 'id="hud-s"' in html_text
        assert 'id="hud-r"' in html_text
        assert 'id="hud-kappa"' in html_text
        assert 'id="hud-tau"' in html_text
        assert 'id="hud-rho"' in html_text

        # 5. Custom JavaScript event listeners
        assert "plotly_click" in html_text
        assert "plotly_sliderchange" in html_text
        assert "plotly_animatingframe" in html_text
        assert "window.addEventListener(\"resize\"" in html_text

    def test_javascript_syntax_with_node(self, tmp_path):
        """Extracts JavaScript scripts from generated HTML and parses them with Node.js to prove 0 syntax errors."""
        res = curva_engine.reconstruct_curve("s", "1", s0=0.0, s1=3.0, num_points=50)
        out_html = tmp_path / "test_js_syntax.html"
        curva_viz.export_interactive_html(res, str(out_html))

        html_text = out_html.read_text(encoding="utf-8")

        # Extract all <script>...</script> contents
        script_pattern = re.compile(r"<script[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE)
        scripts = script_pattern.findall(html_text)
        assert len(scripts) > 0, "No script tags found in HTML!"

        for i, script_content in enumerate(scripts):
            # Ignore CDN script tags with src
            if not script_content.strip():
                continue

            # Write script to temporary JS file
            js_file = tmp_path / f"extracted_script_{i}.js"
            js_file.write_text(script_content, encoding="utf-8")

            # Run node -c (syntax check only)
            proc = subprocess.run(["node", "-c", str(js_file)], capture_output=True, text=True)
            assert proc.returncode == 0, f"Node.js syntax error in script {i}:\n{proc.stderr}\nCode:\n{script_content[:500]}"

    def test_html_export_with_bundled_plotlyjs(self, tmp_path):
        """Verifies include_plotlyjs=True produces a self-contained offline HTML file."""
        res = curva_engine.reconstruct_curve("1", "0", s0=0.0, s1=2.0, num_points=30)
        out_html = tmp_path / "test_bundled.html"
        curva_viz.export_interactive_html(res, str(out_html), include_plotlyjs=True)
        assert out_html.exists()

        content = out_html.read_text(encoding="utf-8")
        # Bundled plotly.js is several megabytes of JS inlined
        assert len(content) > 1_000_000
        assert '<script src="https://cdn.plot.ly' not in content
        assert "<script>" in content
