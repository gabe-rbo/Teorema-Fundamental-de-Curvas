# BRIEFING — 2026-09-30T15:20:00Z

## Mission
Implement `curva_viz.py` for the Fundamental Theorem of Curves project, delivering interactive 3D visualization with Frenet-Serret apparatus, selective frame animation, responsive 100vw x 100vh layout, client-side JS snapping, and HUD.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_worker_m2_1
- Original parent: 0b0dffe7-95be-4cd3-9ff5-acde191dd517
- Milestone: M2 (Visualization Engine)

## 🔒 Key Constraints
- Exclusively own `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_viz.py`. Do NOT modify `curva_engine.py` or existing tests.
- Mandatory integrity: no hardcoded test results, genuine mathematical and visual implementation.
- Must satisfy interface contract: `build_curve_figure(curve_data: CurveResult) -> go.Figure` and `export_interactive_html(curve_data: CurveResult, output_path: str, title: str | None = None) -> str`.
- Pass all visualization tests in `tests/test_teorema_fundamental.py`.
- 10-trace 3D apparatus architecture with selective animation frames (`traces=[1..9]`) and `uirevision='constant'`.

## Current Parent
- Conversation ID: 0b0dffe7-95be-4cd3-9ff5-acde191dd517
- Updated: not yet

## Task Summary
- **What to build**: Interactive 3D visualization module `curva_viz.py` using Plotly and custom HTML/JS.
- **Success criteria**: Pytest suite passes completely without skipping visualization tests (57 passed, 7 skipped for M3 CLI), HTML exports are lightweight (~0.5 - 1.2 MB), fully interactive with slider, click-to-snap, and live HUD.
- **Interface contracts**: `PROJECT.md` & `teamwork_preview_spec_miner_survey_3/handoff.md`.
- **Code layout**: Root directory Python module `curva_viz.py`.

## Key Decisions Made
- [Initial] Followed UI Technical Survey from `teamwork_preview_spec_miner_survey_3/handoff.md`.
- [10 Traces Architecture] Implemented Trace 0 (Curva r(s)), Trace 1 (Ponto Ativo), Traces 2-4 (Vetor Tangente T, Normal N, Binormal B), Trace 5 (Reta Tangente L_T), Traces 6-8 (Plano Osculador, Normal, Retificante via Mesh3d), Trace 9 (Círculo Osculador).
- [Selective Frames] Frames update traces 1..9 only (`traces=[1..9]`), leaving Trace 0 static, keeping HTML file size around 0.5-1.1 MB.
- [Legend State Persistence] Omitted `visible` from `go.Frame` data updates so interactive legend toggles by user persist throughout slider scrubbing.
- [Camera Persistence] Set `uirevision='constant'` on layout and scene.
- [Planar Adaptation] For $\tau \equiv 0$, set orthogonal top-down camera (`eye=(0,0,2.5), up=(0,1,0)`), set out-of-plane traces (Binormal, Plano Normal, Plano Retificante) to `'legendonly'` by default, and added 2D/3D camera switch buttons.
- [Zero Curvature Safety] Osculating circle returns empty coordinates `x=[], y=[], z=[]` when $\kappa \le 10^{-5}$ or $\rho > 10 \cdot \text{span}$, and HUD displays `ρ = ∞`.
- [Client-Side JS] Injected `plotly_click`, `plotly_sliderchange`, `plotly_animatingframe`, and `window.resize` handlers in `post_script`.

## Artifact Index
- `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_viz.py` — Core visualization engine and export module.
- `progress.md` — Liveness heartbeat and milestone tracking.
- `handoff.md` — Final 5-component handoff report.

## Change Tracker
- **Files modified**: `curva_viz.py` (created complete implementation, 932 lines)
- **Build status**: 57 passed, 7 skipped (all 6 visualization tests pass)
- **Pending issues**: none

## Quality Status
- **Build/test result**: pytest passed (57 passed, 7 skipped)
- **Lint status**: clean (py_compile passed)
- **Tests added/modified**: 6 unskipped tests verified in `tests/test_teorema_fundamental.py`

## Loaded Skills
- None
