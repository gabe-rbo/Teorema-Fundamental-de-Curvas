## 2026-09-30T15:12:29Z
# Task Assignment: Milestone M2 (Visualization Engine Worker)

You are an agent with archetype `teamwork_preview_worker`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m2_1`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Original user request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
Project master specification: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/orchestrator_1/PROJECT.md`
UI Technical Survey & Specifications: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_3/handoff.md`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Write Ownership
You EXCLUSIVELY own and write:
- `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_viz.py`
Do NOT modify `curva_engine.py` or existing tests.

## Instructions & Scope
1. Read `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `teamwork_preview_spec_miner_survey_3/handoff.md`.
2. Implement `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_viz.py` fulfilling the interface contract:
   - `build_curve_figure(curve_data: CurveResult) -> go.Figure`
   - `export_interactive_html(curve_data: CurveResult, output_path: str, title: str | None = None) -> str`
3. Include all visual specifications from the UI Survey:
   - **10 Traces Architecture**:
     - Trace 0: `Curva r(s)` (`Scatter3d`, `mode='lines+markers'`, `color='#00e5ff'`, clickable vertices with customdata `[s, frameIdx, kappa, tau]`)
     - Trace 1: `Ponto Ativo r(s)` (`Scatter3d`, `mode='markers'`, `color='#ffea00'`, `size=8`)
     - Trace 2: `Vetor Tangente T` (`Scatter3d`, `mode='lines+markers'`, green `#00e676`, `width=7`)
     - Trace 3: `Vetor Normal N` (`Scatter3d`, `mode='lines+markers'`, red `#ff1744`, `width=7`)
     - Trace 4: `Vetor Binormal B` (`Scatter3d`, `mode='lines+markers'`, blue `#2979ff`, `width=7`)
     - Trace 5: `Reta Tangente L_T` (`Scatter3d`, `mode='lines'`, dashed green `#00e676`)
     - Trace 6: `Plano Osculador (T, N)` (`Mesh3d`, amber `#ffd54f`, `opacity=0.25`, flatshading)
     - Trace 7: `Plano Normal (N, B)` (`Mesh3d`, red/coral `#ff5252`, `opacity=0.20`, flatshading)
     - Trace 8: `Plano Retificante (T, B)` (`Mesh3d`, blue `#448aff`, `opacity=0.20`, flatshading)
     - Trace 9: `Círculo Osculador` (`Scatter3d`, `mode='lines'`, gold `#ffd600`, 64 parametric points, centered at $r + \frac{1}{\kappa} N$, radius $\rho = 1/|\kappa|$; handles $\kappa \le 10^{-5}$ by passing empty coordinates `x=[], y=[], z=[]`)
   - **Planar Curve Adaptation**:
     - When $\tau \equiv 0$ (or $\max|\tau| < 10^{-5}$): set initial camera to top-down view `eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0)`, set Normal and Rectifying planes and Binormal vector to `'legendonly'` by default.
   - **Selective Frame Animation & Camera Persistence**:
     - Frames update only traces 1 through 9 (`traces=[1,2,3,4,5,6,7,8,9]`), keeping Trace 0 static to minimize HTML size (~1MB).
     - Set `uirevision='constant'` on layout and scene so user rotation and zoom are NOT reset during scrubbing.
     - Bottom slider with play/pause controls.
   - **Responsive 100vw x 100vh Fullscreen HTML Template**:
     - Inject CSS reset (`* { margin:0; padding:0; box-sizing:border-box; }`, `html, body { width:100vw; height:100vh; height:100dvh; overflow:hidden; }`, `#plot-container { width:100vw; height:100vh; }`).
     - Real-time glassmorphism HUD card displaying curve class, $s$, $r(s)$, $\kappa(s)$, $\tau(s)$, $\rho(s)$.
   - **Client-Side JavaScript Injection**:
     - `plotly_click` listener: clicking any curve vertex extracts `frameIdx` and executes `Plotly.animate` + `Plotly.relayout('sliders[0].active', frameIdx)` + updates HUD.
     - `plotly_sliderchange` listener: updates HUD metrics when slider is dragged.
     - `window.resize` listener: calls `Plotly.Plots.resize`.
4. Test and verify:
   - Run tests: `python3 -m pytest tests/test_teorema_fundamental.py -v`. The visualization tests (previously skipped) must now execute and pass!
   - Generate a sample HTML file (e.g. for circle and helix) and verify it generates valid HTML containing the CSS, traces, frames, and JavaScript listeners.
5. Write your handoff report to `handoff.md` and notify the orchestrator via `send_message`.
