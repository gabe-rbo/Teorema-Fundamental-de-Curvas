# Survey Report: Codebase, Environment, Git/GitHub, and CLI Specification

**Agent**: `teamwork_preview_explorer_survey_2`  
**Milestone**: Survey (Fundamental Theorem of Curves)  
**Target File**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/teamwork_preview_explorer_survey_2/handoff.md`  

---

## 1. Observation

Direct observations obtained through exact terminal commands, filesystem inspection, and environment queries:

### 1.1 Workspace & Git Repository Status
- **Target Working Directory**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas`
- **Command**:
  ```bash
  ls -la && git status && git log -n 5 2>&1
  ```
- **Output**:
  ```
  total 0
  drwxr-xr-x@  3 gabrielribeiro  staff   96 Sep 30 11:42 .
  drwx------@ 19 gabrielribeiro  staff  608 Sep 30 10:53 ..
  drwxr-xr-x@  3 gabrielribeiro  staff   96 Sep 30 11:42 .agents
  fatal: not a git repository (or any of the parent directories): .git
  ```
- **Observation Summary**:
  - The repository directory is completely pristine; only `.agents/` exists (containing agent coordination metadata).
  - No project code (`teorema-fundamental-curvas.py`), tests (`tests/`), or documentation (`README.md`, `requirements.txt`) exist yet.
  - Git is **not initialized** (`fatal: not a git repository`). No local commits, no branches, and no remotes exist locally.

### 1.2 Python Environment & Installed Packages
- **Command**:
  ```bash
  which -a python3; which -a python; python3 --version; uname -a
  ```
- **Output**:
  ```
  /Library/Frameworks/Python.framework/Versions/3.11/bin/python3
  /usr/local/bin/python3
  /usr/bin/python3
  python not found
  Python 3.11.9
  Darwin MacBook-Pro-de-Gabriel.local 27.0.0 Darwin Kernel Version 27.0.0: Tue Aug 11 21:05:27 PDT 2026; root:xnu-13432.1.9~1/RELEASE_ARM64_T8103 arm64
  ```
- **Package Status Verification**:
  ```bash
  python3 -c "
  for pkg in ['numpy', 'scipy', 'sympy', 'plotly', 'pytest']:
      try:
          mod = __import__(pkg)
          print(f'{pkg}: {getattr(mod, \"__version__\", \"installed\")}')
      except ImportError as e:
          print(f'{pkg}: NOT INSTALLED ({e})')
  "
  ```
- **Output**:
  ```
  numpy: 2.4.6
  scipy: 1.17.1
  sympy: 1.14.0
  plotly: 7.1.0
  pytest: NOT INSTALLED (No module named 'pytest')
  ```
- **Dry-run Package Resolution for Pytest**:
  ```bash
  pip3 install --dry-run pytest 2>&1
  ```
  Successfully resolved `pytest-9.1.1` along with dependencies `iniconfig-2.3.0`, `pluggy-1.6.0`, and `Pygments-2.21.0`.

### 1.3 GitHub CLI & Git Identity Status
- **Commands**:
  ```bash
  git config --global --list && gh auth status && gh api user
  gh repo view gabe-rbo/Teorema-Fundamental-de-Curvas 2>&1
  ```
- **Output**:
  ```
  user.name=gabe-rbo
  user.email=gabriel.ribeiro@dcc.ufmg.br
  init.defaultbranch=main
  credential.helper=osxkeychain
  github.com
    ✓ Logged in to github.com account gabe-rbo (keyring)
    - Active account: true
    - Git operations protocol: ssh
    - Token: gho_************************************
    - Token scopes: 'admin:public_key', 'gist', 'read:org', 'repo'
  {
    "login": "gabe-rbo",
    "name": "Gabriel Ribeiro",
    "email": "gabriel.ribeiro@dcc.ufmg.br",
    "public_repos": 25,
    ...
  }
  GraphQL: Could not resolve to a Repository with the name 'gabe-rbo/Teorema-Fundamental-de-Curvas'. (repository)
  ```
- **Observation Summary**:
  - Global git user: `gabe-rbo <gabriel.ribeiro@dcc.ufmg.br>`.
  - Default branch configured as `main`.
  - GitHub CLI (`gh`) is fully authenticated for user `gabe-rbo` with `repo` and `ssh` permissions.
  - The target remote repository `gabe-rbo/Teorema-Fundamental-de-Curvas` does not yet exist on GitHub.

### 1.4 CLI & Acceptance Criteria Requirements
From `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/.agents/teamwork/ORIGINAL_REQUEST.md`:
- Lines 33-43:
  - Command: `teorema-fundamental-curvas.py`
  - Arguments:
    - `curvatura`: mathematical expression or constant for $\kappa(s)$ (required positional or flagged).
    - `torcao`: mathematical expression or constant for $\tau(s)$ (optional, defaults to `"0"` for planar curves).
    - `--intervalo` / `-i`: start and end of arc length interval $[s_0, s_1]$ (default: $[0, 2\pi]$ or $[0, 10]$).
    - `--num-pontos` / `-n`: number of discretization points (default: 500).
    - `--output` / `-o`: output HTML filename (optional).
  - Filename template: `<identificacao_da_curva>-k<curvatura>-t<torcao>-I<InicioIntervalo_FimIntervalo>.html`.
  - Sanitization requirement: replace unsafe characters (e.g. `/` replaced by `_div_`, `*` by `_mult_`).
- Acceptance criteria (lines 75-79):
  - `python teorema-fundamental-curvas.py "1" "1" -i 0 6.28` produces `helice_circular-k1-t1-I0_6.28.html`.
  - `python teorema-fundamental-curvas.py "1" -i 0 6.28` produces `circulo-k1-t0-I0_6.28.html`.
  - `python teorema-fundamental-curvas.py ... -o test_out.html` writes directly to `test_out.html`.

---

## 2. Logic Chain

1. **Workspace Initial State**:
   - Observation 1.1 shows no `.git` repository and an empty workspace.
   - Therefore, the project implementation must include initializing git (`git init -b main`), adding source code, creating the remote repository (`gh repo create gabe-rbo/Teorema-Fundamental-de-Curvas --public --source=. --remote=origin --push`), and pushing the first commit.

2. **Environment & Dependency Chain**:
   - Observation 1.2 shows that `python3` (3.11.9) is installed, but the unversioned binary `python` is **not** in PATH (`python not found`).
   - Therefore, commands executed in the shell must use `python3` (e.g. `python3 teorema-fundamental-curvas.py`) or the CLI script must provide a hashbang `#!/usr/bin/env python3` and executable permissions (`chmod +x`).
   - Furthermore, `numpy` (2.4.6), `scipy` (1.17.1), `sympy` (1.14.0), and `plotly` (7.1.0) are present in site-packages, but `pytest` is absent.
   - Therefore, `pytest` must be installed (`pip3 install pytest`) prior to running automated unit and integration tests.

3. **Git/GitHub Publishing Feasibility**:
   - Observation 1.3 shows `gh auth status` is authenticated as `gabe-rbo` with `repo` and `admin:public_key` scopes using SSH.
   - Observation 1.3 confirms `gabe-rbo/Teorema-Fundamental-de-Curvas` does not currently exist on GitHub.
   - Therefore, the deployment step has all necessary credentials to create the remote repository and push commits automatically without requiring user credentials or token prompts.

4. **CLI Argument Parser Architecture**:
   - Requirements dictate positional arguments for `curvatura` and optional `torcao` (defaulting to `"0"`), but also allow flagged equivalents (`-k`, `-t`).
   - Using `argparse`, `curvatura` is defined as a positional string argument (or optionally populated via `-k` / `--curvatura`), `torcao` is positional with `nargs='?'` and default `"0"` (or optionally populated via `-t` / `--torcao`).
   - `--intervalo` / `-i` takes two floats `nargs=2, type=float, default=[0.0, 6.28]`, with metavar `('S0', 'S1')`.
   - `--num-pontos` / `-n` takes an integer `type=int, default=500`, with metavar `'N'`.
   - `--output` / `-o` takes an optional string `type=str, default=None`, with metavar `'ARQUIVO'`.
   - This specification exactly accommodates `python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28` and `python3 teorema-fundamental-curvas.py "1" -i 0 6.28`.

5. **Filename Generation & Sanitization Logic**:
   - The required structure is:
     $$\text{filename} = \langle\text{identificacao\_da\_curva}\rangle\text{-k}\langle\text{curvatura\_sanitizada}\rangle\text{-t}\langle\text{torcao\_sanitizada}\rangle\text{-I}\langle s_0\rangle\_\langle s_1\rangle\text{.html}$$
   - The interval representation must map floats cleanly without trailing `.0` when whole: formatting via Python's `:g` format (`f"{s0:g}_{s1:g}"`) transforms `0.0` and `6.28` to `0_6.28`, and `0.0` and `10.0` to `0_10`.
   - The sanitization routine `sanitize_expr(expr_str)` applies the following sequential substitutions:
     1. Strip leading and trailing whitespace; remove internal spaces: `s.replace(" ", "")`
     2. Power operations: replace `**` with `_pow_`, and `^` with `_pow_`
     3. Multiplication: replace `*` with `_mult_`
     4. Division: replace `/` with `_div_`
     5. Addition: replace `+` with `_plus_`
     6. Parentheses: replace `(` with `_lpar_`, `)` with `_rpar_`
     7. Other filesystem-reserved characters (`\`, `:`, `?`, `"`, `<`, `>`, `|`): replace with `_`
   - Evaluation with Acceptance Criteria:
     - Input `curvatura="1"`, `torcao="1"`, `intervalo=[0, 6.28]`, classified as `helice_circular`:
       $\to$ `helice_circular-k1-t1-I0_6.28.html` (matches Acceptance Criteria exactly).
     - Input `curvatura="1"`, `torcao="0"` (default), `intervalo=[0, 6.28]`, classified as `circulo`:
       $\to$ `circulo-k1-t0-I0_6.28.html` (matches Acceptance Criteria exactly).

6. **Error Handling Architecture**:
   - **Syntax Errors**: If SymPy parsing fails (`SympifyError`, `SyntaxError`), raise a descriptive error specifying the invalid expression and exit with code 1.
   - **Invalid Free Symbols**: Check `expr.free_symbols - {Symbol('s')}`. If symbols other than `s` exist (e.g. $x, y, t$), report error requiring only parameter `s` and exit with code 1.
   - **Domain / Singularity Errors**: Prior to ODE integration, evaluate $\kappa(s)$ and $\tau(s)$ over the discretized interval. If any evaluation produces `nan`, `inf`, or `-inf` (such as $1/s$ at $s=0$), report singularity at domain and exit with code 1.
   - **Interval Validation**: Verify $s_0 < s_1$ and bounds are finite. If $s_0 \ge s_1$, exit with code 1 (`s0 must be strictly less than s1`).
   - **Point Count Validation**: Verify $N \ge 2$. If $N < 2$, exit with code 1.
   - **ODE Integration Failure**: Check `solve_ivp` result `res.success`. If numerical integration diverges or fails to converge, report solver message and exit with code 1.
   - **Missing CLI Arguments**: Handled by `argparse`, writing to `stderr` with exit code 2.

---

## 3. Caveats

1. **Python Command Invocation**:
   On macOS, running `python` fails because only `python3` is available in `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3`. Documentation and tests should either instruct running `python3 teorema-fundamental-curvas.py` or provide executable permissions (`chmod +x`) with `#!/usr/bin/env python3`.
2. **Pytest Dependency**:
   `pytest` is not currently installed in the Python 3.11 environment. Prior to executing the test runner track, `pip3 install pytest` must be executed.
3. **Signed vs Absolute Curvature in Planar Curves**:
   In strict 3D differential geometry, curvature is $\kappa(s) \ge 0$ by definition. However, user input might include negative expressions (e.g. `"-1"` or `"-cos(s)"`). The implementation should either support signed curvature for planar curves or automatically take $|\kappa(s)|$ for the Frenet apparatus while maintaining correct turning direction in the plane.

---

## 4. Conclusion

1. **Workspace**: Pristine. Ready for initial development. Git initialization and GitHub repository creation (`gabe-rbo/Teorema-Fundamental-de-Curvas`) will be executed via `git` and `gh` CLI.
2. **Environment**: Python 3.11.9 is ready with `numpy 2.4.6`, `scipy 1.17.1`, `sympy 1.14.0`, and `plotly 7.1.0`. `pytest` requires installation (`pip3 install pytest`).
3. **GitHub CLI**: Fully authenticated as `gabe-rbo` with SSH transport and repo scopes. Remote repo does not yet exist and is ready to be created.
4. **CLI Specification**:
   - Positional: `curvatura` (str), `torcao` (str, default `"0"`).
   - Flags: `-k/--curvatura`, `-t/--torcao`, `-i/--intervalo S0 S1` (default `0 6.28`), `-n/--num-pontos N` (default `500`), `-o/--output ARQUIVO` (default `None`).
   - Automatic naming matches acceptance criteria: `helice_circular-k1-t1-I0_6.28.html` and `circulo-k1-t0-I0_6.28.html`.
5. **Error Handling**: Rigorous input validation rules for syntax, variable namespace, singularities, interval ordering, and ODE convergence.

---

## 5. Verification Method

To independently reproduce and verify this investigation:

1. **Verify Workspace & Git Status**:
   ```bash
   cd /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas
   git status
   # Expected: fatal: not a git repository
   ```

2. **Verify Python Environment & Dependencies**:
   ```bash
   python3 --version
   # Expected: Python 3.11.9
   python3 -c "import numpy, scipy, sympy, plotly; print('All math & viz packages OK')"
   # Expected: All math & viz packages OK
   python3 -c "import pytest" 2>&1
   # Expected: ModuleNotFoundError: No module named 'pytest'
   ```

3. **Verify GitHub CLI Authentication & Remote Status**:
   ```bash
   gh auth status
   # Expected: Logged in to github.com account gabe-rbo
   gh repo view gabe-rbo/Teorema-Fundamental-de-Curvas 2>&1
   # Expected: Could not resolve to a Repository with the name 'gabe-rbo/Teorema-Fundamental-de-Curvas'
   ```

4. **Verify CLI Parser and Filename Sanitization**:
   Execute the standalone validation test:
   ```bash
   python3 -c "
   import argparse

   def sanitize_expr(expr: str) -> str:
       s = expr.strip().replace(' ', '')
       s = s.replace('**', '_pow_').replace('^', '_pow_')
       s = s.replace('*', '_mult_').replace('/', '_div_').replace('+', '_plus_')
       s = s.replace('(', '_lpar_').replace(')', '_rpar_')
       for c in ['\\\\', ':', '?', '\"', '<', '>', '|']:
           s = s.replace(c, '_')
       return s

   def generate_filename(curve_type, k_str, t_str, s0, s1):
       return f'{curve_type}-k{sanitize_expr(k_str)}-t{sanitize_expr(t_str)}-I{s0:g}_{s1:g}.html'

   # Test Acceptance Criteria 1: Circular Helix
   fn1 = generate_filename('helice_circular', '1', '1', 0.0, 6.28)
   assert fn1 == 'helice_circular-k1-t1-I0_6.28.html', f'Failed: {fn1}'

   # Test Acceptance Criteria 2: Circle
   fn2 = generate_filename('circulo', '1', '0', 0.0, 6.28)
   assert fn2 == 'circulo-k1-t0-I0_6.28.html', f'Failed: {fn2}'

   print('All acceptance naming assertions passed!')
   "
   ```
   **Expected output**: `All acceptance naming assertions passed!`

5. **Invalidation Conditions**:
   - If `git status` reports an initialized repository before development begins.
   - If `gh auth status` fails or reports an account other than `gabe-rbo`.
   - If the filename generator fails to match `helice_circular-k1-t1-I0_6.28.html` or `circulo-k1-t0-I0_6.28.html`.
