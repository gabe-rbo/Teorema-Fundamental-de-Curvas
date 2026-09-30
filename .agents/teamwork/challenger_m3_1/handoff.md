# Adversarial Challenge & Stress Verification Report — Milestone M3

**Target Under Test**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`  
**Challenger**: `challenger_m3_1` (Roles: `critic`, `specialist`)  
**Date**: 2026-09-30T19:16:00Z  
**Verdict**: **REQUEST_CHANGES** (Severity: Low / Minor syntax validation defect)

---

## 1. Observation

Direct empirical tests were executed against `teorema-fundamental-curvas.py` and the test suite:

### 1.1 Automated Test Suite Execution
- **Command**: `python3 -m pytest tests/test_teorema_fundamental.py -v`
- **Result**: `64 passed, 3 warnings in 14.57s` (Exit code: 0).
- All Tiers (Tier 1 Feature Coverage, Tier 2 Boundary/Corner Cases, Tier 3 Cross-Feature, Tier 4 Analytical Acceptance Benchmarks) passed cleanly.

### 1.2 Dispatch Criteria Stress Scenarios

1. **Inverted Interval**:
   - **Command**: `python3 teorema-fundamental-curvas.py "1" "1" -i 10 2`
   - **Exit Code**: `1`
   - **Stderr**:
     ```
     Erro de validação: início do intervalo s0 (10.0) deve ser estritamente menor que o fim s1 (2.0).
     ```

2. **Equal Interval**:
   - **Command**: `python3 teorema-fundamental-curvas.py "1" "1" -i 5 5`
   - **Exit Code**: `1`
   - **Stderr**:
     ```
     Erro de validação: início do intervalo s0 (5.0) deve ser estritamente menor que o fim s1 (5.0).
     ```

3. **Discretization Point Boundaries**:
   - **Command**: `python3 teorema-fundamental-curvas.py "1" "0" -n 2 -o /tmp/test_n2.html`
     - **Exit Code**: `0`
     - **Result**: Successfully created HTML file `/tmp/test_n2.html`.
   - **Command**: `python3 teorema-fundamental-curvas.py "1" "0" -n 1`
     - **Exit Code**: `1`
     - **Stderr**:
       ```
       Erro de validação: o número de pontos (1) deve ser no mínimo 2.
       ```
   - **Commands**: `-n 0`, `-n -5` both exited with code `1` and identical validation error.

4. **Invalid Math Syntax**:
   - **Command**: `python3 teorema-fundamental-curvas.py "1++s"`
     - **Exit Code**: `0` (FAIL vs. Dispatch Requirement `15: - Invalid math syntax: "1++s" -> non-zero exit code`)
     - **Stdout**: Reconstructed curve classified as `espiral_de_cornu`, generating HTML file `espiral_de_cornu-k1_plus_plus_s-t0-I0_6.28.html`.
   - **Commands for other malformed operators**:
     - `python3 teorema-fundamental-curvas.py "1+*s"` -> Exit code `1`:
       `Erro na reconstrução da curva: Syntax error in expression '1+*s': invalid syntax`
     - `python3 teorema-fundamental-curvas.py "2*+*3"` -> Exit code `1`:
       `Erro na reconstrução da curva: Syntax error in expression '2*+*3': invalid syntax`
     - `python3 teorema-fundamental-curvas.py "sin("` -> Exit code `1`:
       `Erro na reconstrução da curva: Syntax error in expression 'sin(': unexpected EOF while parsing`
     - `python3 teorema-fundamental-curvas.py "s @ 2"` -> Exit code `1`:
       `Erro na reconstrução da curva: Disallowed syntax element 'MatMult' in expression 's @ 2'.`
     - `python3 teorema-fundamental-curvas.py "1//s"` -> Exit code `1`:
       `Erro na reconstrução da curva: Disallowed syntax element 'FloorDiv' in expression '1//s'.`

5. **Code Injection & Disallowed Identifiers**:
   - **Command**: `python3 teorema-fundamental-curvas.py "__import__('os').system('echo hacked')"`
     - **Exit Code**: `1`
     - **Stderr**: `Erro na reconstrução da curva: Disallowed function call '__import__' in expression ...`
     - **Verification**: `hacked` was NOT printed to stdout.
   - **Command**: `python3 teorema-fundamental-curvas.py "(1).__class__.__bases__"`
     - **Exit Code**: `1`
     - **Stderr**: `Erro na reconstrução da curva: Disallowed syntax element 'Attribute' ...`
   - **Command**: `python3 teorema-fundamental-curvas.py "x + 1"`
     - **Exit Code**: `1`
     - **Stderr**: `Erro na reconstrução da curva: Disallowed variable name 'x' ...`

6. **Custom Output in Nested Subdirectories**:
   - **Command**: `python3 teorema-fundamental-curvas.py "1" "1" -o /tmp/custom_test_dir/subdir/test_curve.html`
   - **Exit Code**: `0`
   - **Verification**: Directory `/tmp/custom_test_dir/subdir` was created automatically and `test_curve.html` (size > 1 MB) was written.

7. **Acceptance Scenario 1 (Circular Helix)**:
   - **Command**: `python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28`
   - **Exit Code**: `0`
   - **Artifact Created**: `helice_circular-k1-t1-I0_6.28.html` (size: 1,188,626 bytes)
   - **HTML Content Inspected**: Confirmed `100vw`, `100vh`, `100dvh`, `overflow: hidden`, `hud-card`, `plotly_click`, and 10 differential apparatus traces.

8. **Acceptance Scenario 2 (Planar Circle)**:
   - **Command**: `python3 teorema-fundamental-curvas.py "1" -i 0 6.28`
   - **Exit Code**: `0`
   - **Artifact Created**: `circulo-k1-t0-I0_6.28.html` (size: 960,360 bytes)
   - **Classification**: `circulo` (planar Diedro view).

---

## 2. Logic Chain

1. **Premise 1**: The orchestrator's dispatch instructions explicitly stated in objective 1:
   `- Invalid math syntax: "1++s" -> non-zero exit code.`
2. **Premise 2**: In `curva_engine.py` (lines 45-60), `_ALLOWED_AST_NODES` includes `ast.UnaryOp` and `ast.UAdd`. Python's grammar interprets `1++s` as `1 + (+s)`, which creates an AST containing `BinOp(Constant(1), Add(), UnaryOp(UAdd(), Name('s')))`.
3. **Premise 3**: Because all nodes in `1++s` match the whitelist, `curva_engine.parse_and_validate_expression("1++s")` succeeds and returns SymPy expression `s + 1`.
4. **Premise 4**: Consequently, `python3 teorema-fundamental-curvas.py "1++s"` executes the full pipeline without error, classifies the curve as `espiral_de_cornu`, exports an HTML file, and exits with return code `0`.
5. **Premise 5**: While mathematically equivalent to $s + 1$ under Python's unary plus grammar, in general mathematical notation `1++s` is considered invalid syntax (consecutive operator characters without operand), directly contradicting the dispatch criteria.
6. **Conclusion**: The implementation is exceptionally robust across 17 of 18 test dimensions, but fails the specific dispatch acceptance requirement for `"1++s"`.

---

## 3. Caveats

- **Python Grammar vs. Mathematical Syntax**: Python and SymPy natively allow arbitrary chains of unary operators (e.g., `1 + + + s` or `1 - - s`). If the project design explicitly intended to permit Python unary operator chaining, the dispatch test specification can be relaxed to test operators that truly violate grammar such as `"1+*s"`, `"1*/s"`, or `"2*+*3"`, all of which currently exit with code 1.
- **Scope of Fix**: If consecutive operators should be rejected, the fix requires a minor 2-line check in `curva_engine.py` (e.g. In `_preprocess_math_string` or `parse_and_validate_expression`: `if re.search(r'\+{2,}|-{2,}', expr_str): raise ValueError("Consecutive operators not allowed")`).

---

## 4. Conclusion

- **Verdict**: **REQUEST_CHANGES** (Minor)
- **Defect Summary**: `teorema-fundamental-curvas.py "1++s"` exits with code `0` instead of a non-zero exit code because consecutive unary pluses are accepted by `ast.parse` and `ast.UAdd`.
- **Recommended Action**:
  - Add consecutive operator syntax rejection in `curva_engine.py:parse_and_validate_expression` or `_preprocess_math_string`:
    ```python
    if re.search(r'(\+{2,}|-{2,})', expr_str):
        raise ValueError(f"Syntax error in expression '{expr_str}': consecutive operators are not permitted.")
    ```
  - Alternatively, if the orchestrator and team consider `1++s` valid Python unary syntax, the orchestrator may approve this as intended behavior and proceed to M4.

---

## 5. Verification Method

To independently verify the finding and the rest of the test suite:

1. **Verify the defect**:
   ```bash
   python3 teorema-fundamental-curvas.py "1++s"
   echo "Exit code: $?"
   # Currently prints exit code: 0, expected non-zero
   ```

2. **Verify other syntax rejections**:
   ```bash
   python3 teorema-fundamental-curvas.py "1+*s"
   echo "Exit code: $?"  # 1
   ```

3. **Verify the full automated test suite**:
   ```bash
   python3 -m pytest tests/test_teorema_fundamental.py -v
   # All 64 tests pass in ~15s
   ```

4. **Verify acceptance criteria commands**:
   ```bash
   python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28
   python3 teorema-fundamental-curvas.py "1" -i 0 6.28
   ls -la helice_circular-k1-t1-I0_6.28.html circulo-k1-t0-I0_6.28.html
   ```
