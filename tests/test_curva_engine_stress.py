"""Empirical Stress, Property-Based, and Adversarial Challenge Suite for curva_engine.py.

Designed and executed by Challenger Agent (teamwork_preview_challenger_m1_1).
Empirically verifies:
  1. Long-range integration stability (s in [0, 100], [0, 500]) and SO(3) drift bounds.
  2. High discretization performance and shape invariants (N=2000, 5000, 10000).
  3. Adversarial expression syntax (nested calls, implicit multiplication, powers, scientific notation).
  4. Boundary conditions (zero curvature, small intervals, negative intervals, inverted intervals, N limits).
  5. Security and AST injection blocking.
  6. Robustness against stiff, high-frequency, and non-differentiable invariant functions.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import curva_engine as ce


class TestLongRangeAndSO3Drift:
    """Stress tests verifying SO(3) Modified Gram-Schmidt prevents numerical drift over long horizons."""

    def test_long_range_helix_drift_bounds(self):
        """Verify s in [0, 100] for circular helix (kappa=1, tau=1).

        Checks that:
          - ||T||, ||N||, ||B|| deviate from 1.0 by less than 1e-14
          - Determinant det([T, N, B]) deviates from 1.0 by less than 1e-14
          - Helix radius deviates from 0.5 by less than 1e-6
          - Trajectory error against analytical Frenet solution is < 1e-6
        """
        s0, s1 = 0.0, 100.0
        num_points = 5000
        res = ce.reconstruct_curve("1", "1", s0=s0, s1=s1, num_points=num_points)

        assert res.classification == "helice_circular"

        # Frame unit norm error to machine precision (< 1e-14)
        norm_T_err = np.max(np.abs(np.linalg.norm(res.T, axis=0) - 1.0))
        norm_N_err = np.max(np.abs(np.linalg.norm(res.N, axis=0) - 1.0))
        norm_B_err = np.max(np.abs(np.linalg.norm(res.B, axis=0) - 1.0))
        assert norm_T_err < 1e-14, f"T norm error {norm_T_err} exceeded 1e-14"
        assert norm_N_err < 1e-14, f"N norm error {norm_N_err} exceeded 1e-14"
        assert norm_B_err < 1e-14, f"B norm error {norm_B_err} exceeded 1e-14"

        # Mutual orthogonality (< 1e-14)
        dot_TN = np.max(np.abs(np.sum(res.T * res.N, axis=0)))
        dot_TB = np.max(np.abs(np.sum(res.T * res.B, axis=0)))
        dot_NB = np.max(np.abs(np.sum(res.N * res.B, axis=0)))
        assert dot_TN < 1e-14, f"T.N max {dot_TN} exceeded 1e-14"
        assert dot_TB < 1e-14, f"T.B max {dot_TB} exceeded 1e-14"
        assert dot_NB < 1e-14, f"N.B max {dot_NB} exceeded 1e-14"

        # SO(3) determinant (< 1e-14)
        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        det_err = np.max(np.abs(np.linalg.det(frames) - 1.0))
        assert det_err < 1e-14, f"Determinant error {det_err} exceeded 1e-14"

        # Trajectory accuracy against closed-form Frenet solution
        sq2 = np.sqrt(2.0)
        x_ana = res.s / 2.0 + (sq2 / 4.0) * np.sin(sq2 * res.s)
        y_ana = 0.5 * (1.0 - np.cos(sq2 * res.s))
        z_ana = res.s / 2.0 - (sq2 / 4.0) * np.sin(sq2 * res.s)
        r_ana = np.stack([x_ana, y_ana, z_ana], axis=0)

        traj_err = np.max(np.linalg.norm(res.r - r_ana, axis=0))
        assert traj_err < 1e-6, f"Trajectory error {traj_err} exceeded 1e-6"

        # Helix cylinder radius stability
        u_axis = np.array([1.0 / sq2, 0.0, 1.0 / sq2])
        p0 = np.array([0.0, 0.5, 0.0])
        diff = res.r - p0[:, None]
        proj = np.sum(diff * u_axis[:, None], axis=0, keepdims=True) * u_axis[:, None]
        perp = diff - proj
        radii = np.linalg.norm(perp, axis=0)
        radius_err = np.max(np.abs(radii - 0.5))
        assert radius_err < 1e-6, f"Radius error {radius_err} exceeded 1e-6"

    def test_extreme_long_range_500(self):
        """Verify s in [0, 500] with N=10000 retains SO(3) orthonormality and low error."""
        res = ce.reconstruct_curve("1", "1", s0=0.0, s1=500.0, num_points=10000)
        norm_T_err = np.max(np.abs(np.linalg.norm(res.T, axis=0) - 1.0))
        assert norm_T_err < 1e-14

        frames = np.transpose(np.array([res.T, res.N, res.B]), (2, 0, 1))
        det_err = np.max(np.abs(np.linalg.det(frames) - 1.0))
        assert det_err < 1e-14

    def test_circle_100_full_orbits(self):
        """Verify circle with kappa=2, tau=0 over 100 orbits (s in [0, 100*pi])."""
        res = ce.reconstruct_curve("2", "0", s0=0.0, s1=100.0 * np.pi, num_points=10000)
        assert res.classification == "circulo"

        # In-plane z must be strictly 0
        assert np.max(np.abs(res.r[2])) < 1e-14

        # Center at (0, 0.5, 0), radius 0.5
        center = np.array([[0.0], [0.5], [0.0]])
        radii = np.linalg.norm(res.r - center, axis=0)
        assert np.max(np.abs(radii - 0.5)) < 1e-6


class TestHighDiscretizationScaling:
    """Stress tests verifying high point counts (N=2000, 5000, 10000, 20000)."""

    @pytest.mark.parametrize("n_points", [2000, 5000, 10000])
    def test_discretization_point_counts(self, n_points):
        res = ce.reconstruct_curve("1 + 0.1*s", "0.5", s0=0.0, s1=10.0, num_points=n_points)
        assert res.s.shape == (n_points,)
        assert res.r.shape == (3, n_points)
        assert res.T.shape == (3, n_points)
        assert res.N.shape == (3, n_points)
        assert res.B.shape == (3, n_points)
        assert np.max(np.abs(np.linalg.norm(res.T, axis=0) - 1.0)) < 1e-14


class TestAdversarialMathematicalExpressions:
    """Stress tests on complex, nested, and boundary math expressions."""

    @pytest.mark.parametrize(
        "k_str, t_str, exp_class",
        [
            ("s^2", "0", "curva_plana"),
            ("s**2", "0", "curva_plana"),
            ("(s + 1)^3", "0", "curva_plana"),
            ("2s", "0", "espiral_de_cornu"),
            ("3(s + 1)", "0", "espiral_de_cornu"),
            ("(s + 1)(s + 2)", "0", "curva_plana"),
            ("2pi", "0", "circulo"),
            ("4sin(s) + 5", "0", "curva_plana"),
            ("sin(s)cos(s) + 1", "0", "curva_plana"),
            ("1e-3", "0", "circulo"),
            ("2.5e-2*s", "0", "espiral_de_cornu"),
            ("pi", "0", "circulo"),
            ("e", "0", "circulo"),
            ("E", "0", "circulo"),
            ("sqrt(sin(s)**2 + 1)", "0", "curva_plana"),
            ("exp(-s/10)", "0", "curva_plana"),
            ("log(s + 2)", "0", "curva_plana"),
            ("atan(s) + 1", "0", "curva_plana"),
            ("1/2", "0", "circulo"),
            ("3/(s + 1)", "0", "espiral_logaritmica"),
            ("1/(s^2 + 1)", "0", "curva_plana"),
            ("sin(s)**2 + cos(s)**2", "0", "circulo"),
            ("sqrt(4)", "0", "circulo"),
            ("s - s", "0", "reta"),
            ("0*s", "0", "reta"),
            ("1 + 0*s", "0", "circulo"),
            ("1 + s", "2 + 2*s", "helice_cilindrica_geral"),
            ("s^2 + 1", "3*(s^2 + 1)", "helice_cilindrica_geral"),
            ("  2*s  ", " 0 ", "espiral_de_cornu"),
        ],
    )
    def test_adversarial_expressions(self, k_str, t_str, exp_class):
        res = ce.reconstruct_curve(k_str, t_str, s0=0.0, s1=2.0, num_points=50)
        assert res.classification == exp_class
        assert np.max(np.abs(np.linalg.norm(res.T, axis=0) - 1.0)) < 1e-14


class TestBoundaryConditionsAndRobustness:
    """Stress tests on geometric and numerical boundary conditions."""

    def test_isolated_zero_curvature_origin(self):
        """kappa(s) = s^2 starts at 0 at s=0."""
        res = ce.reconstruct_curve("s^2", "0", s0=0.0, s1=2.0, num_points=100)
        assert res.classification == "curva_plana"
        assert np.max(np.abs(np.linalg.norm(res.T, axis=0) - 1.0)) < 1e-14

    def test_isolated_zero_curvature_interior(self):
        """kappa(s) = 1 - cos(s) has zeros at s=0, 2*pi."""
        res = ce.reconstruct_curve("1 - cos(s)", "0", s0=0.0, s1=2 * np.pi, num_points=100)
        assert res.classification == "curva_plana"
        assert np.max(np.abs(np.linalg.norm(res.T, axis=0) - 1.0)) < 1e-14

    def test_zero_curvature_with_nonzero_torsion(self):
        """kappa = 0 identically with tau = 1 must yield a straight line."""
        res = ce.reconstruct_curve("0", "1", s0=0.0, s1=5.0, num_points=50)
        assert res.classification == "reta"
        assert np.allclose(res.r[0], res.s, atol=1e-10)
        assert np.allclose(res.r[1], 0.0, atol=1e-10)
        assert np.allclose(res.r[2], 0.0, atol=1e-10)

    def test_large_curvature_scale(self):
        """kappa = 1000 (radius = 0.001) circle closure and radius precision."""
        res = ce.reconstruct_curve("1000", "0", s0=0.0, s1=2 * np.pi / 1000, num_points=200)
        center = np.array([[0.0], [0.001], [0.0]])
        radius_err = np.max(np.abs(np.linalg.norm(res.r - center, axis=0) - 0.001))
        assert radius_err < 1e-9

    def test_tiny_curvature_scale(self):
        """kappa = 1e-4 (radius = 10000) integrates cleanly."""
        res = ce.reconstruct_curve("1e-4", "0", s0=0.0, s1=10.0, num_points=100)
        assert res.classification == "circulo"
        assert np.isclose(res.r[0, -1], 10.0, atol=1e-3)

    def test_high_frequency_oscillation(self):
        """Rapidly oscillating invariants: kappa = 2 + sin(20*s), tau = cos(20*s)."""
        res = ce.reconstruct_curve("2 + sin(20*s)", "cos(20*s)", s0=0.0, s1=10.0, num_points=1000)
        assert res.classification == "curva_espacial"
        assert np.max(np.abs(np.linalg.norm(res.T, axis=0) - 1.0)) < 1e-14

    def test_non_differentiable_curvature(self):
        """C0 curvature abs(s - 1) integrates smoothly."""
        res = ce.reconstruct_curve("abs(s - 1)", "0", s0=0.0, s1=2.0, num_points=100)
        assert res.classification == "curva_plana"
        assert np.max(np.abs(np.linalg.norm(res.T, axis=0) - 1.0)) < 1e-14

    def test_very_small_interval(self):
        """Interval of width 1e-6 integrates without floating point overflow."""
        res = ce.reconstruct_curve("1", "1", s0=0.0, s1=1e-6, num_points=10)
        assert np.isclose(res.r[0, -1], 1e-6, atol=1e-12)

    def test_negative_interval(self):
        """Interval entirely in negative reals [-10, -5]."""
        res = ce.reconstruct_curve("1", "1", s0=-10.0, s1=-5.0, num_points=50)
        assert np.isclose(res.s[0], -10.0)
        assert np.isclose(res.s[-1], -5.0)

    def test_invalid_interval_equal_or_inverted(self):
        with pytest.raises(ValueError):
            ce.reconstruct_curve("1", "1", s0=2.0, s1=2.0)
        with pytest.raises(ValueError):
            ce.reconstruct_curve("1", "1", s0=5.0, s1=2.0)

    def test_invalid_point_counts(self):
        with pytest.raises(ValueError):
            ce.reconstruct_curve("1", "0", s0=0.0, s1=1.0, num_points=1)
        with pytest.raises(ValueError):
            ce.reconstruct_curve("1", "0", s0=0.0, s1=1.0, num_points=0)
        with pytest.raises(ValueError):
            ce.reconstruct_curve("1", "0", s0=0.0, s1=1.0, num_points=-5)

    def test_negative_curvature_rejected(self):
        with pytest.raises(ValueError):
            ce.reconstruct_curve("-1", "0", s0=0.0, s1=1.0)
        with pytest.raises(ValueError):
            ce.reconstruct_curve("sin(s)", "0", s0=0.0, s1=2 * np.pi)

    def test_singularities_rejected(self):
        with pytest.raises(ValueError):
            ce.reconstruct_curve("1/s", "0", s0=0.0, s1=2.0)
        with pytest.raises(ValueError):
            ce.reconstruct_curve("log(s)", "0", s0=0.0, s1=2.0)

    def test_ast_security_injection_blocked(self):
        for malicious in [
            "__import__('os').system('ls')",
            "eval('1+1')",
            "exec('x=1')",
            "open('/etc/passwd')",
            "(1).__class__.__mro__",
            "x + y",
            "",
            "   ",
        ]:
            with pytest.raises(ValueError):
                ce.parse_and_validate_expression(malicious)
