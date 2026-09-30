# Forensic Audit Handoff Report — Milestone M3 (CLI Interface)

**Work Product**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`  
**Profile**: General Project  
**Integrity Mode**: Development (as specified in `ORIGINAL_REQUEST.md`)  
**Verdict**: **`CLEAN`**

---

## 1. Observation

### 1.1 Static Code & AST Analysis
- **File**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py` (257 lines, 8,243 bytes).
- **Functions Defined**:
  - `build_argument_parser() -> argparse.ArgumentParser` (lines 53–121)
  - `parse_arguments(argv: list[str] | None = None) -> argparse.Namespace` (lines 124–168)
  - `run_pipeline(args: argparse.Namespace) -> int` (lines 170–246)
  - `main(argv: list[str] | None = None) -> None` (lines 248–257)
- **AST Constant Inspection**:
  - AST walk across all 68 string constants revealed 0 hardcoded test results, 0 mock values, 0 dummy data structures, and 0 test bypass tokens.
  - No conditional logic branching on specific test names, test inputs, or magic strings.
- **Module Imports**:
  - Line 49: `import curva_engine`
  - Line 50: `import curva_viz`
  - Both modules are imported at module level and actively invoked in `run_pipeline`.

### 1.2 Dynamic Call-Graph Tracing
Dynamic interception using `unittest.mock.patch` was performed on `curva_engine.reconstruct_curve`, `curva_viz.export_interactive_html`, and `curva_engine.solve_ivp`:
1. **Pipeline Delegation to `curva_engine`**:
   - Command: `parse_arguments(['3 + s', '0.5*s', '-i', '0', '2', '-n', '50', '-o', '/tmp/audit_test_1.html'])`
   - Intercepted Call: `curva_engine.reconstruct_curve((), {'kappa_expr_str': '3 + s', 'tau_expr_str': '0.5*s', 's0': 0.0, 's1': 2.0, 'num_points': 50})`
   - Observation: Exact parameters passed without transformation, bypass, or shortcut.
2. **ODE Integration Verification**:
   - Intercepted Call on `curva_engine.solve_ivp`:
     - Method: `DOP853`
     - `t_span`: `(0.0, 3.14)`
     - `t_eval`: 60 points
     - Solves genuine 12-state Frenet-Serret system: $T'(s) = \kappa N$, $N'(s) = -\kappa T + \tau B$, $B'(s) = -\tau N$, $r'(s) = T$.
3. **Pipeline Delegation to `curva_viz`**:
   - Intercepted Call: `curva_viz.export_interactive_html(curve_data=curve_data, output_path='/tmp/audit_test_1.html')`
   - File created: `/tmp/audit_test_1.html` (size: 365,809 bytes).
   - Verifications on output content:
     - `Plotly.newPlot`: True
     - `100vw`: True
     - `100vh` / `100dvh`: True
     - `plotly_click`: True
     - `frame_0`, `slider`, `steps`: True

### 1.3 Pre-Populated Artifact & Dynamic Recreation Test
- Observation: Files `helice_circular-k1-t1-I0_6.28.html` and `circulo-k1-t0-I0_6.28.html` were present in the workspace root.
- Experiment: Both files were explicitly deleted via `Path.unlink()`.
- Dynamic Recreation:
  - Executed: `python3 teorema-fundamental-curvas.py 1 1 -i 0 6.28`
    - Result: `helice_circular-k1-t1-I0_6.28.html` re-created (size: 1,188,626 bytes, fresh mtime).
  - Executed: `python3 teorema-fundamental-curvas.py 1 -i 0 6.28`
    - Result: `circulo-k1-t0-I0_6.28.html` re-created (size: 960,360 bytes, fresh mtime).
- Dynamic Output Variance & Mathematical Fidelity:
  - Curve A (`kappa=2, tau=0, [0, 3.14], n=50`): SHA-256 `7ebf758905966dfb09fb9aed344d49020acb0aa293436608ff5f4b528fad4556`, size: 253,422 bytes. Reconstructed endpoint matches $x=-0.0016, y=0.0000, z=0.0000$.
  - Curve B (`kappa=0.5, tau=2, [1, 5], n=120`): SHA-256 `cecb1cc72548bf6922915e2d82b702ab34f94b9234d2a0acdc59a48545f24351`, size: 709,819 bytes.
  - Observation: Output varies deterministically based on parameters; zero static caching or hardcoded HTML payloads.

### 1.4 CLI Matrix & Exit Code Validation
11 CLI test scenarios were executed via subprocess:
1. `python3 teorema-fundamental-curvas.py 1 -i 0 6.28` -> exit 0, classified `circulo` (PASS)
2. `python3 teorema-fundamental-curvas.py 1 1 -i 0 6.28` -> exit 0, classified `helice_circular` (PASS)
3. `python3 teorema-fundamental-curvas.py -k 2 -t 0.5 -i 0 3 -n 80` -> exit 0, classified `helice_circular` (PASS)
4. `python3 teorema-fundamental-curvas.py s 0 -i 0 4` -> exit 0, classified `espiral_de_cornu` (PASS)
5. `python3 teorema-fundamental-curvas.py` (missing curvature) -> exit 2 (argparse error, PASS)
6. `python3 teorema-fundamental-curvas.py 1 -i 5 2` (inverted interval $s_0 \ge s_1$) -> exit 1 (validation error, PASS)
7. `python3 teorema-fundamental-curvas.py 1 -n 1` (points < 2) -> exit 1 (validation error, PASS)
8. `python3 teorema-fundamental-curvas.py -2 0` (negative curvature $\kappa < 0$) -> exit 1 (math error, PASS)
9. `python3 teorema-fundamental-curvas.py "__import__('os').system('ls')"` (AST injection) -> exit 1 (security error, PASS)
10. `python3 teorema-fundamental-curvas.py "1/s" 0 -i 0 2` (singularity at origin) -> exit 1 (math error, PASS)
11. `python3 teorema-fundamental-curvas.py 1 0 unexpected_arg` (unexpected positionals) -> exit 2 (argparse error, PASS)

### 1.5 Full Project Test Suite Execution
- Command: `pytest -v tests/`
- Output: `156 passed, 5 warnings in 25.44s` (exit code 0).
- All 156 unit and end-to-end tests across Tier 1 (Coverage), Tier 2 (Boundaries), Tier 3 (Cross-combinations), and Tier 4 (Analytical benchmarks) passed without regressions.

---

## 2. Logic Chain

1. **Premise 1 (Absence of Hardcoding)**: Static AST inspection of `teorema-fundamental-curvas.py` shows no static return values, test fixtures, or pre-computed outputs (Section 1.1).
2. **Premise 2 (Legitimate Pipeline Coordination)**: Dynamic call interception confirms that `run_pipeline` directly delegates to `curva_engine.reconstruct_curve` and `curva_viz.export_interactive_html` with exact user arguments, and that `curva_engine` genuinely invokes SciPy's `solve_ivp` with `DOP853` to integrate the differential equations (Section 1.2).
3. **Premise 3 (Authentic Artifact Generation)**: Unlinking and regenerating the output HTML files proved that files are created dynamically at runtime with non-identical SHA-256 hashes matching the mathematical trajectories of the ODE solver (Section 1.3).
4. **Premise 4 (Robust CLI Error Handling)**: Subprocess execution confirmed strict conformance with POSIX and argparse standards (exit code 0 for valid runs, exit code 1 for validation/math failures, exit code 2 for CLI syntax errors) (Section 1.4).
5. **Premise 5 (Multi-Mode Integrity Conformance)**:
   - Under *Development Mode* (user's mandate in `ORIGINAL_REQUEST.md`): No fake outputs, no facade stubs, genuine implementation throughout -> CLEAN.
   - Under *Demo Mode*: Core logic built by the repository team, genuine implementation -> CLEAN.
   - Under *Benchmark Mode*: Scientific stack (SciPy, SymPy, Plotly) used as explicitly specified in prompt requirements R1/R3 -> CLEAN.

**Deduction**: `teorema-fundamental-curvas.py` is an authentic, non-facade implementation that fully adheres to project specifications and mathematical integrity standards.

---

## 3. Caveats

- **External GUI Rendering**: Visual inspection in a physical browser window was not performed in this headless environment; however, HTML/JS structural compliance (CSS resets, WebGL container, Plotly scripts, slider steps, `plotly_click` listener) was verified directly from the serialized file contents.
- **No other caveats**: All components were empirically tested and traced.

---

## 4. Conclusion

**Verdict: `CLEAN`**

`teorema-fundamental-curvas.py` contains zero integrity violations. It genuinely reconstructs space curves via the Frenet-Serret ODE system using `curva_engine` and exports responsive interactive 3D Plotly visualizations using `curva_viz`.

---

## 5. Verification Method

To independently reproduce and verify this audit verdict:

1. **Verify full test suite (156 tests)**:
   ```bash
   pytest -v tests/
   ```
2. **Verify dynamic file generation and acceptance criteria**:
   ```bash
   # Remove pre-existing files
   rm -f circulo-k1-t0-I0_6.28.html helice_circular-k1-t1-I0_6.28.html
   
   # Run acceptance helix
   python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28
   test -f helice_circular-k1-t1-I0_6.28.html && echo "Helix generated successfully"
   
   # Run acceptance circle
   python3 teorema-fundamental-curvas.py "1" -i 0 6.28
   test -f circulo-k1-t0-I0_6.28.html && echo "Circle generated successfully"
   ```
3. **Verify CLI error handling**:
   ```bash
   python3 teorema-fundamental-curvas.py; test $? -eq 2 && echo "Exit code 2 verified"
   python3 teorema-fundamental-curvas.py "1" -i 5 2; test $? -eq 1 && echo "Exit code 1 verified"
   ```
4. **Invalidation condition**: Any hardcoded coordinates, mock ODE integrations, or failure to generate authentic interactive HTML upon valid CLI invocation.
