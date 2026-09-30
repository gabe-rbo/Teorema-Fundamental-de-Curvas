# Task Assignment: Replacement Forensic Auditor for Milestone M2 (Visualization Engine)

You are an agent with archetype `teamwork_preview_auditor`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_auditor_m2_fresh`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Original user request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
Implementation target: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_viz.py`

## Instructions
1. Perform forensic integrity audit of `curva_viz.py`:
   - Static analysis: check for hardcoded HTML, fake SVG/Plotly structures, dummy coordinates, or facade visualization logic.
   - Runtime tracing: verify `build_curve_figure` authentically constructs Plotly traces with genuine 3D coordinates from `CurveResult`, authentic normal/tangent/binormal vectors, genuine Mesh3d planes, and genuine parametric circles.
   - Interactive tracing: verify `export_interactive_html` authentically generates valid HTML with responsive CSS and genuine JavaScript event bindings.
2. Deliver binary verdict: `CLEAN` or `INTEGRITY VIOLATION`.
3. Write full evidence report to `handoff.md` and notify orchestrator via `send_message`.

## 2026-09-30T15:29:05Z
You are assigned to the Fundamental Theorem of Curves project.
Your assigned working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_auditor_m2_fresh
Project root: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas
Original user request: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md
Your detailed task assignment: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_auditor_m2_fresh/DISPATCH.md
Implementation to audit: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_viz.py

Perform forensic integrity audit of curva_viz.py for hardcoded HTML, dummy visual structures, mock traces, or test circumventing.
Deliver your binary verdict: CLEAN or INTEGRITY VIOLATION.
Write full evidence report to handoff.md and notify orchestrator with send_message.

