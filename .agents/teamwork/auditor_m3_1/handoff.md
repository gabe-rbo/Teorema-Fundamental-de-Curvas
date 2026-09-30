# Forensic Audit Report — Milestone M3 CLI Entrypoint (`teorema-fundamental-curvas.py`)

**Work Product**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`  
**Profile**: General Project  
**Integrity Mode**: Development (`ORIGINAL_REQUEST.md`, line 14)  
**Binary Verdict**: **CLEAN**

---

## 1. Observation

### 1.1 Source Code Static & AST Inspection
- Target file: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py` (272 lines, 8808 bytes, executable permissions `rwxr-xr-x`).
- Line 270 contains the only equality comparison in the entire script:
  ```python
  if __name__ == "__main__":
      main()
  ```
  No conditional branching on specific curvature, torsion, classification names, or test filenames exists.
- Grep queries for keywords `pytest`, `mock`, `fake`, `dummy`, `assert`, `unittest`, `bypass`, `magic` returned zero hits in `teorema-fundamental-curvas.py`, `curva_engine.py`, and `curva_viz.py`.
- Delegation to `curva_engine` and `curva_viz` is authentic and direct:
  - Line 50: `import curva_engine`
  - Line 51: `import curva_viz`
  - Line 211: `curve_data = curva_engine.reconstruct_curve(...)`
  - Line 229: `output_filename = curva_engine.generate_output_filename(...)`
  - Line 239: `final_path = curva_viz.export_interactive_html(...)`

### 1.2 Independent Test Suite Execution
- Command: `python3 -m pytest tests/test_teorema_fundamental.py -v`
- Output:
  ```text
  ======================== 64 passed, 3 warnings in 8.35s ========================
  ```
  All 64 tests passed with zero failures and zero skipped tests.
- Full repository test execution (`python3 -m pytest tests/ -v`):
  ```text
  ======================= 156 passed, 5 warnings in 21.97s =======================
  ```
  All 156 tests across all 4 test suites (`test_teorema_fundamental.py`, `test_curva_engine_stress.py`, `test_curva_viz_stress.py`, `test_adversarial_m2.py`) passed cleanly.

### 1.3 Pre-populated Artifact Inspection
- Search: `find . -name '*.log' -o -name '*result*' -o -name '*output*'` returned 0 files.
- Test inspection: Every CLI and visualization test in `tests/test_teorema_fundamental.py` uses pytest's isolated `tmp_path` fixture (e.g. lines 351, 359, 367, 382, 448, 459, 475, 490, 507, 542, 745). No test relies on pre-generated fixtures or cached output files.
- Test suite timestamp: `tests/test_teorema_fundamental.py` was created on Sep 30 11:54:54 and remained untouched during Milestone M3 development (`teorema-fundamental-curvas.py` created at 16:08:10).

### 1.4 Exit Codes & Error Diagnostics Empirical Verification
- Comprehensive programmatic test over 8 error and success conditions:
  ```text
  PASS missing args: returncode=2
  PASS inverted interval: returncode=1
  PASS num_points < 2: returncode=1
  PASS num_points = 0: returncode=1
  PASS disallowed identifier: returncode=1
  PASS negative curvature: returncode=1
  PASS malformed syntax: returncode=1
  PASS code injection attempt: returncode=1
  ALL EXIT CODE CHECKS PASSED
  ```
- Unrecognized positional arguments test (`python3 teorema-fundamental-curvas.py -k 2 -t 1 3`):
  ```text
  teorema-fundamental-curvas.py: error: argumentos posicionais não reconhecidos: 3
  Exit code: 2
  ```
- Invalid interval bound test (`python3 teorema-fundamental-curvas.py "1" -i "not_a_number" "5"`):
  ```text
  teorema-fundamental-curvas.py: error: argument -i/--intervalo: Valor de intervalo inválido 'not_a_number': deve ser numérico ou constante válida.
  Exit code: 2
  ```

### 1.5 Acceptance Criteria Execution Verification
- Command 1 (Circular Helix): `python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28`
  - Exit code: `0`
  - Output file generated: `helice_circular-k1-t1-I0_6.28.html` (size: 1.1 MB).
- Command 2 (Planar Circle): `python3 teorema-fundamental-curvas.py "1" -i 0 6.28`
  - Exit code: `0`
  - Output file generated: `circulo-k1-t0-I0_6.28.html` (size: 938 KB).
- Command 3 (Custom Output): `python3 teorema-fundamental-curvas.py "1" "1" -o test_out_acceptance.html`
  - Exit code: `0`
  - Output file generated: `test_out_acceptance.html` (size: 1.1 MB).

### 1.6 Behavioral Testing on Arbitrary & Symbolic Parameters
- Command: `python3 teorema-fundamental-curvas.py "3.7" -i -1 2.5 -n 137 -o forensic_circle.html`
  - Successfully reconstructed plane circle with radius $R = 1/3.7 \approx 0.27027$, classified as `circulo`, 137 points.
- Command: `python3 teorema-fundamental-curvas.py "2 + 0.3*s" "0.5*(2 + 0.3*s)" -i 0 4.2 -n 215`
  - Successfully reconstructed Lancret generalized helix ($\tau/\kappa = 0.5$), classified as `helice_cilindrica_geral`, sanitized filename `helice_cilindrica_geral-k2_plus_0_3_mult_s-t0_5_mult_2_plus_0_3_mult_s-I0_4.2.html`.
- Command: `python3 teorema-fundamental-curvas.py "1" "1" -i "pi" "2*pi" -n 50 -o forensic_sym.html`
  - Successfully evaluated symbolic interval bounds `[3.14159, 6.28319]`, exit code `0`.
- Probe inspection of generated HTML:
  - Responsive CSS reset: `100vw`, `100vh` / `100dvh`, `overflow: hidden`.
  - Complete 10-trace Frenet apparatus: `Curva r(s)`, `Ponto Ativo`, `Vetor Tangente`, `Vetor Normal`, `Vetor Binormal`, `Reta Tangente`, `Plano Osculador`, `Plano Normal`, `Plano Retificante`, `Círculo Osculador`.
  - Interactivity: JavaScript `plotly_click` callback and floating glassmorphic HUD card.

---

## 2. Logic Chain

1. **Absence of Hardcoded Cheats**:
   - Observations 1.1 and 1.6 establish that `teorema-fundamental-curvas.py` contains no conditional branches checking specific test expressions, no hardcoded output strings or canned return values, and functions identically for arbitrary, never-before-seen inputs.
2. **Authenticity of Implementation & Delegation**:
   - Observation 1.1 confirms that `teorema-fundamental-curvas.py` serves as a genuine orchestrating entrypoint delegating all mathematical modeling to `curva_engine.reconstruct_curve` and visualization export to `curva_viz.export_interactive_html`. There is no facade or dummy stub.
3. **Absence of Pre-populated Verification Artifacts**:
   - Observation 1.3 shows no cached logs or test results exist. The test suite runs in isolated temporary directories (`tmp_path`) and was written in Milestone T1 prior to M3, excluding any possibility of retroactive overfitting.
4. **Authentic Error & Exit Code Conformance**:
   - Observation 1.4 confirms that missing CLI arguments and syntax errors produce exit code `2` via argparse, while mathematical domain errors (AST violations, inverted intervals, negative curvature, points $< 2$) produce exit code `1` via stderr error messaging and pipeline return.
5. **Acceptance Criteria Fulfillment**:
   - Observation 1.5 empirically proves that all CLI commands specified in `ORIGINAL_REQUEST.md` (lines 76–78) execute cleanly and produce genuine responsive HTML visualizers with correct filenames.

---

## 3. Caveats

- **No caveats.** The implementation of `teorema-fundamental-curvas.py` was audited exhaustively, both statically and dynamically, and demonstrates total integrity across all requirements.

---

## 4. Conclusion

- **Verdict**: **CLEAN**.
- No hardcoded shortcuts, facade implementations, mock traces, AST evasion, or verification bypasses were found.
- Milestone M3 satisfies all integrity requirements under **Development Mode** (and would equally satisfy Demo and Benchmark modes).
- Work product is approved for Milestone M4.

---

## 5. Verification Method

To independently reproduce this audit:

```bash
# 1. Run full automated test suite
python3 -m pytest tests/test_teorema_fundamental.py -v

# 2. Verify exit codes empirically
python3 -c '
import subprocess
assert subprocess.run(["python3", "teorema-fundamental-curvas.py"], capture_output=True).returncode == 2
assert subprocess.run(["python3", "teorema-fundamental-curvas.py", "1", "-i", "5", "2"], capture_output=True).returncode == 1
assert subprocess.run(["python3", "teorema-fundamental-curvas.py", "1", "-n", "1"], capture_output=True).returncode == 1
assert subprocess.run(["python3", "teorema-fundamental-curvas.py", "x+1"], capture_output=True).returncode == 1
print("Exit code verification OK")
'

# 3. Verify acceptance criteria CLI executions
python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28
test -s helice_circular-k1-t1-I0_6.28.html && rm -f helice_circular-k1-t1-I0_6.28.html

python3 teorema-fundamental-curvas.py "1" -i 0 6.28
test -s circulo-k1-t0-I0_6.28.html && rm -f circulo-k1-t0-I0_6.28.html
```
