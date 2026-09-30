"""Empirical Adversarial and Stress Test Suite for Milestone M4.

Validates the integrated CLI (teorema-fundamental-curvas.py) and underlying engines
against adversarial inputs, boundary conditions, singular geometries, and injection attempts.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import curva_engine
import curva_viz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = PROJECT_ROOT / "teorema-fundamental-curvas.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Helper to execute the CLI script in a subprocess."""
    cmd = [sys.executable, str(CLI_PATH), *args]
    return subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )


# ==============================================================================
# 1. EXTREME INTERVALS AND RESOLUTIONS
# ==============================================================================
class TestExtremeIntervalsAndResolutions:
    """Stress tests on parameter discretization and interval boundaries."""

    def test_extremely_small_interval(self, tmp_path):
        """Very small interval [0, 0.001] with minimal points."""
        out = tmp_path / "small.html"
        proc = run_cli("0", "0", "-i", "0", "0.001", "-n", "10", "-o", str(out))
        assert proc.returncode == 0, proc.stderr
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_high_point_count(self, tmp_path):
        """Discretization with 2000 points."""
        out = tmp_path / "high_n.html"
        proc = run_cli("1", "1", "-i", "0", "6.28", "-n", "2000", "-o", str(out))
        assert proc.returncode == 0, proc.stderr
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_negative_interval_range(self, tmp_path):
        """Integration over negative arc length interval [-10, -2]."""
        out = tmp_path / "neg_interval.html"
        proc = run_cli("1", "0", "-i", "-10", "-2", "-n", "100", "-o", str(out))
        assert proc.returncode == 0, proc.stderr
        assert out.exists()


# ==============================================================================
# 2. SINGULAR AND SPECIAL GEOMETRIES
# ==============================================================================
class TestSpecialGeometries:
    """Validates classification and integration for singular and textbook curves."""

    def test_straight_line_zero_curvature_zero_torsion(self, tmp_path):
        """kappa = 0, tau = 0 yields straight line."""
        out = tmp_path / "line.html"
        proc = run_cli("0", "0", "-i", "0", "5", "-o", str(out))
        assert proc.returncode == 0, proc.stderr
        assert "Classificação da Curva : reta" in proc.stdout

    def test_straight_line_zero_curvature_nonzero_torsion(self, tmp_path):
        """kappa = 0, tau = 1: trajectory must be straight line, classified as reta."""
        out = tmp_path / "line_tau.html"
        proc = run_cli("0", "1", "-i", "0", "5", "-o", str(out))
        assert proc.returncode == 0, proc.stderr
        assert "Classificação da Curva : reta" in proc.stdout

        res = curva_engine.reconstruct_curve("0", "1", 0.0, 5.0, 50)
        assert res.classification == "reta"
        assert np.allclose(res.r[1:, :], 0.0, atol=1e-7)
        assert np.allclose(res.r[0, :], res.s, atol=1e-7)

    def test_lancret_generalized_cylindrical_helix(self, tmp_path):
        """tau / kappa = const != 0: Lancret's theorem."""
        out = tmp_path / "lancret.html"
        proc = run_cli(
            "2 + cos(s)", "4 + 2*cos(s)", "-i", "0", "6.28", "-o", str(out)
        )
        assert proc.returncode == 0, proc.stderr
        assert "Classificação da Curva : helice_cilindrica_geral" in proc.stdout

    def test_clothoid_cornu_spiral(self, tmp_path):
        """kappa(s) = s, tau(s) = 0: Cornu spiral / Clothoid."""
        out = tmp_path / "clothoid.html"
        proc = run_cli("s", "0", "-i", "0", "5", "-o", str(out))
        assert proc.returncode == 0, proc.stderr
        assert "Classificação da Curva : espiral_de_cornu" in proc.stdout


# ==============================================================================
# 3. DOMAIN AND MATHEMATICAL FAILURES (EXIT CODE 1)
# ==============================================================================
class TestDomainAndMathFailures:
    """Verifies graceful handling with exit code 1 for domain/math errors."""

    def test_negative_constant_curvature_rejected(self):
        """Negative constant curvature must exit with 1."""
        proc = run_cli("-1", "0")
        assert proc.returncode == 1
        assert "Erro na reconstrução da curva" in proc.stderr
        assert "Curvature kappa(s) must be non-negative" in proc.stderr

    def test_variable_curvature_crossing_negative_rejected(self):
        """Variable curvature crossing zero to negative must exit with 1."""
        proc = run_cli("s - 2", "0", "-i", "0", "4")
        assert proc.returncode == 1
        assert "Curvature kappa(s) must be non-negative" in proc.stderr

    def test_singularity_division_by_zero_rejected(self):
        """Singularity at origin 1/s on [0, 5] must exit with 1."""
        proc = run_cli("1/s", "0", "-i", "0", "5")
        assert proc.returncode == 1
        assert "Expression evaluates to non-finite values" in proc.stderr

    def test_interior_pole_singularity_rejected(self):
        """Interior pole 1/(s - 2)^2 on [0, 4] must reject cleanly with exit code 1."""
        proc = run_cli("1/(s - 2)^2", "0", "-i", "0", "4", "-n", "500")
        assert proc.returncode == 1
        assert "Expression evaluates to non-finite values" in proc.stderr

    def test_inverted_interval_rejected(self):
        """s0 >= s1 must exit with 1."""
        proc = run_cli("1", "0", "-i", "5", "2")
        assert proc.returncode == 1
        assert "Erro de validação: início do intervalo s0" in proc.stderr

    def test_points_less_than_two_rejected(self):
        """num_pontos < 2 must exit with 1."""
        proc = run_cli("1", "0", "-n", "1")
        assert proc.returncode == 1
        assert "Erro de validação: o número de pontos" in proc.stderr


# ==============================================================================
# 4. ARGPARSE SYNTAX AND CLI ERRORS (EXIT CODE 2)
# ==============================================================================
class TestArgparseErrors:
    """Verifies standard argparse exit code 2 on invalid CLI syntax."""

    def test_missing_required_curvature(self):
        """Missing curvature argument must exit with 2."""
        proc = run_cli()
        assert proc.returncode == 2
        assert "usage:" in proc.stderr
        assert "curvatura κ(s) é obrigatório" in proc.stderr

    def test_unrecognized_positional_arguments(self):
        """Extra unrecognized positional argument must exit with 2."""
        proc = run_cli("1", "0", "extra_pos")
        assert proc.returncode == 2
        assert "unrecognized arguments" in proc.stderr

    def test_unrecognized_flag(self):
        """Unknown option flag must exit with 2."""
        proc = run_cli("1", "0", "--nonexistent-flag")
        assert proc.returncode == 2
        assert "unrecognized arguments" in proc.stderr

    def test_incomplete_interval_argument(self):
        """Providing only 1 float to -i must exit with 2."""
        proc = run_cli("1", "0", "-i", "0")
        assert proc.returncode == 2
        assert "expected 2 arguments" in proc.stderr

    def test_non_numeric_points(self):
        """Providing string to -n must exit with 2."""
        proc = run_cli("1", "0", "-n", "not_a_number")
        assert proc.returncode == 2
        assert "invalid int value" in proc.stderr


# ==============================================================================
# 5. CODE INJECTION & AST SECURITY IN EXPRESSIONS
# ==============================================================================
class TestExpressionSecurity:
    """Verifies AST whitelist prevents arbitrary execution in kappa(s) and tau(s)."""

    @pytest.mark.parametrize(
        "payload",
        [
            "__import__('os').system('echo hacked')",
            "open('/etc/passwd')",
            "eval('1+1')",
            "exec('x=1')",
            "lambda s: s",
            "s.__class__",
            "getattr(sp, 'sin')",
            "[x for x in [1, 2]]",
        ],
    )
    def test_malicious_expressions_blocked_cleanly(self, payload: str):
        """Malicious payloads in curvature expression must exit with code 1."""
        proc = run_cli(payload, "0")
        assert proc.returncode == 1
        assert "Erro na reconstrução da curva" in proc.stderr

    def test_interval_bound_security_injection(self, tmp_path):
        """Verifies that malicious payloads in -i cannot execute arbitrary code."""
        marker = tmp_path / "injected.txt"
        payload = f"__import__('pathlib').Path('{marker}').touch()"
        run_cli("1", "0", "-i", "0", payload)
        assert not marker.exists(), "CRITICAL: Arbitrary code execution occurred via -i argument parsing!"

    def test_interval_bound_variable_s_rejected(self):
        """Interval bound containing variable 's' must be rejected with exit code 2."""
        proc = run_cli("1", "0", "-i", "0", "s + 1")
        assert proc.returncode == 2
        assert "Valor de intervalo inválido" in proc.stderr

    def test_interval_bound_non_finite_rejected(self):
        """Interval bound evaluated to inf/nan must be rejected with exit code 2."""
        proc = run_cli("1", "0", "-i", "0", "inf")
        assert proc.returncode == 2
        assert "Valor de intervalo inválido" in proc.stderr
