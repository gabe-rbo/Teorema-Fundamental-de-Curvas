"""The standalone app/triedro.html must be rebuilt whenever app/ or design-system/ change."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"


def _load_builder():
    spec = importlib.util.spec_from_file_location("app_build", APP / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_built_file_is_up_to_date():
    expected = _load_builder().build()
    assert (APP / "triedro.html").read_text(encoding="utf-8") == expected, (
        "app/triedro.html is stale: run `python3 app/build.py`"
    )


def test_built_file_has_no_local_dependencies():
    html = (APP / "triedro.html").read_text(encoding="utf-8")
    assert not re.search(r'<link rel="stylesheet" href="(?!https?:)', html)
    assert not re.search(r'<script src="(?!https?:)', html)
    assert "--curve:" in html and ".tf-dock" in html and "function reconstruct" in html
