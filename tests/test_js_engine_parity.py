"""Parity gate: the JavaScript engine in app/js must match the Python reference engine.

The interactive app reconstructs curves in the browser (Magnus integrator + Taylor-jet
derivatives). This test feeds the same kappa(s), tau(s) to both engines and compares the
trajectory, the Frenet frame and the evolute/involute invariants.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

import curva_engine as ce
import curva_viz as cv

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")

# kappa, tau, s0, s1, points
CASES = [
    ("1", "0", 0.0, 6.28, 400),
    ("s", "0", 0.0, 5.0, 500),
    ("1/(s+1)", "0", 0.0, 10.0, 500),
    ("2+2*cos(5*s)", "0", 0.0, 12.5, 800),
    ("1", "1", 0.0, 12.56, 600),
    ("1+0.5*sin(s)", "0.5+cos(2*s)", 0.0, 25.0, 1500),
    ("2+sin(3*s)", "1+0.5*cos(5*s)", 0.0, 14.0, 1200),
    ("sqrt(1+s)", "2*sqrt(1+s)", 0.0, 14.0, 800),
    ("1.5", "3*tanh(s-8)", 0.0, 16.0, 800),
    ("abs(sin(s))+0.4", "2*abs(cos(s))", 0.0, 18.0, 2000),
]


def _reference(k: str, t: str, s0: float, s1: float, n: int) -> dict:
    res = ce.reconstruct_curve(k, t, s0=s0, s1=s1, num_points=n)
    planar = bool(np.all(np.abs(res.tau) < 1e-12))
    inv = cv._associated_curve_invariants(res, planar)
    return {
        "k": k, "t": t, "s0": s0, "s1": s1, "n": n,
        "R": res.r.tolist(), "T": res.T.tolist(), "N": res.N.tolist(), "B": res.B.tolist(),
        "inv": {key: [None if not np.isfinite(v) else float(v) for v in inv[key]] for key in inv},
        "inv_idx": [n // 7, n // 3, n // 2, (2 * n) // 3],
    }


@pytest.fixture(scope="module")
def js_errors() -> list[dict]:
    payload = json.dumps({"cases": [_reference(*c) for c in CASES]})
    proc = subprocess.run(
        ["node", str(ROOT / "tests" / "js" / "parity.js")],
        input=payload, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["errors"]


def test_trajectory_and_frame_match_python(js_errors):
    for e in js_errors:
        for key in ("R", "T", "N", "B"):
            assert e[key] < 1e-5, f"kappa={e['k']} tau={e['t']}: {key} error {e[key]:.2e}"


def test_evolute_involute_invariants_match_python(js_errors):
    for e in js_errors:
        for key, err in e["inv"].items():
            assert err < 1e-6, f"kappa={e['k']} tau={e['t']}: {key} relative error {err:.2e}"


def test_planar_detection_and_classification(js_errors):
    by = {(e["k"], e["t"]): e for e in js_errors}
    assert by[("1", "0")]["planar"] and by[("1", "0")]["label"] == "Círculo"
    assert by[("s", "0")]["label"].startswith("Clotoide")
    assert by[("1/(s+1)", "0")]["label"] == "Espiral logarítmica"
    assert by[("1", "1")]["label"] == "Hélice circular"
    assert by[("sqrt(1+s)", "2*sqrt(1+s)")]["label"].startswith("Hélice cilíndrica")
    assert not by[("1", "1")]["planar"]
