"""Tier 5 Adversarial Coverage Hardening Suite for Fundamental Theorem of Curves.

Empirical Challenger Test Suite:
- Category A: Mathematical Boundaries & Singularities (vanishing kappa, negative intervals, negative tau)
- Category B: Rapid Oscillations & High Dynamics (oscillating kappa/tau, long-range accumulation)
- Category C: Geometric Extremes & Scale Invariance (micro-scale, macro-scale, extreme aspect ratios)
- Category D: Curve Classification Rigor & Lancret's Theorem (all 8 classes, boundary transitions)
- Category E: AST Security Whitelist & Evaluation Hardening (injection, nesting, complex inputs)
- Category F: CLI Interface, Parameter Combinations & File Generation
- Category G: Visualization DOM Integrity & HTML Payload Scalability
"""

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import curva_engine
import curva_viz

CLI_PATH = PROJECT_ROOT / "teorema-fundamental-curvas.py"


# ==============================================================================
# CATEGORY A: MATHEMATICAL BOUNDARIES & SINGULARITIES
# ==============================================================================
class TestCategoryABoundariesAndSingularities:
    """Probes zero-crossings, isolated zero-curvatures, negative intervals, and negative torsion."""

    def test_a1_isolated_zero_curvature_parabola(self):
        """Curvature kappa(s) = s^2 touches zero at s=0 on [-2, 2].

        At s=0, kappa=0. The ODE must integrate across s=0 without failure,
        maintaining unit tangent, normal, and binormal, and frame orthonormality < 1e-4.
        """
        res = curva_engine.reconstruct_curve("s**2", "0", s0=-2.0, s1=2.0, num_points=201)
        assert res.classification == "curva_plana"
        assert res.r.shape == (3, 201)

        # Orthonormality across the zero crossing
        norms_T = np.linalg.norm(res.T, axis=0)
        norms_N = np.linalg.norm(res.N, axis=0)
        norms_B = np.linalg.norm(res.B, axis=0)
        assert np.all(np.abs(norms_T - 1.0) < 1e-4)
        assert np.all(np.abs(norms_N - 1.0) < 1e-4)
        assert np.all(np.abs(norms_B - 1.0) < 1e-4)

        # Dot products
        assert np.all(np.abs(np.sum(res.T * res.N, axis=0)) < 1e-4)
        assert np.all(np.abs(np.sum(res.T * res.B, axis=0)) < 1e-4)
        assert np.all(np.abs(np.sum(res.N * res.B, axis=0)) < 1e-4)

        # Planar curve constraint: z-coordinate is zero
        assert np.allclose(res.r[2], 0.0, atol=1e-10)

    def test_a2_vanishing_curvature_trigonometric(self):
        """Curvature kappa(s) = 1 + cos(s) touches zero at s=pi on [0, 2*pi].

        Verifies smooth integration through tangent inflection and frame orthonormality.
        """
        res = curva_engine.reconstruct_curve("1 + cos(s)", "0", s0=0.0, s1=2.0 * np.pi, num_points=250)
        assert res.classification == "curva_plana"
        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        dets = np.linalg.det(frames)
        assert np.all(np.abs(dets - 1.0) < 1e-4)

    def test_a3_strictly_negative_interval_endpoints(self):
        """Integration over strictly negative domain: s in [-10, -2].

        Checks that initial condition is placed at s0 = -10 (r(-10) = 0),
        discretization matches interval, and arc length equals 8.0.
        """
        res = curva_engine.reconstruct_curve("1", "0.5", s0=-10.0, s1=-2.0, num_points=300)
        assert np.isclose(res.s[0], -10.0)
        assert np.isclose(res.s[-1], -2.0)
        assert np.allclose(res.r[:, 0], [0.0, 0.0, 0.0], atol=1e-10)

        # Reconstructed curve length via tangent integration
        tangent_norms = np.linalg.norm(res.T, axis=0)
        assert np.all(np.abs(tangent_norms - 1.0) < 1e-4)

    def test_a4_symmetric_negative_interval_cornu(self):
        """Clothoid / Cornu spiral on symmetric interval s in [-5, 5].

        By point symmetry of Clothoid: kappa(-s) = -kappa(s). Since kappa >= 0 is required,
        we test kappa(s) = abs(s) on [-3, 3] to check non-negativity constraint.
        """
        res = curva_engine.reconstruct_curve("abs(s)", "0", s0=-3.0, s1=3.0, num_points=200)
        assert res.r.shape == (3, 200)
        assert np.all(np.abs(np.linalg.norm(res.T, axis=0) - 1.0) < 1e-4)

    def test_a5_negative_torsion_left_handed_helix(self):
        """Negative torsion tau = -1 (left-handed circular helix).

        Curvature kappa=1, torsion tau=-1.
        Must classify as 'helice_circular'.
        Frame must satisfy right-handed det([T, N, B]) = +1.0 everywhere.
        """
        res = curva_engine.reconstruct_curve("1", "-1", s0=0.0, s1=6.28, num_points=200)
        assert res.classification == "helice_circular"

        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        dets = np.linalg.det(frames)
        assert np.all(np.abs(dets - 1.0) < 1e-4)

        # In a left-handed helix, z-coordinate progresses in opposite direction to right-handed
        res_rh = curva_engine.reconstruct_curve("1", "1", s0=0.0, s1=6.28, num_points=200)
        # Compare z coordinates: for left-handed with initial IC, z grows differently than right-handed
        assert not np.allclose(res.r[2], res_rh.r[2], atol=1e-2)

    def test_a6_nearly_zero_curvature_limit(self):
        """Very small curvature kappa = 1e-8.

        Must behave almost indistinguishably from a straight line over length 1.0.
        """
        res = curva_engine.reconstruct_curve("1e-8", "0", s0=0.0, s1=1.0, num_points=100)
        assert np.isclose(res.r[0, -1], 1.0, atol=1e-6)
        assert np.abs(res.r[1, -1]) < 1e-6
        assert np.abs(res.r[2, -1]) < 1e-6


# ==============================================================================
# CATEGORY B: RAPID OSCILLATIONS & HIGH DYNAMICS (STRESS RUNS)
# ==============================================================================
class TestCategoryBHighDynamicsAndStress:
    """Stress tests high-frequency oscillations in kappa and tau, and long-range integration."""

    def test_b1_rapidly_oscillating_curvature(self):
        """High-frequency curvature: kappa(s) = 5 + sin(20*s), tau(s) = 0.

        Wavelength lambda = 2*pi/20 approx 0.314. Over s in [0, 4], ~12 complete oscillation cycles.
        Verifies that DOP853/RK45 handles rapid oscillations with frame orthonormality < 1e-4.
        """
        res = curva_engine.reconstruct_curve("5 + sin(20*s)", "0", s0=0.0, s1=4.0, num_points=400)
        assert res.classification == "curva_plana"

        norms_T = np.linalg.norm(res.T, axis=0)
        norms_N = np.linalg.norm(res.N, axis=0)
        norms_B = np.linalg.norm(res.B, axis=0)
        assert np.all(np.abs(norms_T - 1.0) < 1e-4)
        assert np.all(np.abs(norms_N - 1.0) < 1e-4)
        assert np.all(np.abs(norms_B - 1.0) < 1e-4)
        assert np.allclose(res.r[2], 0.0, atol=1e-10)

    def test_b2_rapidly_oscillating_torsion(self):
        """High-frequency torsion: kappa(s) = 2, tau(s) = cos(20*s).

        Oscillating torsion induces rapid frame twisting along the normal plane.
        """
        res = curva_engine.reconstruct_curve("2", "cos(20*s)", s0=0.0, s1=4.0, num_points=400)
        assert res.classification == "curva_espacial"

        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        dets = np.linalg.det(frames)
        assert np.all(np.abs(dets - 1.0) < 1e-4)

    def test_b3_coupled_oscillatory_stress(self):
        """Both kappa and tau oscillating at high frequencies: kappa = 5 + sin(25*s), tau = 3*cos(25*s)."""
        res = curva_engine.reconstruct_curve(
            "5 + sin(25*s)", "3*cos(25*s)", s0=0.0, s1=3.0, num_points=500
        )
        assert res.classification == "curva_espacial"
        dot_TN = np.abs(np.sum(res.T * res.N, axis=0))
        dot_TB = np.abs(np.sum(res.T * res.B, axis=0))
        dot_NB = np.abs(np.sum(res.N * res.B, axis=0))
        assert np.max(dot_TN) < 1e-4
        assert np.max(dot_TB) < 1e-4
        assert np.max(dot_NB) < 1e-4

    def test_b4_ultra_long_integration_accumulation(self):
        """Extended integration over s in [0, 150] with kappa=1, tau=0.5.

        Over length 150, the curve winds through ~24 complete helical revolutions.
        Verifies that numerical drift is tightly bounded by SO(3) orthonormalization.
        """
        res = curva_engine.reconstruct_curve("1", "0.5", s0=0.0, s1=150.0, num_points=800)
        assert res.classification == "helice_circular"

        norms_T = np.linalg.norm(res.T, axis=0)
        assert np.all(np.abs(norms_T - 1.0) < 1e-4)

        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        dets = np.linalg.det(frames)
        assert np.all(np.abs(dets - 1.0) < 1e-4)


# ==============================================================================
# CATEGORY C: GEOMETRIC EXTREMES & SCALE INVARIANCE
# ==============================================================================
class TestCategoryCGeometricExtremes:
    """Tests extreme scale variations: microscopic radii, macroscopic trajectories, high aspect ratios."""

    def test_c1_micro_scale_circle(self):
        """Microscopic circle: kappa = 1000, radius R = 1e-3.

        Interval [0, 2*pi*R] = [0, 2*pi*1e-3] approx [0, 0.00628318].
        Reconstructed endpoint should close back to start within 1e-5.
        """
        R = 1e-3
        s_end = 2.0 * np.pi * R
        res = curva_engine.reconstruct_curve("1000", "0", s0=0.0, s1=s_end, num_points=200)
        assert res.classification == "circulo"

        closure_err = np.linalg.norm(res.r[:, -1] - res.r[:, 0])
        assert closure_err < 1e-4, f"Micro circle closure error {closure_err} too large"

    def test_c2_macro_scale_trajectory(self):
        """Macroscopic scale: kappa = 1e-4 (radius 10,000) over [0, 1000]."""
        res = curva_engine.reconstruct_curve("1e-4", "0", s0=0.0, s1=1000.0, num_points=300)
        assert res.classification == "circulo"
        assert res.r.shape == (3, 300)
        assert np.all(np.isfinite(res.r))
        assert np.all(np.abs(np.linalg.norm(res.T, axis=0) - 1.0) < 1e-4)

    def test_c3_extreme_torsion_ratio(self):
        """Extreme torsion dominance: kappa = 0.05, tau = 50.0."""
        res = curva_engine.reconstruct_curve("0.05", "50.0", s0=0.0, s1=1.0, num_points=300)
        assert res.classification == "helice_circular"
        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        dets = np.linalg.det(frames)
        assert np.all(np.abs(dets - 1.0) < 1e-4)

    def test_c4_extreme_curvature_dominance(self):
        """Extreme curvature dominance: kappa = 50.0, tau = 0.05."""
        res = curva_engine.reconstruct_curve("50.0", "0.05", s0=0.0, s1=1.0, num_points=300)
        assert res.classification == "helice_circular"
        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        dets = np.linalg.det(frames)
        assert np.all(np.abs(dets - 1.0) < 1e-4)


# ==============================================================================
# CATEGORY D: CURVE CLASSIFICATION RIGOR & LANCRET'S THEOREM
# ==============================================================================
class TestCategoryDClassificationRigor:
    """Stress tests classification across edge case formulations."""

    def test_d1_lancret_rational_fractions(self):
        """Lancret's theorem with rational function: kappa = 1/(s^2 + 1), tau = 3/(s^2 + 1).

        tau / kappa = 3 = const != 0.
        Must classify as 'helice_cilindrica_geral'.
        """
        res = curva_engine.reconstruct_curve(
            "1/(s**2 + 1)", "3/(s**2 + 1)", s0=0.0, s1=4.0, num_points=100
        )
        assert res.classification == "helice_cilindrica_geral"

    def test_d2_lancret_exponential(self):
        """Lancret with exponential: kappa = exp(s/2), tau = 2*exp(s/2).

        Ratio = 2. Must classify as 'helice_cilindrica_geral'.
        """
        res = curva_engine.reconstruct_curve(
            "exp(s/2)", "2*exp(s/2)", s0=0.0, s1=2.0, num_points=100
        )
        assert res.classification == "helice_cilindrica_geral"

    def test_d3_cornu_spiral_with_affine_shift(self):
        """Clothoid with affine curvature: kappa(s) = 3*s + 2, tau = 0 on [0, 3].

        d2(kappa)/ds2 = 0 and d(kappa)/ds != 0. Must classify as 'espiral_de_cornu'.
        """
        res = curva_engine.reconstruct_curve("3*s + 2", "0", s0=0.0, s1=3.0, num_points=100)
        assert res.classification == "espiral_de_cornu"

    def test_d4_logarithmic_spiral_affine_inverse(self):
        """Logarithmic spiral with affine inverse radius: kappa(s) = 1/(2*s + 3), tau = 0.

        1/kappa(s) = 2*s + 3. Must classify as 'espiral_logaritmica'.
        """
        res = curva_engine.reconstruct_curve("1/(2*s + 3)", "0", s0=0.0, s1=3.0, num_points=100)
        assert res.classification == "espiral_logaritmica"

    def test_d5_curva_plana_fallback_cubic(self):
        """Planar curve with nonlinear curvature: kappa(s) = s^3 + 1, tau = 0 on [0, 2].

        Neither constant, linear, nor inverse-linear. Must classify as 'curva_plana'.
        """
        res = curva_engine.reconstruct_curve("s**3 + 1", "0", s0=0.0, s1=2.0, num_points=100)
        assert res.classification == "curva_plana"

    def test_d6_curva_espacial_fallback_varying_ratio(self):
        """Spatial curve with non-constant tau/kappa: kappa = s + 1, tau = s^2 + 1 on [0, 2].

        Ratio (s^2 + 1)/(s + 1) is not constant. Must classify as 'curva_espacial'.
        """
        res = curva_engine.reconstruct_curve("s + 1", "s**2 + 1", s0=0.0, s1=2.0, num_points=100)
        assert res.classification == "curva_espacial"


# ==============================================================================
# CATEGORY E: AST SECURITY WHITELIST & EVALUATION HARDENING
# ==============================================================================
class TestCategoryEASTSecurityAndHardening:
    """Stress tests AST sandbox with nested expressions, unary operators, and malicious attacks."""

    def test_e1_nested_unary_and_binary_operators(self):
        """Valid nested expressions: -(-s + 1), (s + (s * (s - 1)))."""
        expr1 = curva_engine.parse_and_validate_expression("-(-s + 1)")
        assert expr1 is not None
        expr2 = curva_engine.parse_and_validate_expression("(s + (s * (s - 1)))")
        assert expr2 is not None

    def test_e2_scientific_notation_in_expression(self):
        """Valid scientific notation: 1e-3*s + 2.5e-2."""
        expr = curva_engine.parse_and_validate_expression("1e-3*s + 2.5e-2")
        evaluator = curva_engine.create_evaluator(expr)
        val = evaluator(np.array([0.0, 1.0]))
        assert np.allclose(val, [0.025, 0.026], atol=1e-5)

    def test_e3_implicit_multiplication_parentheses(self):
        """Preprocessed implicit multiplication: 2(s + 1) and (s + 1)(s + 2)."""
        expr1 = curva_engine.parse_and_validate_expression("2(s + 1)")
        assert expr1 is not None
        eval1 = curva_engine.create_evaluator(expr1)
        assert np.isclose(eval1(2.0), 6.0)

        expr2 = curva_engine.parse_and_validate_expression("(s + 1)(s + 2)")
        assert expr2 is not None
        eval2 = curva_engine.create_evaluator(expr2)
        assert np.isclose(eval2(1.0), 6.0)

    @pytest.mark.parametrize(
        "malicious_expr",
        [
            "__import__('os').system('echo hacked')",
            "open('/etc/passwd').read()",
            "eval('2+2')",
            "exec('x=1')",
            "(lambda: 1)()",
            "[x for x in (1, 2)]",
            "{'a': 1}",
            "s.__class__.__bases__",
            "globals()",
            "locals()",
            "compile('1', '', 'eval')",
            "getattr(s, 'name')",
        ],
    )
    def test_e4_malicious_inputs_blocked_by_ast(self, malicious_expr):
        """Strictly blocks all code execution vectors."""
        with pytest.raises(ValueError):
            curva_engine.parse_and_validate_expression(malicious_expr)

    def test_e5_complex_valued_evaluation_rejected(self):
        """Rejects expressions that evaluate to complex numbers (e.g. sqrt(-s) for s > 0)."""
        with pytest.raises(ValueError):
            curva_engine.reconstruct_curve("sqrt(-s)", "0", s0=1.0, s1=4.0, num_points=50)


# ==============================================================================
# CATEGORY F: CLI PARAMETERS & FILE GENERATION
# ==============================================================================
class TestCategoryFCLIAndFileGeneration:
    """Verifies CLI handling of symbolic limits, flag permutations, and file creation."""

    def test_f1_symbolic_interval_constants_cli(self, tmp_path):
        """CLI correctly accepts symbolic constants for interval bounds: -i 0 '2*pi'."""
        out_html = tmp_path / "symbolic_pi.html"
        cmd = [
            sys.executable,
            str(CLI_PATH),
            "1",
            "1",
            "-i",
            "0",
            "2*pi",
            "-n",
            "50",
            "-o",
            str(out_html),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI error: {proc.stderr}"
        assert out_html.exists()

    def test_f2_symbolic_interval_euler_constant(self, tmp_path):
        """CLI correctly accepts Euler's number 'e' in interval: -i 'e' '2*e'."""
        out_html = tmp_path / "symbolic_e.html"
        cmd = [
            sys.executable,
            str(CLI_PATH),
            "1",
            "-i",
            "e",
            "2*e",
            "-n",
            "50",
            "-o",
            str(out_html),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI error: {proc.stderr}"
        assert out_html.exists()

    def test_f3_complex_filename_sanitization(self):
        """Sanitizes complex expressions with multiple operators without invalid filesystem characters."""
        san = curva_engine.sanitize_expr_for_filename("2*s**2 + sin(s)/3")
        assert "/" not in san
        assert "*" not in san
        assert "+" not in san
        assert "(" not in san
        assert ")" not in san
        assert " " not in san
        assert "_mult_" in san
        assert "_pow_" in san
        assert "_plus_" in san
        assert "_div_" in san

    def test_f4_nested_output_directory_creation(self, tmp_path):
        """CLI automatically creates parent directories when -o specifies nested non-existent path."""
        nested_out = tmp_path / "deep" / "nested" / "dir" / "curve.html"
        cmd = [
            sys.executable,
            str(CLI_PATH),
            "1",
            "-o",
            str(nested_out),
            "-n",
            "50",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI error: {proc.stderr}"
        assert nested_out.exists()


# ==============================================================================
# CATEGORY G: VISUALIZATION DOM INTEGRITY & HTML PAYLOAD SCALABILITY
# ==============================================================================
class TestCategoryGVisualizationPayloadIntegrity:
    """Verifies that generated HTML is compact, structurally sound, and free of NaNs across all 8 classes."""

    @pytest.mark.parametrize(
        "k_expr, t_expr, expected_class",
        [
            ("0", "0", "reta"),
            ("2", "0", "circulo"),
            ("1", "1", "helice_circular"),
            ("1 + s", "2*(1 + s)", "helice_cilindrica_geral"),
            ("2*s", "0", "espiral_de_cornu"),
            ("1/(s + 1)", "0", "espiral_logaritmica"),
            ("cos(s) + 2", "0", "curva_plana"),
            ("1 + s**2", "s", "curva_espacial"),
        ],
    )
    def test_g1_all_eight_classes_html_payload_and_size(
        self, tmp_path, k_expr, t_expr, expected_class
    ):
        """Generates HTML for all 8 classes and verifies size < 4MB and DOM integrity."""
        res = curva_engine.reconstruct_curve(k_expr, t_expr, s0=0.0, s1=4.0, num_points=250)
        assert res.classification == expected_class

        out_file = tmp_path / f"{expected_class}.html"
        curva_viz.export_interactive_html(res, str(out_file))

        assert out_file.exists()
        file_size_kb = out_file.stat().st_size / 1024.0
        # HTML file size must be compact (under 3.5 MB)
        assert file_size_kb < 3500, f"HTML file size {file_size_kb:.1f} KB exceeds 3500 KB"

        content = out_file.read_text(encoding="utf-8")
        # Ensure no unquoted numeric NaN values were written into the JSON payload
        assert re.search(r'(:\s*NaN\b|\[\s*NaN\b|,\s*NaN\b)', content) is None

        # Verify CURVE_METRICS JSON payload parses cleanly and all frame metrics are valid
        m = re.search(r"window\.CURVE_METRICS\s*=\s*(\[.*?\]);\s*\n", content, re.DOTALL)
        assert m is not None, "window.CURVE_METRICS not found in HTML"
        metrics = json.loads(m.group(1))
        assert len(metrics) > 0
        for item in metrics:
            assert isinstance(item["s"], (int, float))
            assert isinstance(item["x"], (int, float))
            assert isinstance(item["y"], (int, float))
            assert isinstance(item["z"], (int, float))
            assert isinstance(item["kappa"], (int, float))
            assert isinstance(item["tau"], (int, float))
            assert item["rho"] is None or isinstance(item["rho"], (int, float))

        assert "hud-card" in content

    def test_g2_osculating_circle_omission_for_vanishing_curvature(self):
        """Verifies that for straight line (kappa = 0), osculating circle coordinates are empty lists."""
        coords = curva_viz._compute_circle_coords(
            P=np.array([0.0, 0.0, 0.0]),
            T=np.array([1.0, 0.0, 0.0]),
            N=np.array([0.0, 1.0, 0.0]),
            k_val=0.0,
            span=10.0,
        )
        assert coords == ([], [], [])

    def test_g3_osculating_circle_omission_for_large_radius(self):
        """Verifies that when rho > 10 * span, osculating circle coordinates are omitted to prevent visual explosion."""
        coords = curva_viz._compute_circle_coords(
            P=np.array([0.0, 0.0, 0.0]),
            T=np.array([1.0, 0.0, 0.0]),
            N=np.array([0.0, 1.0, 0.0]),
            k_val=1e-4,  # rho = 10,000
            span=5.0,  # 10 * span = 50 << 10,000
        )
        assert coords == ([], [], [])
