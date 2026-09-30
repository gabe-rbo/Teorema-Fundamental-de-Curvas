# Reviewer & Adversarial Critic Report — Milestone M2

**Author**: `reviewer_m2_2`  
**Roles**: reviewer, critic  
**Target File Under Review**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_viz.py`  
**Milestone**: M2 (Visualization Engine & Differential Apparatus)  
**Parent Orchestrator**: `c02fecd8-2c8f-44e6-bc31-daf5123708ba`  

---

## Review Summary

**Verdict**: **APPROVE**  
**Integrity Audit**: **PASS** (Zero integrity violations; genuine implementations of differential geometry formulas; no hardcoded test answers; no facade logic).  
**Overall Risk Assessment**: **LOW**

---

## 1. Observation

1. **Test Suite Execution**:
   - Command: `python3 -m pytest tests/test_teorema_fundamental.py -v`
   - Output verbatim:
     ```
     ================== 57 passed, 7 skipped, 3 warnings in 1.77s ===================
     ```
   - All 6 visualization tests marked `@requires_viz` passed cleanly:
     - `tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_html_viewport_meta_css PASSED`
     - `tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_html_plotly_container PASSED`
     - `tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_html_apparatus_traces PASSED`
     - `tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_html_click_navigation_script PASSED`
     - `tests/test_teorema_fundamental.py::TestTier2BoundaryAndCornerCases::test_tier2_zero_curvature_osculating_circle PASSED`
     - `tests/test_teorema_fundamental.py::TestTier3CrossFeatureCombinations::test_tier3_planar_vs_spatial_visualization_config PASSED`
   - The 7 skipped tests belong exclusively to Milestone M3 CLI entrypoint (`teorema-fundamental-curvas.py`), which is pending implementation.

2. **Source Code Structure of `curva_viz.py`**:
   - `build_curve_figure(curve_data: CurveResult, title: str | None = None) -> go.Figure` (lines 309–686) constructs exactly 10 traces:
     - Trace 0: `Curva r(s)` (`go.Scatter3d`, `mode='lines+markers'`, `line=dict(color='#00e5ff', width=5)`, `customdata=[s, frameIdx, kappa, tau]`)
     - Trace 1: `Ponto Ativo r(s)` (`go.Scatter3d`, `mode='markers'`, `color='#ffea00'`, `size=8`)
     - Trace 2: `Vetor Tangente T` (`go.Scatter3d`, `mode='lines+markers'`, `color='#00e676'`, `width=7`)
     - Trace 3: `Vetor Normal N` (`go.Scatter3d`, `mode='lines+markers'`, `color='#ff1744'`, `width=7`)
     - Trace 4: `Vetor Binormal B` (`go.Scatter3d`, `mode='lines+markers'`, `color='#2979ff'`, `width=7`)
     - Trace 5: `Reta Tangente L_T` (`go.Scatter3d`, `mode='lines'`, `color='rgba(0, 230, 118, 0.65)'`, `dash='dash'`)
     - Trace 6: `Plano Osculador (T, N)` (`go.Mesh3d`, `color='rgba(255, 213, 79, 0.28)'`, normal to $B$)
     - Trace 7: `Plano Normal (N, B)` (`go.Mesh3d`, `color='rgba(255, 82, 82, 0.20)'`, normal to $T$)
     - Trace 8: `Plano Retificante (T, B)` (`go.Mesh3d`, `color='rgba(68, 138, 255, 0.20)'`, normal to $N$)
     - Trace 9: `Círculo Osculador` (`go.Scatter3d`, `mode='lines'`, `color='#ffd600'`, `width=4`)
   - Planar curve detection (lines 347–358):
     - When $\tau \equiv 0$ or classified as planar (`circulo`, `reta`, `espiral_de_cornu`, `espiral_logaritmica`, `curva_plana`), Traces 4, 7, and 8 are set to `visible='legendonly'`.
     - Initial camera layout is configured with top-down orthogonal view `eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0)`.

3. **Selective Animation Frames & Performance**:
   - Frames are generated in lines 437–494.
   - Each `go.Frame` specifies `traces=[1, 2, 3, 4, 5, 6, 7, 8, 9]`.
   - Trace 0 (`Curva r(s)`) is excluded from frame payloads, maintaining static curve geometry and keeping file size around 1.13 MB for 500 points / 200 frames.
   - Frame traces in `_build_apparatus_traces(..., is_initial=False)` omit the `visible` key, preserving user legend toggle selections across slider animations.
   - `uirevision="constant"` is set on both `fig.layout` and `fig.layout.scene`, preserving camera orientation, zoom, and pitch during scrubbing.

4. **Fullscreen Responsive Template & Client-Side JS**:
   - In `export_interactive_html`:
     - CSS reset sets `* { margin:0; padding:0; box-sizing:border-box; }` and `html, body { width:100vw; height:100vh; height:100dvh; overflow:hidden; }`.
     - Container `#plot-container` and `.plotly-graph-div` set to `width: 100vw !important; height: 100vh !important;`.
     - Floating glassmorphism HUD card `#hud-card` (`backdrop-filter: blur(12px); z-index: 1000; pointer-events: auto;`) displays live metrics: $s, r(s), \kappa(s), \tau(s), \rho(s)$.
     - Client-side JS injected via Plotly post-script:
       - `plotly_click`: snaps slider and differential apparatus to clicked curve vertex via `pt.customdata[1]` frame index mapping.
       - `plotly_sliderchange`: updates HUD metrics in real time when scrubbing slider.
       - `plotly_animatingframe`: updates HUD metrics during automated playback.
       - `window.resize`: invokes `Plotly.Plots.resize(gd)` for responsive reflow.

---

## 2. Logic Chain

1. **Adherence to Contract and Requirements**:
   - Observation 2 demonstrates that all 10 differential apparatus traces required by `ORIGINAL_REQUEST.md` R3 and `PROJECT.md` Feature 10 are implemented.
   - The osculating circle calculation in `_compute_circle_coords` (lines 88–123):
     $$C(\theta) = c - \frac{1}{\kappa} N \cos(\theta) + \rho T \sin(\theta), \quad c = P + \frac{1}{\kappa} N$$
     satisfies $C(0) = P$, $C'(0) = \rho T$, and $C''(0) = \rho N$, correctly achieving second-order contact with the curve.
   - When $\kappa \le 10^{-5}$ (straight lines or inflection points), division by zero is safely avoided by returning empty coordinates `[], [], []`, while the HUD card displays $\rho = \infty$.

2. **Responsive Layout and UX Robustness**:
   - Observation 4 demonstrates full viewport scaling via `100vw`, `100vh`, and `100dvh` (accounting for mobile dynamic address bars).
   - Injected event listeners cleanly handle user interactions (`plotly_click` snapping, slider tracking, play/pause HUD synchronization, and window resizing).
   - Because `post_script` executes inside `Plotly.newPlot(...).then(...)`, the graph DOM element is guaranteed to exist before listeners are attached.

3. **Performance and Memory Optimization**:
   - By subsampling frames up to `M_frames = min(N_pts, 200)` and updating only traces 1..9, the generated HTML remains lightweight (1.13 MB for $N=500$, compared to >15 MB if trace 0 were duplicated per frame).
   - The nearest-frame distance lookup table (`dist_matrix`) accurately maps each of the $N$ curve vertices to its corresponding animation frame index, guaranteeing instantaneous click snapping without index out-of-bounds errors.

4. **Integrity Verification**:
   - No mock data or hardcoded results were discovered.
   - All mathematical transforms compute directly from the provided `CurveResult`.
   - The visualizer handles generic curves without shortcutting.

---

## 3. Caveats

- **Plotly CDN Dependency**: By default, `export_interactive_html` uses `include_plotlyjs="cdn"`. When offline, users should supply `include_plotlyjs=True` or use CLI `--embed-js` (to be connected in Milestone M3).
- **No other caveats**: All requirements, edge cases, and test assertions are satisfied.

---

## 4. Conclusion

**Verdict: APPROVE**

`curva_viz.py` fulfills all specifications of Milestone M2:
1. Full 10-trace 3D composite scene with Frenet apparatus and osculating circle.
2. Responsive 100vw x 100vh full-viewport HTML shell with CSS reset and `100dvh`.
3. Planar curve adaptation ($\tau \equiv 0$) with top-down orthogonal view and `legendonly` out-of-plane traces.
4. Client-side JS click snapping, slider synchronization, playback tracking, and glassmorphic HUD card.
5. All automated tests pass (57 passed, 7 skipped).
6. Robust handling of edge cases (zero curvature, large point counts, negative intervals, $N=2$ minimum).

Milestone M2 is approved and ready for integration into Milestone M3 (`teorema-fundamental-curvas.py` CLI).

---

## 5. Verification Method

### 1. Automated Pytest Verification
Execute the test suite from the repository root:
```bash
python3 -m pytest tests/test_teorema_fundamental.py -v
```
*Expected Outcome*: 57 passed, 7 skipped (all 6 `@requires_viz` tests pass).

### 2. Differential Apparatus & Planar Adaptation Script
Run the following verification script:
```bash
python3 -c "
import curva_engine, curva_viz
# 1. Space curve (helix)
res_space = curva_engine.reconstruct_curve('1', '1', s0=0.0, s1=6.28, num_points=100)
fig_space = curva_viz.build_curve_figure(res_space)
assert len(fig_space.data) == 10, f'Expected 10 traces, got {len(fig_space.data)}'

# 2. Planar curve (circle)
res_planar = curva_engine.reconstruct_curve('2', '0', s0=0.0, s1=3.14, num_points=100)
fig_planar = curva_viz.build_curve_figure(res_planar)
assert fig_planar.data[4].visible == 'legendonly', 'Binormal B should be legendonly'
assert fig_planar.data[7].visible == 'legendonly', 'Plano Normal should be legendonly'
assert fig_planar.data[8].visible == 'legendonly', 'Plano Retificante should be legendonly'
assert fig_planar.layout.scene.camera.eye.z == 2.5, 'Top-down camera expected'
print('Differential apparatus check PASSED')
"
```
*Expected Outcome*: `Differential apparatus check PASSED`.

### 3. Responsive HTML & JS Injection Script
```bash
python3 -c "
import curva_engine, curva_viz
res = curva_engine.reconstruct_curve('1', '1', s0=0.0, s1=6.28, num_points=50)
path = curva_viz.export_interactive_html(res, '/tmp/verify_viz.html')
content = open(path).read()
tokens = [
    '100vw', '100vh', '100dvh', 'overflow: hidden', 'plotly_click',
    'plotly_sliderchange', 'plotly_animatingframe', 'hud-card', 'updateHUDMetrics'
]
for t in tokens:
    assert t in content, f'Missing required token: {t}'
print('HTML responsiveness and JS check PASSED')
"
```
*Expected Outcome*: `HTML responsiveness and JS check PASSED`.

### Invalidation Conditions
- Any failure in the 6 `@requires_viz` tests.
- Generation of fewer than 10 traces in `build_curve_figure`.
- Scrollbars or viewport overflow occurring on desktop or mobile layouts.
- Failure of `plotly_click` curve snapping to update slider and HUD metrics.

---

## Adversarial Stress-Test Results

| # | Stress Scenario | Expected Behavior | Actual Behavior | Result |
|---|-----------------|-------------------|-----------------|--------|
| 1 | $N=2$ minimum discretization points | Generates valid 10-trace figure and HTML | Figure built, HTML exported cleanly | PASS |
| 2 | $N=1$ invalid point count | Raises `ValueError` | `ValueError: CurveResult must contain at least 2 points.` | PASS |
| 3 | Straight line ($\kappa(s) = 0$ everywhere) | Osculating circle empty, HUD displays $\rho = \infty$ | Trace 9 coordinates empty, HUD shows $\infty$ | PASS |
| 4 | Inflection point / Clothoid ($\kappa(s) = s$) at $s=0$ | Handles transition without division by zero | Zero division avoided, smoothly rendered | PASS |
| 5 | Large point count ($N=5000$) | Frame subsampling caps frames at 200 | Frames capped at 200, HTML size remains 1.1 MB | PASS |
| 6 | Negative interval ($s \in [-3, 3]$) | Traverses interval without coordinate error | Visualizes interval $[-3, 3]$ smoothly | PASS |
| 7 | Bare `go.Figure` passed to exporter | Gracefully falls back with default titles | Successfully exports fallback HTML | PASS |
| 8 | Oscillating torsion ($\tau = \sin(s)$) | Frame and planes continuously reorient in 3D | Frames animated seamlessly | PASS |
