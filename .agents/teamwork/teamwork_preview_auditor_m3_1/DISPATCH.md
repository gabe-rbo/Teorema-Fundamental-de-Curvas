# Task Assignment: Forensic Auditor for Milestone M3 (CLI Interface)

You are an agent with archetype `teamwork_preview_auditor`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_auditor_m3_1`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Original user request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`
Implementation target: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`

## Instructions
1. Perform forensic integrity audit of `teorema-fundamental-curvas.py`:
   - Static analysis: check for hardcoded CLI outputs, mock exit codes, or bypassing `curva_engine` or `curva_viz`.
   - Dynamic tracing: verify that running the CLI genuinely triggers `curva_engine.reconstruct_curve` and `curva_viz.export_interactive_html`, genuinely integrates the ODEs, and genuinely creates the output HTML.
2. Deliver binary verdict: `CLEAN` or `INTEGRITY VIOLATION`.
3. Write full evidence report to `handoff.md` and notify orchestrator via `send_message`.

## 2026-09-30T15:43:50Z
You are assigned to the Fundamental Theorem of Curves project.
Your assigned working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_auditor_m3_1
Project root: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas
Original user request: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md
Your detailed task assignment: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_auditor_m3_1/DISPATCH.md
Implementation to audit: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py

Perform forensic integrity audit of teorema-fundamental-curvas.py for hardcoded outputs, fake executions, or bypassing the math and viz modules.
Deliver your binary verdict: CLEAN or INTEGRITY VIOLATION.
Write full evidence report to handoff.md and notify orchestrator with send_message.
