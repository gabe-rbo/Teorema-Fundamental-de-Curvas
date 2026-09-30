# Task Assignment: Codebase & Environment Explorer

You are an agent with archetype `teamwork_preview_explorer`.
Working directory: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_explorer_survey_2`
Project root: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
Original user request: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`

## Objective
Survey the current workspace, Python environment, tools, and CLI specifications.

## Scope & Instructions
1. Read `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`.
2. Inspect the current workspace directory `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`: check existing files, git status, git remotes, and branch status.
3. Check the Python environment and installed libraries: Python version, numpy, scipy, sympy, plotly, pytest.
4. Check GitHub CLI (`gh`) auth status and git config for account `gabe-rbo`.
5. Specify the exact CLI interface for `teorema-fundamental-curvas.py`:
   - Arguments, flags, defaults (`curvatura`, `torcao`, `--intervalo` / `-i`, `--num-pontos` / `-n`, `--output` / `-o`)
   - Filename generation and sanitization algorithm (`<identificacao_da_curva>-k<curvatura>-t<torcao>-I<InicioIntervalo_FimIntervalo>.html`)
   - Error handling for invalid expressions, empty intervals, invalid parameters.

## Output Requirements
Write your detailed report to `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_explorer_survey_2/handoff.md`.
Include:
- Workspace & Git survey
- Environment check results
- Complete CLI spec and filename sanitizer rules
Notify the orchestrator via `send_message` when done.

## 2026-09-30T14:43:59Z
You are assigned to the Fundamental Theorem of Curves project.
Your assigned working directory: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_explorer_survey_2
Original user request: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md
Your task assignment details: /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_explorer_survey_2/DISPATCH.md

Read ORIGINAL_REQUEST.md and DISPATCH.md.
Investigate and report on:
1. Workspace inspection: existing files, git repo status, commits, remotes, branches in /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas.
2. Environment inspection: Python version, installed packages (numpy, scipy, sympy, plotly, pytest).
3. GitHub CLI status: gh auth status, git user/email configuration, access to account gabe-rbo.
4. CLI specification for teorema-fundamental-curvas.py: exact arguments (curvatura, torcao, --intervalo/-i, --num-pontos/-n, --output/-o), default values, sanitization logic for filename formatting (<identificacao_da_curva>-k<curvatura>-t<torcao>-I<InicioIntervalo_FimIntervalo>.html).
5. CLI error handling requirements.

Write your final report to /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_explorer_survey_2/handoff.md.
Update progress.md in your working directory.
When done, notify the orchestrator with send_message.

