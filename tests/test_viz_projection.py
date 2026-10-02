"""The Python-generated viewer offers an axonometric (orthographic) projection toggle in 3D."""

from __future__ import annotations

import curva_engine as ce
import curva_viz as cv


def _html(tmp_path, kappa: str, tau: str) -> str:
    res = ce.reconstruct_curve(kappa, tau, s0=0.0, s1=10.0, num_points=120)
    out = tmp_path / "v.html"
    cv.export_interactive_html(res, str(out))
    return out.read_text(encoding="utf-8")


def test_spatial_viewer_has_projection_toggle(tmp_path):
    html = _html(tmp_path, "1", "1")
    assert 'id="btn-dock-proj"' in html
    assert "function toggleProjection()" in html
    assert "scene.camera.projection.type" in html
    # the chosen projection must survive the per-frame view sync
    assert 'isOrtho ? "orthographic" : "perspective"' in html


def test_planar_viewer_has_no_projection_toggle(tmp_path):
    assert 'id="btn-dock-proj"' not in _html(tmp_path, "1", "0")
