# Milestone M3 Review and Adversarial Challenge Report

## Review Summary

- **Verdict**: **APPROVE**
- **Target File**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`
- **Integrity Assessment**: **NO INTEGRITY VIOLATIONS DETECTED**. Zero hardcoded curve solutions, zero facade/dummy implementations, genuine ODE integration (`solve_ivp` DOP853/RK45 with $rtol=10^{-9}, atol=10^{-9}$), genuine Modified Gram-Schmidt orthonormalization in $\mathrm{SO}(3)$, and authentic Plotly interactive visualization output.
- **Automated Test Results**: **64 passed, 0 failed, 3 warnings** (`python3 -m pytest tests/test_teorema_fundamental.py -v`).

---

## 1. Observation

### 1.1 Test Suite Execution
Command executed:
```bash
python3 -m pytest tests/test_teorema_fundamental.py -v
```
Output:
```text
tests/test_teorema_fundamental.py::TestMathematicalOracleModels::test_oracle_vectorized_gram_schmidt_so3 PASSED [  6%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_ode_integration_solution_shape PASSED [  7%]
...
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_cli_defaults PASSED [ 34%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_cli_positional_both PASSED [ 35%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_cli_flags_short PASSED [ 37%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_cli_flags_long PASSED [ 39%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_cli_missing_required PASSED [ 40%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_filename_helix_acceptance PASSED [ 42%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_filename_circle_acceptance PASSED [ 43%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_filename_sanitization_powers PASSED [ 45%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_filename_sanitization_operators PASSED [ 46%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_filename_sanitization_division PASSED [ 48%]
tests/test_teorema_fundamental.py::TestTier1FeatureCoverage::test_tier1_filename_custom_output_preserved PASSED [ 50%]
...
tests/test_teorema_fundamental.py::TestTier2BoundaryAndCornerCases::test_tier2_interval_inverted_cli_exit_code PASSED [ 68%]
...
======================== 64 passed, 3 warnings in 8.16s ========================
```

### 1.2 CLI Argument Handling & Defaults Observation
In `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`:
- Lines 64-120: `build_argument_parser()` defines positional slots `pos_curvatura`, `pos_torcao`, alongside flags `-k`/`--curvatura`, `-t`/`--torcao`, `-i`/`--intervalo` (default `[0.0, 6.28]`), `-n`/`--num-pontos` (default `500`), and `-o`/`--output` (default `None`).
- Lines 139-167: `parse_arguments()` harmonizes positional and flag arguments. When `curvatura` is omitted, `parser.error()` is called. When `torcao` is omitted, it defaults to `"0"`. Unrecognized excess positional arguments trigger `parser.error()`.
- Verified live command executions:
  * Missing required arguments: `python3 teorema-fundamental-curvas.py` exited with status `2` and printed:
    `teorema-fundamental-curvas.py: error: o argumento de curvatura κ(s) é obrigatório (forneça posicionalmente ou via -k/--curvatura).`
  * Unrecognized argument: `python3 teorema-fundamental-curvas.py "1" "2" "extra_arg"` exited with status `2`.
  * Type error: `python3 teorema-fundamental-curvas.py "1" -n "abc"` exited with status `2`.
  * Mixed flag and positional: `python3 teorema-fundamental-curvas.py -k "1" "2"` yielded `curvatura=1, torcao=2`.

### 1.3 Exit Codes Observation
In `teorema-fundamental-curvas.py`:
- Lines 180-192: Interval validation (`s0 >= s1`) and discretization validation (`num_pontos < 2`) write to `sys.stderr` and return code `1`.
  * Live test `python3 teorema-fundamental-curvas.py "1" -i 5 2`: printed `Erro de validação: início do intervalo s0 (5.0) deve ser estritamente menor que o fim s1 (2.0).` and returned code `1`.
  * Live test `python3 teorema-fundamental-curvas.py "1" -n 1`: printed `Erro de validação: o número de pontos (1) deve ser no mínimo 2.` and returned code `1`.
- Lines 195-209: Mathematical domain and reconstruction errors:
  * Negative curvature `python3 teorema-fundamental-curvas.py "-1" "0"`: printed `Erro na reconstrução da curva: Curvature kappa(s) must be non-negative everywhere on the interval.` and returned code `1`.
  * Singularity `python3 teorema-fundamental-curvas.py "1/s" "0" -i 0 1`: returned code `1`.
  * Malformed expression `python3 teorema-fundamental-curvas.py "sin(" "0"`: returned code `1`.
  * Malicious AST injection `python3 teorema-fundamental-curvas.py "__import__('os').system('ls')" "0"`: returned code `1`.
- Successful runs: returned code `0`.

### 1.4 Automatic Sanitized Filename Generation Observation
In `curva_engine.py` (lines 625-640) and `teorema-fundamental-curvas.py` (lines 211-220):
- Filename format: `<identificacao_da_curva>-k<curvatura>-t<torcao>-I<Inicio_Fim>.html`.
- Acceptance command 1:
  ```bash
  python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28
  ```
  Generated: `helice_circular-k1-t1-I0_6.28.html` (1.18 MB HTML file with full Plotly apparatus and HUD).
- Acceptance command 2:
  ```bash
  python3 teorema-fundamental-curvas.py "1" -i 0 6.28
  ```
  Generated: `circulo-k1-t0-I0_6.28.html` (960 KB HTML file).
- Operator sanitization:
  `curva_engine.generate_output_filename('curva_plana', '1/(s+1)', 's**2', 0.0, 2.0)` produced:
  `curva_plana-k1_div_s_plus_1-ts_pow_2-I0_2.html`.

### 1.5 Pipeline Integration Observation
- `run_pipeline` in `teorema-fundamental-curvas.py` orchestrates the mathematical solve via `curva_engine.reconstruct_curve`, selects automatic or custom filename, exports responsive 3D WebGL HTML via `curva_viz.export_interactive_html`, and formats a clear summary terminal banner.
- Custom output paths with nested subdirectories (e.g. `/tmp/test_nested_dir/sub/test.html`) automatically create missing parent directories and write valid output.

---

## 2. Logic Chain

1. **Requirement Check: CLI argument parsing & defaults**
   - The CLI interface requires `curvatura` (mandatory positional or `-k`), `torcao` (optional, default `"0"`), `--intervalo`/`-i` (default `[0.0, 6.28]`), `--num-pontos`/`-n` (default `500`), and `--output`/`-o` (default automatic filename).
   - Observed in `build_argument_parser()` and `parse_arguments()` that all argument definitions, types, defaults, and resolution mechanics are implemented according to contract.
   - Conclusion: CLI interface strictly satisfies R2.

2. **Requirement Check: Exit code compliance**
   - Syntax and parser errors trigger `argparse.error()`, which exits with POSIX standard code `2`.
   - Domain errors, mathematical singularities, negative curvature, inverted intervals, and point count $< 2$ return code `1` via `sys.stderr` error reporting.
   - Successful runs complete the pipeline and exit with code `0`.
   - Conclusion: Exit codes strictly adhere to specification.

3. **Requirement Check: Filename generation & sanitization**
   - Filename generation adheres to `<identificacao_da_curva>-k<curvatura>-t<torcao>-I<Inicio_Fim>.html`.
   - Acceptance criteria benchmarks for helix and circle produced the exact filenames `helice_circular-k1-t1-I0_6.28.html` and `circulo-k1-t0-I0_6.28.html`.
   - Operator sanitization prevents illegal filesystem characters while keeping expressions intelligible.
   - Conclusion: Filename generation strictly satisfies R2.

4. **Requirement Check: Pipeline integration & visualization output**
   - The CLI seamlessly integrates `curva_engine` and `curva_viz`.
   - Generated files open into responsive 100vw $\times$ 100vh Plotly canvases with the complete 10-trace Frenet apparatus, dynamic HUD card, parameter scrubbing, and `plotly_click` curve snapping.
   - Conclusion: Pipeline integration satisfies R1, R2, and R3.

5. **Integrity & Test Suite Verification**
   - All 64 tests pass across all 4 tiers without skipping or modifying assertion thresholds.
   - Code inspection reveals authentic mathematical differential equation integration and genuine visualization routines.
   - Conclusion: Implementation is sound, free of facades, and fully verified.

---

## 3. Caveats

- **No caveats.** Every aspect of the CLI, argument parser, default values, filename sanitizer, exit codes, and test suite was independently tested and verified.

---

## 4. Conclusion

The Milestone M3 CLI implementation in `teorema-fundamental-curvas.py` is robust, clean, complete, and completely complies with the user specification and technical requirements. All 64 automated tests pass cleanly.

**Final Verdict**: **APPROVE**.

---

## 5. Verification Method

To independently reproduce this verification:

1. Run the test suite:
   ```bash
   python3 -m pytest tests/test_teorema_fundamental.py -v
   ```
   *Expected outcome*: 64 passed, 0 failed.

2. Verify CLI defaults and acceptance filenames:
   ```bash
   python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28
   # Check file creation:
   ls -la helice_circular-k1-t1-I0_6.28.html

   python3 teorema-fundamental-curvas.py "1" -i 0 6.28
   # Check file creation:
   ls -la circulo-k1-t0-I0_6.28.html
   ```

3. Verify exit codes:
   ```bash
   # Syntax error -> exit code 2
   python3 teorema-fundamental-curvas.py; echo "Exit code: $?"

   # Domain/validation error -> exit code 1
   python3 teorema-fundamental-curvas.py "1" -i 5 2; echo "Exit code: $?"
   python3 teorema-fundamental-curvas.py "-1" "0"; echo "Exit code: $?"

   # Success -> exit code 0
   python3 teorema-fundamental-curvas.py "1" "1" -o test.html; echo "Exit code: $?"
   ```

*Invalidation conditions*: Any test failure in `pytest`, any exit code divergence from the contract (0 on success, 1 on math/domain error, 2 on syntax/argparse error), or filename divergence from the specified template.
