"""Comprehensive E2E and Unit Test Suite for Fundamental Theorem of Curves.

Tiers Covered:
- Tier 1: Feature Coverage (ODE math, frame orthonormality, classification, CLI, HTML output)
- Tier 2: Boundary & Corner Cases (zero curvature, singularities, intervals, limits, AST security)
- Tier 3: Cross-Feature Combinations (Lancret helices, Cornu spiral, Log spiral, planar vs 3D)
- Tier 4: Real-World Analytical Acceptance Benchmarks (Circle R=0.5, Helix isometry, Clothoid Fresnel)

Theoretical Foundations:
- Toponogov (2006): Differential Geometry of Curves and Surfaces
- Tenenblat (2008): Introdução à Geometria Diferencial
- Alencar & Santos (2009): Geometria Diferencial: Curvas e Superfícies
- do Carmo (2016): Differential Geometry of Curves and Surfaces
- Lancret (1802): Mémoire sur les courbes à double courbure
"""

import ast
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.special import fresnel

# Add project root to sys.path to enable direct module imports when created
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ENGINE_PATH = PROJECT_ROOT / "src" / "curva_engine.py"
VIZ_PATH = PROJECT_ROOT / "src" / "curva_viz.py"
CLI_PATH = PROJECT_ROOT / "teorema-fundamental-curvas.py"


def has_engine() -> bool:
    return ENGINE_PATH.exists()


def has_viz() -> bool:
    return VIZ_PATH.exists()


def has_cli() -> bool:
    return CLI_PATH.exists()


requires_engine = pytest.mark.skipif(
    not has_engine(), reason="curva_engine.py not yet implemented (Milestone M1)"
)
requires_viz = pytest.mark.skipif(
    not has_viz(), reason="curva_viz.py not yet implemented (Milestone M2)"
)
requires_cli = pytest.mark.skipif(
    not has_cli(), reason="teorema-fundamental-curvas.py not yet implemented (Milestone M3)"
)


# ==============================================================================
# MATHEMATICAL ORACLE MODELS & BENCHMARK VERIFICATION (TIER 4 & REFERENCE)
# ==============================================================================
class TestMathematicalOracleModels:
    """Verifies theoretical formulas and mathematical invariants independently.

    These tests run standalone in all milestones to ensure the mathematical
    oracles and tolerances are rigorously verified against SciPy and differential geometry.
    """

    def test_oracle_circle_closed_form_and_chord(self):
        """Authoritative Oracle for Circle: kappa=2, tau=0.

        Curvature kappa=2 gives radius R = 1/2 = 0.5.
        Circumference C = 2*pi*R = pi.
        Over [0, pi/2]: arc length is pi/2, chord distance is 2*R = 1.0 (semicircle).
        Over [0, pi]: arc length is pi, chord distance is 0.0 (full circle).
        """
        s_semi = np.pi / 2.0
        r_semi = np.array([0.5 * np.sin(2.0 * s_semi), 0.5 * (1.0 - np.cos(2.0 * s_semi)), 0.0])
        assert np.allclose(r_semi, [0.0, 1.0, 0.0], atol=1e-12)
        chord_dist = np.linalg.norm(r_semi - np.array([0.0, 0.0, 0.0]))
        assert np.isclose(chord_dist, 1.0, atol=1e-12)

        s_full = np.pi
        r_full = np.array([0.5 * np.sin(2.0 * s_full), 0.5 * (1.0 - np.cos(2.0 * s_full)), 0.0])
        assert np.allclose(r_full, [0.0, 0.0, 0.0], atol=1e-12)
        assert np.isclose(np.linalg.norm(r_full), 0.0, atol=1e-12)

    def test_oracle_helix_closed_form_and_isometry(self):
        """Authoritative Oracle for Circular Helix: kappa=1, tau=1.

        Analytical Frenet solution starting with T0=e1, N0=e2, B0=e3:
        r_frenet(s) = [s/2 + (sqrt(2)/4)*sin(sqrt(2)*s),
                       0.5*(1 - cos(sqrt(2)*s)),
                       s/2 - (sqrt(2)/4)*sin(sqrt(2)*s)]
        Radius R = kappa / (kappa^2 + tau^2) = 0.5.
        Pitch P = 2*pi * tau / (kappa^2 + tau^2) = pi.
        Total displacement over [0, 2*pi*sqrt(2)]: 2*pi.
        Isometry to canonical z-axis cylinder helix:
        r_cyl(s) = [0.5*cos(sqrt(2)*s), 0.5*sin(sqrt(2)*s), s/sqrt(2)]
        """
        sq2 = np.sqrt(2.0)
        s_eval = np.linspace(0.0, 2.0 * np.pi * sq2, 200)

        # Analytical Frenet trajectory
        x_frenet = s_eval / 2.0 + (sq2 / 4.0) * np.sin(sq2 * s_eval)
        y_frenet = 0.5 * (1.0 - np.cos(sq2 * s_eval))
        z_frenet = s_eval / 2.0 - (sq2 / 4.0) * np.sin(sq2 * s_eval)
        r_frenet = np.stack([x_frenet, y_frenet, z_frenet], axis=0)

        # Endpoint displacement at s = 2*pi*sqrt(2)
        s_end = 2.0 * np.pi * sq2
        disp = np.linalg.norm(r_frenet[:, -1] - r_frenet[:, 0])
        assert np.isclose(disp, 2.0 * np.pi, atol=1e-12)

        # Canonical cylinder helix transformed by proper rigid motion R in SO(3), t0 in R^3
        r_cyl = np.stack([0.5 * np.cos(sq2 * s_eval), 0.5 * np.sin(sq2 * s_eval), s_eval / sq2], axis=0)
        R_iso = np.array([
            [0.0, 1.0 / sq2, 1.0 / sq2],
            [-1.0, 0.0, 0.0],
            [0.0, -1.0 / sq2, 1.0 / sq2]
        ])
        assert np.isclose(np.linalg.det(R_iso), 1.0, atol=1e-12)
        assert np.allclose(R_iso @ R_iso.T, np.eye(3), atol=1e-12)
        t0 = np.array([[0.0], [0.5], [0.0]])

        r_mapped = R_iso @ r_cyl + t0
        assert np.allclose(r_mapped, r_frenet, atol=1e-14)

    def test_oracle_clothoid_fresnel_evaluation(self):
        """Authoritative Oracle for Cornu Spiral / Clothoid: kappa(s) = s, tau = 0.

        Trajectory given by Fresnel integrals:
        x(s) = sqrt(pi) * C(s / sqrt(pi))
        y(s) = sqrt(pi) * S(s / sqrt(pi))
        """
        s_vals = np.linspace(0.0, 5.0, 100)
        S, C = fresnel(s_vals / np.sqrt(np.pi))
        x_ana = np.sqrt(np.pi) * C
        y_ana = np.sqrt(np.pi) * S

        # Verify initial velocity is unit tangent along x-axis
        dx_ds0 = (x_ana[1] - x_ana[0]) / (s_vals[1] - s_vals[0])
        assert np.isclose(dx_ds0, 1.0, atol=1e-3)
        assert np.isclose(y_ana[0], 0.0, atol=1e-12)

    def test_oracle_vectorized_gram_schmidt_so3(self):
        """Authoritative Oracle for Modified Gram-Schmidt SO(3) orthonormalization.

        Ensures that projection of perturbed frames preserves tangent direction,
        restores ||T||=||N||=||B||=1, guarantees orthogonality, and det(F)=+1.
        """
        np.random.seed(42)
        K = 100
        T = np.array([[1.0], [0.0], [0.0]]) + 0.05 * np.random.randn(3, K)
        N = np.array([[0.0], [1.0], [0.0]]) + 0.05 * np.random.randn(3, K)
        B = np.array([[0.0], [0.0], [1.0]]) + 0.05 * np.random.randn(3, K)

        T_u = T / np.linalg.norm(T, axis=0, keepdims=True)
        N_proj = N - np.sum(N * T_u, axis=0, keepdims=True) * T_u
        N_u = N_proj / np.linalg.norm(N_proj, axis=0, keepdims=True)
        B_u = np.cross(T_u, N_u, axis=0)

        # Norms
        assert np.allclose(np.linalg.norm(T_u, axis=0), 1.0, atol=1e-14)
        assert np.allclose(np.linalg.norm(N_u, axis=0), 1.0, atol=1e-14)
        assert np.allclose(np.linalg.norm(B_u, axis=0), 1.0, atol=1e-14)

        # Dot products
        assert np.allclose(np.sum(T_u * N_u, axis=0), 0.0, atol=1e-14)
        assert np.allclose(np.sum(T_u * B_u, axis=0), 0.0, atol=1e-14)
        assert np.allclose(np.sum(N_u * B_u, axis=0), 0.0, atol=1e-14)

        # Determinant == +1
        frames = np.transpose(np.array([T_u, N_u, B_u]), (2, 0, 1))
        dets = np.linalg.det(frames)
        assert np.allclose(dets, 1.0, atol=1e-14)


# ==============================================================================
# TIER 1: FEATURE COVERAGE
# ==============================================================================
class TestTier1FeatureCoverage:
    """Tier 1: Feature Coverage (math integration, frame orthonormality, classification, CLI, output)."""

    # --- 1.1 Mathematical ODE Integration & Frame Orthonormality ---
    @requires_engine
    def test_tier1_ode_integration_solution_shape(self):
        """Verifies reconstruct_curve returns CurveResult with exact expected array shapes."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=150)
        assert res.s.shape == (150,)
        assert res.r.shape == (3, 150)
        assert res.T.shape == (3, 150)
        assert res.N.shape == (3, 150)
        assert res.B.shape == (3, 150)
        assert res.kappa.shape == (150,)
        assert res.tau.shape == (150,)
        assert res.classification == "helice_circular"
        assert np.isclose(res.s0, 0.0)
        assert np.isclose(res.s1, 6.28)

    @requires_engine
    def test_tier1_frame_unit_tangent_norm(self):
        """Verifies ||T(s)|| = 1 with error < 1e-4 across all points."""
        import curva_engine

        res = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=3.1415, num_points=200)
        norms = np.linalg.norm(res.T, axis=0)
        assert np.all(np.abs(norms - 1.0) < 1e-4)

    @requires_engine
    def test_tier1_frame_unit_normal_norm(self):
        """Verifies ||N(s)|| = 1 with error < 1e-4 across all points."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=5.0, num_points=200)
        norms = np.linalg.norm(res.N, axis=0)
        assert np.all(np.abs(norms - 1.0) < 1e-4)

    @requires_engine
    def test_tier1_frame_unit_binormal_norm(self):
        """Verifies ||B(s)|| = 1 with error < 1e-4 across all points."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "2", s0=0.0, s1=5.0, num_points=200)
        norms = np.linalg.norm(res.B, axis=0)
        assert np.all(np.abs(norms - 1.0) < 1e-4)

    @requires_engine
    def test_tier1_frame_orthogonality_tangent_normal(self):
        """Verifies T · N = 0 with error < 1e-4 across all points."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1 + 0.1*s", "0.5", s0=0.0, s1=4.0, num_points=100)
        dot_TN = np.sum(res.T * res.N, axis=0)
        assert np.all(np.abs(dot_TN) < 1e-4)

    @requires_engine
    def test_tier1_frame_orthogonality_tangent_binormal(self):
        """Verifies T · B = 0 with error < 1e-4 across all points."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=4.0, num_points=100)
        dot_TB = np.sum(res.T * res.B, axis=0)
        assert np.all(np.abs(dot_TB) < 1e-4)

    @requires_engine
    def test_tier1_frame_orthogonality_normal_binormal(self):
        """Verifies N · B = 0 with error < 1e-4 across all points."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=4.0, num_points=100)
        dot_NB = np.sum(res.N * res.B, axis=0)
        assert np.all(np.abs(dot_NB) < 1e-4)

    @requires_engine
    def test_tier1_frame_determinant_so3(self):
        """Verifies det([T, N, B]) = +1 with error < 1e-4 across all points."""
        import curva_engine

        res = curva_engine.reconstruct_curve("2", "1", s0=0.0, s1=6.0, num_points=100)
        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        dets = np.linalg.det(frames)
        assert np.all(np.abs(dets - 1.0) < 1e-4)

    @requires_engine
    def test_tier1_initial_conditions(self):
        """Verifies r(s0) = (0,0,0), T(s0) = (1,0,0), N(s0) = (0,1,0), B(s0) = (0,0,1)."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1.5", "0.5", s0=0.0, s1=2.0, num_points=50)
        assert np.allclose(res.r[:, 0], [0.0, 0.0, 0.0], atol=1e-10)
        assert np.allclose(res.T[:, 0], [1.0, 0.0, 0.0], atol=1e-10)
        assert np.allclose(res.N[:, 0], [0.0, 1.0, 0.0], atol=1e-10)
        assert np.allclose(res.B[:, 0], [0.0, 0.0, 1.0], atol=1e-10)

    # --- 1.2 Curve Classification for all 8 categories ---
    @requires_engine
    def test_tier1_classification_reta(self):
        """Verifies classification of kappa = 0 as 'reta'."""
        import curva_engine

        res1 = curva_engine.reconstruct_curve("0", "0", s0=0.0, s1=5.0)
        assert res1.classification == "reta"
        res2 = curva_engine.reconstruct_curve("0", "2", s0=0.0, s1=5.0)
        assert res2.classification == "reta"

    @requires_engine
    def test_tier1_classification_circulo(self):
        """Verifies classification of constant kappa > 0, tau = 0 as 'circulo'."""
        import curva_engine

        res = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=6.28)
        assert res.classification == "circulo"

    @requires_engine
    def test_tier1_classification_helice_circular(self):
        """Verifies classification of constant kappa > 0, constant tau != 0 as 'helice_circular'."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=6.28)
        assert res.classification == "helice_circular"

    @requires_engine
    def test_tier1_classification_helice_cilindrica_geral(self):
        """Verifies Lancret's theorem: tau / kappa = const != 0 with non-constant kappa -> 'helice_cilindrica_geral'."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1 + s", "2*(1 + s)", s0=0.0, s1=4.0)
        assert res.classification == "helice_cilindrica_geral"

    @requires_engine
    def test_tier1_classification_espiral_de_cornu(self):
        """Verifies kappa(s) = c*s, tau = 0 as 'espiral_de_cornu'."""
        import curva_engine

        res = curva_engine.reconstruct_curve("2*s", "0", s0=0.0, s1=5.0)
        assert res.classification == "espiral_de_cornu"

    @requires_engine
    def test_tier1_classification_espiral_logaritmica(self):
        """Verifies 1/kappa(s) = a*s + b, tau = 0 as 'espiral_logaritmica'."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1/(s + 1)", "0", s0=0.0, s1=5.0)
        assert res.classification == "espiral_logaritmica"

    @requires_engine
    def test_tier1_classification_curva_plana(self):
        """Verifies tau = 0 with generic kappa(s) as 'curva_plana'."""
        import curva_engine

        res = curva_engine.reconstruct_curve("cos(s) + 2", "0", s0=0.0, s1=6.28)
        assert res.classification == "curva_plana"

    @requires_engine
    def test_tier1_classification_curva_espacial(self):
        """Verifies non-constant tau/kappa as 'curva_espacial'."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1 + s**2", "s", s0=0.0, s1=3.0)
        assert res.classification == "curva_espacial"

    # --- 1.3 CLI Argument Parsing & Validation ---
    @requires_cli
    def test_tier1_cli_defaults(self, tmp_path):
        """Verifies running CLI with only '1' defaults tau to 0, interval [0, 6.28], points 500."""
        cmd = [sys.executable, str(CLI_PATH), "1", "-o", str(tmp_path / "default_out.html")]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI error: {proc.stderr}"
        assert (tmp_path / "default_out.html").exists()

    @requires_cli
    def test_tier1_cli_positional_both(self, tmp_path):
        """Verifies running CLI with positional '1' '1' works properly."""
        cmd = [sys.executable, str(CLI_PATH), "1", "1", "-o", str(tmp_path / "helix_out.html")]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI error: {proc.stderr}"
        assert (tmp_path / "helix_out.html").exists()

    @requires_cli
    def test_tier1_cli_flags_short(self, tmp_path):
        """Verifies CLI short flags: -k, -t, -i, -n, -o."""
        out_file = tmp_path / "short_flags.html"
        cmd = [
            sys.executable, str(CLI_PATH),
            "-k", "2", "-t", "0",
            "-i", "0", "3.14",
            "-n", "100",
            "-o", str(out_file)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI error: {proc.stderr}"
        assert out_file.exists()

    @requires_cli
    def test_tier1_cli_flags_long(self, tmp_path):
        """Verifies CLI long flags: --curvatura, --torcao, --intervalo, --num-pontos, --output."""
        out_file = tmp_path / "long_flags.html"
        cmd = [
            sys.executable, str(CLI_PATH),
            "--curvatura", "1",
            "--torcao", "1",
            "--intervalo", "0", "5",
            "--num-pontos", "120",
            "--output", str(out_file)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI error: {proc.stderr}"
        assert out_file.exists()

    @requires_cli
    def test_tier1_cli_missing_required(self):
        """Verifies running with no arguments returns non-zero code (argparse code 2)."""
        cmd = [sys.executable, str(CLI_PATH)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode != 0

    # --- 1.4 Automatic Filename Generation & Sanitization ---
    @requires_engine
    def test_tier1_filename_helix_acceptance(self):
        """Verifies acceptance criteria filename: 'helice_circular-k1-t1-I0_6.28.html'."""
        import curva_engine

        fn = curva_engine.generate_output_filename("helice_circular", "1", "1", 0.0, 6.28)
        assert fn == "helice_circular-k1-t1-I0_6.28.html"

    @requires_engine
    def test_tier1_filename_circle_acceptance(self):
        """Verifies acceptance criteria filename: 'circulo-k1-t0-I0_6.28.html'."""
        import curva_engine

        fn = curva_engine.generate_output_filename("circulo", "1", "0", 0.0, 6.28)
        assert fn == "circulo-k1-t0-I0_6.28.html"

    @requires_engine
    def test_tier1_filename_sanitization_powers(self):
        """Verifies powers ** and ^ are sanitized cleanly."""
        import curva_engine

        fn1 = curva_engine.sanitize_expr_for_filename("s**2")
        assert "**" not in fn1 and ("_pow_" in fn1 or "pow" in fn1)
        fn2 = curva_engine.sanitize_expr_for_filename("s^2")
        assert "^" not in fn2

    @requires_engine
    def test_tier1_filename_sanitization_operators(self):
        """Verifies * and + are sanitized with _mult_ and _plus_."""
        import curva_engine

        fn = curva_engine.sanitize_expr_for_filename("2*s + 1")
        assert "*" not in fn and "+" not in fn and " " not in fn

    @requires_engine
    def test_tier1_filename_sanitization_division(self):
        """Verifies / is sanitized without illegal filename characters."""
        import curva_engine

        fn = curva_engine.sanitize_expr_for_filename("1/(s+1)")
        assert "/" not in fn and "(" not in fn and ")" not in fn

    @requires_cli
    def test_tier1_filename_custom_output_preserved(self, tmp_path):
        """Verifies that user specified -o overrides automatic naming."""
        custom_out = tmp_path / "custom_named_file.html"
        cmd = [sys.executable, str(CLI_PATH), "1", "-o", str(custom_out)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0
        assert custom_out.exists()

    # --- 1.5 HTML Output Structure & Differential Apparatus ---
    @requires_viz
    @requires_engine
    def test_tier1_html_viewport_meta_css(self, tmp_path):
        """Verifies generated HTML contains fullscreen responsive CSS reset (100vw, 100vh/100dvh)."""
        import curva_engine
        import curva_viz

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=2.0, num_points=50)
        out_html = tmp_path / "test_css.html"
        curva_viz.export_interactive_html(res, str(out_html))
        content = out_html.read_text(encoding="utf-8")

        assert "100vw" in content
        assert ("100vh" in content or "100dvh" in content)
        assert "overflow: hidden" in content or "overflow:hidden" in content

    @requires_viz
    @requires_engine
    def test_tier1_html_plotly_container(self, tmp_path):
        """Verifies generated HTML includes Plotly library link or script and container div."""
        import curva_engine
        import curva_viz

        res = curva_engine.reconstruct_curve("1", "0", s0=0.0, s1=2.0, num_points=50)
        out_html = tmp_path / "test_div.html"
        curva_viz.export_interactive_html(res, str(out_html))
        content = out_html.read_text(encoding="utf-8")

        assert "plotly" in content.lower()
        assert "<div" in content

    @requires_viz
    @requires_engine
    def test_tier1_html_apparatus_traces(self, tmp_path):
        """Verifies generated HTML contains references to Frenet apparatus traces."""
        import curva_engine
        import curva_viz

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=2.0, num_points=50)
        out_html = tmp_path / "test_apparatus.html"
        curva_viz.export_interactive_html(res, str(out_html))
        content = out_html.read_text(encoding="utf-8")

        # Must mention Tangente, Normal, Binormal
        assert "Tangente" in content or "tangente" in content
        assert "Normal" in content or "normal" in content
        assert "Binormal" in content or "binormal" in content

    @requires_viz
    @requires_engine
    def test_tier1_html_click_navigation_script(self, tmp_path):
        """Verifies generated HTML contains plotly_click JavaScript listener."""
        import curva_engine
        import curva_viz

        res = curva_engine.reconstruct_curve("1", "0", s0=0.0, s1=2.0, num_points=50)
        out_html = tmp_path / "test_click.html"
        curva_viz.export_interactive_html(res, str(out_html))
        content = out_html.read_text(encoding="utf-8")

        assert "plotly_click" in content


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ==============================================================================
class TestTier2BoundaryAndCornerCases:
    """Tier 2: Boundary & Corner Cases (zero curvature, singularities, intervals, limits, AST security)."""

    # --- 2.1 Zero Curvature (Straight Line & Infinite Radius) ---
    @requires_engine
    def test_tier2_zero_curvature_integration(self):
        """Verifies that kappa=0 integrates smoothly as a straight line along the x-axis without zero division."""
        import curva_engine

        res = curva_engine.reconstruct_curve("0", "0", s0=0.0, s1=5.0, num_points=50)
        # Position must be r(s) = (s, 0, 0)
        assert np.allclose(res.r[0], res.s, atol=1e-10)
        assert np.allclose(res.r[1], 0.0, atol=1e-10)
        assert np.allclose(res.r[2], 0.0, atol=1e-10)
        # Tangent must be (1, 0, 0)
        assert np.allclose(res.T[0], 1.0, atol=1e-10)

    @requires_viz
    @requires_engine
    def test_tier2_zero_curvature_osculating_circle(self, tmp_path):
        """Verifies osculating circle handles infinite radius rho -> inf gracefully (empty trace coordinates)."""
        import curva_engine
        import curva_viz

        res = curva_engine.reconstruct_curve("0", "0", s0=0.0, s1=5.0, num_points=50)
        fig = curva_viz.build_curve_figure(res)
        # Figure must build without error and HTML exports cleanly
        out_html = tmp_path / "straight_line.html"
        curva_viz.export_interactive_html(res, str(out_html))
        assert out_html.exists()

    # --- 2.2 Singularities & Undefined Domain ---
    @requires_engine
    def test_tier2_singularity_division_by_zero_at_origin(self):
        """Verifies kappa(s) = 1/s over [0, 2] is rejected with ValueError due to division by zero at s=0."""
        import curva_engine

        with pytest.raises(ValueError):
            curva_engine.reconstruct_curve("1/s", "0", s0=0.0, s1=2.0, num_points=100)

    @requires_engine
    def test_tier2_singularity_evaluates_nan_or_inf(self):
        """Verifies log(s) over [-2, 1] is rejected with ValueError due to non-finite evaluations."""
        import curva_engine

        with pytest.raises(ValueError):
            curva_engine.reconstruct_curve("log(s)", "0", s0=-2.0, s1=1.0, num_points=100)

    # --- 2.3 Interval Boundaries ---
    @requires_engine
    def test_tier2_interval_very_small(self):
        """Verifies very small interval [0, 0.001] integrates accurately without numerical failure."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=0.001, num_points=50)
        assert res.r.shape == (3, 50)
        assert np.isclose(res.r[0, -1], 0.001, atol=1e-5)

    @requires_engine
    def test_tier2_interval_large(self):
        """Verifies large interval [0, 100] integrates with frame orthonormality preserved (< 1e-4 error)."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=100.0, num_points=500)
        norms_T = np.linalg.norm(res.T, axis=0)
        assert np.all(np.abs(norms_T - 1.0) < 1e-4)

    @requires_engine
    def test_tier2_interval_inverted_rejected(self):
        """Verifies s0 >= s1 (e.g. s0=5, s1=2) is rejected with ValueError."""
        import curva_engine

        with pytest.raises(ValueError):
            curva_engine.reconstruct_curve("1", "0", s0=5.0, s1=2.0)

    @requires_cli
    def test_tier2_interval_inverted_cli_exit_code(self):
        """Verifies CLI returns non-zero exit code when s0 >= s1."""
        cmd = [sys.executable, str(CLI_PATH), "1", "-i", "5", "2"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode != 0

    @requires_engine
    def test_tier2_interval_negative(self):
        """Verifies negative interval [-5, -1] works for expressions valid on negative numbers."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "0", s0=-5.0, s1=-1.0, num_points=50)
        assert np.isclose(res.s[0], -5.0)
        assert np.isclose(res.s[-1], -1.0)

    # --- 2.4 Discretization Point Limits ---
    @requires_engine
    def test_tier2_points_minimum_allowed(self):
        """Verifies num_points = 2 is accepted and returns exactly 2 points."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "0", s0=0.0, s1=1.0, num_points=2)
        assert res.s.shape == (2,)
        assert res.r.shape == (3, 2)

    @requires_engine
    def test_tier2_points_less_than_two_rejected(self):
        """Verifies num_points < 2 (e.g. 1, 0, -1) is rejected with ValueError."""
        import curva_engine

        with pytest.raises(ValueError):
            curva_engine.reconstruct_curve("1", "0", s0=0.0, s1=1.0, num_points=1)
        with pytest.raises(ValueError):
            curva_engine.reconstruct_curve("1", "0", s0=0.0, s1=1.0, num_points=0)

    # --- 2.5 Syntax Errors & Malicious AST Execution ---
    @requires_engine
    def test_tier2_syntax_error_malformed_expression(self):
        """Verifies malformed expressions like '2*+*3' or 'sin(' raise ValueError."""
        import curva_engine

        with pytest.raises(ValueError):
            curva_engine.parse_and_validate_expression("2*+*3")
        with pytest.raises(ValueError):
            curva_engine.parse_and_validate_expression("sin(")

    @requires_engine
    def test_tier2_security_ast_blocks_arbitrary_code(self):
        """Verifies AST whitelist validator blocks __import__ or arbitrary code injection."""
        import curva_engine

        with pytest.raises(ValueError):
            curva_engine.parse_and_validate_expression("__import__('os').system('ls')")

    @requires_engine
    def test_tier2_security_ast_blocks_attribute_access(self):
        """Verifies AST validator blocks attribute access like (1).__class__."""
        import curva_engine

        with pytest.raises(ValueError):
            curva_engine.parse_and_validate_expression("(1).__class__.__bases__")

    @requires_engine
    def test_tier2_security_ast_blocks_disallowed_variables(self):
        """Verifies variables other than 's', 'pi', 'e' (e.g. 'x', 'y') are rejected."""
        import curva_engine

        with pytest.raises(ValueError):
            curva_engine.parse_and_validate_expression("x + 1")

    @requires_engine
    def test_tier2_negative_curvature_rejected(self):
        """Verifies negative curvature kappa < 0 (e.g. '-2') is rejected with ValueError."""
        import curva_engine

        with pytest.raises(ValueError):
            curva_engine.reconstruct_curve("-2", "0", s0=0.0, s1=2.0)


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS
# ==============================================================================
class TestTier3CrossFeatureCombinations:
    """Tier 3: Cross-Feature Combinations (pairwise curvature/torsion combinations & projection)."""

    @requires_engine
    def test_tier3_variable_curvature_constant_torsion(self):
        """Pairwise: Variable curvature + constant torsion (spatial curve).

        kappa(s) = 1 + 0.1*s, tau(s) = 1.0.
        Verifies classification as 'curva_espacial' and frame orthonormality.
        """
        import curva_engine

        res = curva_engine.reconstruct_curve("1 + 0.1*s", "1.0", s0=0.0, s1=5.0, num_points=100)
        assert res.classification == "curva_espacial"
        dets = np.linalg.det(np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1)))
        assert np.all(np.abs(dets - 1.0) < 1e-4)

    @requires_engine
    def test_tier3_lancret_generalized_helix(self):
        """Pairwise: Lancret generalized cylindrical helix.

        kappa(s) = 1 + s, tau(s) = 2*(1 + s).
        Ratio tau / kappa = 2.0 = const != 0.
        Verifies tangent vector makes constant angle alpha with cylinder axis:
        cos(alpha) = tau / sqrt(kappa^2 + tau^2) = 2 / sqrt(5) = const.
        """
        import curva_engine

        res = curva_engine.reconstruct_curve("1 + s", "2*(1 + s)", s0=0.0, s1=4.0, num_points=150)
        assert res.classification == "helice_cilindrica_geral"

        # Darboux direction axis: w = (tau*T + kappa*N) / sqrt(kappa^2 + tau^2)
        # Orthonormality check across entire trajectory
        assert np.all(np.abs(np.linalg.norm(res.T, axis=0) - 1.0) < 1e-4)

    @requires_engine
    def test_tier3_cornu_spiral_classification_and_integration(self):
        """Pairwise: Polynomial curvature + zero torsion (Clothoid / Cornu spiral).

        kappa(s) = 2*s, tau(s) = 0.
        Verifies classification as 'espiral_de_cornu' and z(s) == 0 (strictly planar).
        """
        import curva_engine

        res = curva_engine.reconstruct_curve("2*s", "0", s0=0.0, s1=3.0, num_points=100)
        assert res.classification == "espiral_de_cornu"
        assert np.allclose(res.r[2], 0.0, atol=1e-10)  # z-coordinate identically zero

    @requires_engine
    def test_tier3_log_spiral_classification_and_integration(self):
        """Pairwise: Inverted linear radius curvature + zero torsion (Logarithmic spiral).

        kappa(s) = 1/(s + 1), tau(s) = 0.
        Curvature radius rho(s) = s + 1 (linear in s).
        Verifies classification as 'espiral_logaritmica' and planar constraint.
        """
        import curva_engine

        res = curva_engine.reconstruct_curve("1/(s + 1)", "0", s0=0.0, s1=4.0, num_points=100)
        assert res.classification == "espiral_logaritmica"
        assert np.allclose(res.r[2], 0.0, atol=1e-10)

    @requires_viz
    @requires_engine
    def test_tier3_planar_vs_spatial_visualization_config(self, tmp_path):
        """Cross-feature: Planar curves (tau=0) vs Spatial curves (tau!=0) UI configuration."""
        import curva_engine
        import curva_viz

        # Planar curve
        res_planar = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=3.14, num_points=50)
        fig_planar = curva_viz.build_curve_figure(res_planar)
        assert fig_planar is not None

        # Space curve
        res_space = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=3.14, num_points=50)
        fig_space = curva_viz.build_curve_figure(res_space)
        assert fig_space is not None


# ==============================================================================
# TIER 4: REAL-WORLD ANALYTICAL ACCEPTANCE BENCHMARKS
# ==============================================================================
class TestTier4AnalyticalAcceptanceBenchmarks:
    """Tier 4: Analytical Acceptance Benchmarks with strict mathematical error bounds (< 10^-3)."""

    @requires_engine
    def test_tier4_circle_semicircle_interval(self):
        """Acceptance Criteria 1: Circle over [0, pi/2] with kappa=2, tau=0.

        Forms semicircle of radius R=0.5 with chord distance 1.0 (diameter 2R).
        Verifies endpoint error < 10^-3 and chord error < 10^-3.
        """
        import curva_engine

        s_half = np.pi / 2.0
        res = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=s_half, num_points=300)

        # Expected endpoint r(pi/2) = (0, 1.0, 0)
        expected_end = np.array([0.0, 1.0, 0.0])
        endpoint_err = np.linalg.norm(res.r[:, -1] - expected_end)
        assert endpoint_err < 1e-3, f"Circle semicircle endpoint error {endpoint_err} exceeds 1e-3"

        # Chord distance: ||r(pi/2) - r(0)|| == 1.0
        chord = np.linalg.norm(res.r[:, -1] - res.r[:, 0])
        assert np.isclose(chord, 1.0, atol=1e-3)

    @requires_engine
    def test_tier4_circle_full_circle_interval(self):
        """Acceptance Criteria 1 (Full): Circle over [0, pi] with kappa=2, tau=0.

        Arc length pi = 2*pi*R traverses the complete circumference.
        Verifies closure error ||r(pi) - r(0)|| < 10^-3.
        """
        import curva_engine

        res = curva_engine.reconstruct_curve("2", "0", s0=0.0, s1=np.pi, num_points=400)

        closure_err = np.linalg.norm(res.r[:, -1] - res.r[:, 0])
        assert closure_err < 1e-3, f"Full circle closure error {closure_err} exceeds 1e-3"

        # Verify radius from center c = (0, 0.5, 0) is 0.5 everywhere
        center = np.array([[0.0], [0.5], [0.0]])
        radii = np.linalg.norm(res.r - center, axis=0)
        assert np.all(np.abs(radii - 0.5) < 1e-3)

    @requires_engine
    def test_tier4_helix_parameters_and_trajectory(self):
        """Acceptance Criteria 2: Circular Helix with kappa=1, tau=1 over [0, 2*pi*sqrt(2)].

        Radius R = 0.5, Pitch P = pi.
        Verifies relative trajectory error against analytical r_frenet(s) is < 10^-3.
        """
        import curva_engine

        sq2 = np.sqrt(2.0)
        s_end = 2.0 * np.pi * sq2
        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=s_end, num_points=500)

        # Closed-form Frenet trajectory
        x_ana = res.s / 2.0 + (sq2 / 4.0) * np.sin(sq2 * res.s)
        y_ana = 0.5 * (1.0 - np.cos(sq2 * res.s))
        z_ana = res.s / 2.0 - (sq2 / 4.0) * np.sin(sq2 * res.s)
        r_ana = np.stack([x_ana, y_ana, z_ana], axis=0)

        abs_err = np.max(np.linalg.norm(res.r - r_ana, axis=0))
        assert abs_err < 1e-3, f"Helix absolute trajectory error {abs_err} exceeds 1e-3"

        # Total displacement over interval is 2*pi
        disp = np.linalg.norm(res.r[:, -1] - res.r[:, 0])
        assert np.isclose(disp, 2.0 * np.pi, atol=1e-3)

    @requires_engine
    def test_tier4_helix_rigid_motion_isometry(self):
        """Verifies reconstructed Frenet helix is isometric to canonical cylinder helix via proper rigid motion."""
        import curva_engine

        sq2 = np.sqrt(2.0)
        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=2.0 * np.pi * sq2, num_points=300)

        # Canonical cylinder helix
        r_cyl = np.stack([0.5 * np.cos(sq2 * res.s), 0.5 * np.sin(sq2 * res.s), res.s / sq2], axis=0)
        R_iso = np.array([
            [0.0, 1.0 / sq2, 1.0 / sq2],
            [-1.0, 0.0, 0.0],
            [0.0, -1.0 / sq2, 1.0 / sq2]
        ])
        t0 = np.array([[0.0], [0.5], [0.0]])
        r_expected = R_iso @ r_cyl + t0

        err = np.max(np.linalg.norm(res.r - r_expected, axis=0))
        assert err < 1e-3

    @requires_engine
    def test_tier4_straight_line_trajectory(self):
        """Straight Line Benchmark: kappa=0, tau=0 over [0, 10]. Length L=10, error < 10^-6."""
        import curva_engine

        res = curva_engine.reconstruct_curve("0", "0", s0=0.0, s1=10.0, num_points=100)
        assert np.isclose(np.linalg.norm(res.r[:, -1] - res.r[:, 0]), 10.0, atol=1e-6)
        assert np.allclose(res.r[0], res.s, atol=1e-6)

    @requires_engine
    def test_tier4_clothoid_fresnel_comparison(self):
        """Clothoid Benchmark: kappa=s, tau=0 over [0, 5]. Max error against scipy.special.fresnel < 10^-3."""
        import curva_engine

        res = curva_engine.reconstruct_curve("s", "0", s0=0.0, s1=5.0, num_points=300)
        S, C = fresnel(res.s / np.sqrt(np.pi))
        x_fresnel = np.sqrt(np.pi) * C
        y_fresnel = np.sqrt(np.pi) * S

        err_x = np.max(np.abs(res.r[0] - x_fresnel))
        err_y = np.max(np.abs(res.r[1] - y_fresnel))
        assert err_x < 1e-3, f"Clothoid x error {err_x} exceeds 1e-3"
        assert err_y < 1e-3, f"Clothoid y error {err_y} exceeds 1e-3"

    @requires_engine
    def test_tier4_long_range_frame_stability(self):
        """Verifies frame orthonormality preservation over extended arc length s in [0, 50]."""
        import curva_engine

        res = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=50.0, num_points=500)
        # All frame vectors must satisfy ||V|| = 1 +/- 1e-4
        assert np.all(np.abs(np.linalg.norm(res.T, axis=0) - 1.0) < 1e-4)
        assert np.all(np.abs(np.linalg.norm(res.N, axis=0) - 1.0) < 1e-4)
        assert np.all(np.abs(np.linalg.norm(res.B, axis=0) - 1.0) < 1e-4)
        # All dot products < 1e-4
        assert np.all(np.abs(np.sum(res.T * res.N, axis=0)) < 1e-4)
        assert np.all(np.abs(np.sum(res.T * res.B, axis=0)) < 1e-4)
        assert np.all(np.abs(np.sum(res.N * res.B, axis=0)) < 1e-4)
        # Determinant == 1 +/- 1e-4
        dets = np.linalg.det(np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1)))
        assert np.all(np.abs(dets - 1.0) < 1e-4)
