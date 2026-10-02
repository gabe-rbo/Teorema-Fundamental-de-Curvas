"""Runs the Node unit tests for the browser engine (tests/js/engine.test.js)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_browser_engine_unit_tests():
    proc = subprocess.run(
        ["node", "--test", str(ROOT / "tests" / "js")],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
