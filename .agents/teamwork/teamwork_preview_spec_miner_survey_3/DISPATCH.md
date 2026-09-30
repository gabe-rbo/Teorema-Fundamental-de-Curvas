# Task Assignment: UI & Visualization Spec Miner

You are an agent with archetype `teamwork_preview_spec_miner`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_3`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Original user request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`

## Objective
Detail the technical specifications and architecture for the responsive Plotly HTML interactive visualization and differential apparatus.

## Scope & Instructions
1. Read `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`.
2. Analyze the requirements for R3 (Interactive Plotly Visualization & Differential Apparatus):
   - 100vw and 100vh responsive layout without unwanted scrollbars.
   - Curve trajectory rendering.
   - Frenet frame unit vectors at active point s: Tangent T (green), Normal N (red), Binormal B (blue).
   - Tangent line rendering: L_T(u) = r(s) + u * T(s).
   - Three planes rendering (spanned as parametric surfaces / mesh / polygon):
     - Osculating plane: spanned by T and N.
     - Normal plane: spanned by N and B.
     - Rectifying plane: spanned by T and B.
   - Osculating circle: radius rho = 1/|kappa|, center c = r + (1/kappa)*N, lying in osculating plane.
   - Planar curve adaptation: clean 2D/3D projection with T and N diedro and osculating circle when tau = 0.
   - Bottom slider scrubbing s from s0 to s1 updating all apparatus elements dynamically.
   - Plotly click event (`plotly_click` JavaScript callback) to jump slider/apparatus immediately when a user clicks any curve point.
   - Legend toggling for each visual component.
3. Specify exact Plotly data structures, trace definitions, slider animation/steps, and custom JavaScript injection methods for `plotly_click` and responsive viewport styling.

## Output Requirements
Write your detailed report to `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_3/handoff.md`.
Include:
- Complete trace and layout architecture
- Mathematical formulas for planes, tangent line, and osculating circle geometry
- Plotly slider configuration & frame update payload
- JavaScript injection code for `plotly_click` and CSS 100vw/100vh
Notify the orchestrator via `send_message` when done.

## 2026-09-30T14:43:59Z
You are assigned to the Fundamental Theorem of Curves project.
Your assigned working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_3
Original user request: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md
Your task assignment details: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_3/DISPATCH.md

Read ORIGINAL_REQUEST.md and DISPATCH.md.
Investigate and produce a detailed UI and visualization technical specification for R3:
1. 100vw x 100vh responsive layout in Plotly HTML without unwanted scrollbars.
2. Differential geometry apparatus:
   - Curve 3D trajectory
   - Unit vectors T (green), N (red), B (blue)
   - Tangent line L_T(u) = r(s) + u*T(s)
   - Three planes: Osculating (span T, N), Normal (span N, B), Rectifying (span T, B)
   - Osculating circle: radius rho = 1/|kappa|, center c = r + (1/kappa)*N in osculating plane
   - Planar curve adaptation: clean projection when tau = 0
3. Bottom slider scrubbing s continuously from s0 to s1 updating position, frame vectors, tangent line, planes, and osculating circle.
4. Plotly click event (`plotly_click` JavaScript injection) allowing clicking any curve point to jump slider and apparatus immediately to that point.
5. Legend toggles for individual components.

Write your final report to /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_spec_miner_survey_3/handoff.md.
Update progress.md in your working directory.
When done, notify the orchestrator with send_message.

