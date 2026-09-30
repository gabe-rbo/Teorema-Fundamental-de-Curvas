# Milestone M3 Final Challenge Report — CLI Interface

**Target**: `teorema-fundamental-curvas.py`  
**Challenger Archetype**: `teamwork_preview_challenger`  
**Verdict**: **APPROVE**  
**Overall Risk Assessment**: **LOW**

---

## 1. Challenge Summary

An exhaustive empirical evaluation of `teorema-fundamental-curvas.py` was conducted across 31 individual test executions covering:
- **Baseline Acceptance Tests** (helix, circle, custom output path).
- **CLI Flag Variations & Parameter Harmonies** (positional vs. flagged arguments, explicit overrides).
- **Geometric Classification Verification** via CLI (`reta`, `circulo`, `helice_circular`, `helice_cilindrica_geral`, `espiral_de_cornu`, `espiral_logaritmica`).
- **Domain & Validation Error Handling (Exit Code 1)**: inverted intervals, equal bounds, insufficient points ($N < 2$), invalid mathematical syntax, unauthorized AST nodes, division by zero, non-positive curvature.
- **CLI Syntax & Argument Parser Handling (Exit Code 2)**: missing required parameters, extra positional arguments, unknown flags, non-numeric values.
- **Generated Visualization Integrity**: complete HTML document structure, full viewport CSS rules (`100vw`/`100vh`), Plotly 3D apparatus, interactive slider steps, and Frenet frame traces.

All 31 empirical challenges passed unconditionally without errors or crashes.

---

## 2. 5-Component Handoff Report

### 2.1 Observation

1. **Acceptance Test 1 (Circular Helix)**:
   - Command: `python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28`
   - Exit Code: `0`
   - Stdout:
     ```text
     ================================================================================
       TEOREMA FUNDAMENTAL DE CURVAS — RECONSTRUÇÃO FRENET-SERRET
     ================================================================================
       Classificação da Curva : helice_circular
       Curvatura κ(s)         : 1
       Torção τ(s)            : 1
       Intervalo [s0, s1]     : [0, 6.28]
       Pontos Discretizados   : 500
       Arquivo HTML Gerado    : /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/helice_circular-k1-t1-I0_6.28.html
     ================================================================================
     Visualização pronta! Abra '/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/helice_circular-k1-t1-I0_6.28.html' no seu navegador.
     ```
   - Generated Artifact: `helice_circular-k1-t1-I0_6.28.html` (size: 1,188,626 bytes, valid HTML).

2. **Acceptance Test 2 (Planar Circle)**:
   - Command: `python3 teorema-fundamental-curvas.py "1" -i 0 6.28`
   - Exit Code: `0`
   - Stdout:
     ```text
     ================================================================================
       TEOREMA FUNDAMENTAL DE CURVAS — RECONSTRUÇÃO FRENET-SERRET
     ================================================================================
       Classificação da Curva : circulo
       Curvatura κ(s)         : 1
       Torção τ(s)            : 0
       Intervalo [s0, s1]     : [0, 6.28]
       Pontos Discretizados   : 500
       Arquivo HTML Gerado    : /Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/circulo-k1-t0-I0_6.28.html
     ================================================================================
     ```
   - Generated Artifact: `circulo-k1-t0-I0_6.28.html` (size: 960,360 bytes, valid HTML).

3. **Acceptance Test 3 (Custom Output)**:
   - Command: `python3 teorema-fundamental-curvas.py "1" -i 0 6.28 -o custom_out.html`
   - Exit Code: `0`
   - Generated Artifact: `custom_out.html` (size: 960,360 bytes, valid HTML).

4. **HTML Content & Structure Inspection** (`custom_out.html` and `helice_circular-k1-t1-I0_6.28.html`):
   - Document contains `<!DOCTYPE html>`, `<html>`, `<body>`.
   - Embeds Plotly.js library and canvas configuration.
   - Styling: `width: 100vw; height: 100vh; margin: 0; padding: 0; overflow: hidden;`.
   - Traces present: Trajetória da Curva $r(s)$, Vetor Tangente $\vec{T}$, Vetor Normal $\vec{N}$, Vetor Binormal $\vec{B}$, Reta Tangente, Plano Osculador, Plano Normal, Plano Retificante, Círculo Osculador.
   - Slider steps present for interactive progression along $s$.

5. **Negative Test Suite — Domain & Validation Errors (Exit Code 1)**:
   - Inverted interval `[-i 6.28 0]`: Exit code `1`, Stderr: `Erro de validação: início do intervalo s0 (6.28) deve ser estritamente menor que o fim s1 (0.0).`
   - Degenerate interval `[-i 3.14 3.14]`: Exit code `1`, Stderr: `Erro de validação: início do intervalo s0 (3.14) deve ser estritamente menor que o fim s1 (3.14).`
   - Point count below 2 (`-n 1`, `-n 0`, `-n -50`): Exit code `1`, Stderr: `Erro de validação: o número de pontos (...) deve ser no mínimo 2.`
   - Invalid syntax expression (`"1 +* 2"`): Exit code `1`, Stderr: `Erro na reconstrução da curva: Expressão inválida...`
   - Disallowed variable (`"x^2 + 1"`): Exit code `1`, Stderr: `Erro na reconstrução da curva: Identificador 'x' não permitido...`
   - Malicious injection (`"__import__('os').system('ls')"`): Exit code `1`, Stderr: `Erro na reconstrução da curva: AST node Call/Attribute disallowed...`
   - Mathematical singularity (`"1/s"` on `[0, 5]`): Exit code `1`, Stderr: `Erro na reconstrução da curva: Singularity / NaN detected in curvature expression...`
   - Negative curvature (`"-1"`): Exit code `1`, Stderr: `Erro na reconstrução da curva: Curvature kappa(s) must be non-negative everywhere on the interval.`

6. **Negative Test Suite — CLI Syntax Errors (Exit Code 2)**:
   - Missing required curvature (`python3 teorema-fundamental-curvas.py`): Exit code `2`, Stderr: `teorema-fundamental-curvas.py: error: o argumento de curvatura κ(s) é obrigatório...`
   - Extra unrecognized positional (`"1" "1" "extra"`): Exit code `2`, Stderr: `teorema-fundamental-curvas.py: error: unrecognized arguments: extra`
   - Extra positional with explicit flags (`-k 1 -t 1 extra`): Exit code `2`, Stderr: `teorema-fundamental-curvas.py: error: argumentos posicionais não reconhecidos: extra`
   - Unrecognized option (`--unsupported-flag`): Exit code `2`, Stderr: `teorema-fundamental-curvas.py: error: unrecognized arguments: --unsupported-flag`
   - Incomplete interval (`-i 0`): Exit code `2`, Stderr: `teorema-fundamental-curvas.py: error: argument -i/--intervalo: expected 2 arguments`
   - Non-numeric interval bound (`-i abc def`): Exit code `2`, Stderr: `teorema-fundamental-curvas.py: error: argument -i/--intervalo: Valor de intervalo inválido 'abc'...`
   - Non-integer num-points (`-n not_a_number`): Exit code `2`, Stderr: `teorema-fundamental-curvas.py: error: argument -n/--num-pontos: invalid int value...`

7. **Project Test Suite Status**:
   - `pytest` executed across entire test directory: `156 passed, 5 warnings in 22.74s`.

### 2.2 Logic Chain

1. **Requirement R2 Compliance**: R2 specifies that `curvatura` is mandatory, `torcao` defaults to `"0"`, `-i` accepts `[s0, s1]`, `-n` specifies points, and `-o` specifies custom path with automatic fallback naming `<identificacao_da_curva>-k<curvatura>-t<torcao>-I<InicioIntervalo_FimIntervalo>.html`.
   - Directly confirmed by Observations 1, 2, 3, 5, and 6. Both positional syntax (`"1" "1"`) and flagged syntax (`-k 1 -t 1`) are supported.
2. **Acceptance Criteria Verification**:
   - Acceptance test 1 generated `helice_circular-k1-t1-I0_6.28.html` with exit code 0.
   - Acceptance test 2 generated `circulo-k1-t0-I0_6.28.html` with exit code 0.
   - Acceptance test 3 generated `custom_out.html` with exit code 0.
3. **Exit Code Discrimination**:
   - The contract specifies exit code 0 for success, 1 for domain/runtime errors, and 2 for argument parsing syntax errors.
   - All 10 domain error tests exited with status 1.
   - All 7 argument parsing syntax tests exited with status 2.
4. **Interactive Visualization Apparatus**:
   - Generated HTML files adhere to responsive viewport styling (`100vw`, `100vh`), include the complete Frenet apparatus traces, and incorporate slider keyframes.
5. **No Regressions**:
   - Full test suite of 156 existing unit and stress tests passes cleanly.

### 2.3 Caveats

- Interactive mouse clicks in a live browser engine were not run via automated headless Chromium (e.g. Playwright), but the generated JavaScript code, Plotly JSON structures, and DOM event bindings were inspected and verified in the generated HTML.
- Arbitrary extreme point discretizations exceeding memory limits (e.g. $N > 10^7$) were not tested as default CLI operations typically operate at $N \in [100, 5000]$.

### 2.4 Conclusion

The CLI interface in `teorema-fundamental-curvas.py` fulfills all Milestone M3 requirements and acceptance criteria. It exhibits clean argument parsing, strict error code isolation, automatic curve classification, robust AST-sanitized expression parsing, and accurate interactive visualization export.

**Verdict**: **APPROVE**.

### 2.5 Verification Method

To independently verify these findings, run:

```bash
# 1. Acceptance Tests
python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28
ls -lh helice_circular-k1-t1-I0_6.28.html

python3 teorema-fundamental-curvas.py "1" -i 0 6.28
ls -lh circulo-k1-t0-I0_6.28.html

python3 teorema-fundamental-curvas.py "1" -i 0 6.28 -o custom_out.html
ls -lh custom_out.html

# 2. Domain Negative Tests (Exit Code 1)
python3 teorema-fundamental-curvas.py "1" "1" -i 10 0
echo "Exit: $?" # Should be 1

python3 teorema-fundamental-curvas.py "1" "1" -n 1
echo "Exit: $?" # Should be 1

python3 teorema-fundamental-curvas.py "-1" "0" -i 0 6.28
echo "Exit: $?" # Should be 1

# 3. CLI Syntax Negative Tests (Exit Code 2)
python3 teorema-fundamental-curvas.py
echo "Exit: $?" # Should be 2

python3 teorema-fundamental-curvas.py "1" "1" "extra"
echo "Exit: $?" # Should be 2

# 4. Entire project pytest suite
pytest
```

---

## 3. Adversarial Challenges & Stress Testing

### Challenge 1: Argument Injection & Ambiguity (Positional vs. Flagged)
- **Assumption Challenged**: Combining positional and flagged arguments or supplying superfluous positionals could cause crashes or silent misassignment.
- **Attack Scenario**: Running `python3 teorema-fundamental-curvas.py -k 1 -t 1 extra_pos` or `python3 teorema-fundamental-curvas.py "1" "1" "extra"`.
- **Result**: `argparse` correctly captures unexpected arguments and exits with status `2` (`error: unrecognized arguments` / `argumentos posicionais não reconhecidos`).
- **Blast Radius**: None. Securely handled.

### Challenge 2: Mathematical Invariants & Non-Positive Curvature
- **Assumption Challenged**: By the Frenet-Serret theorem, curvature $\kappa(s)$ must satisfy $\kappa(s) \ge 0$. Supplying negative curvature could cause unphysical or degenerate frame integration.
- **Attack Scenario**: `python3 teorema-fundamental-curvas.py "-1" "0" -i 0 6.28`.
- **Result**: `curva_engine` checks positivity across the interval and raises `ValueError`, resulting in CLI exit code `1` with message `Curvature kappa(s) must be non-negative everywhere on the interval`.
- **Blast Radius**: None. Mathematically sound.

### Challenge 3: Symbolic Constants in Interval Bounds
- **Assumption Challenged**: Users frequently pass `"2*pi"` or `"pi"` to `-i` instead of floating point decimals.
- **Attack Scenario**: `python3 teorema-fundamental-curvas.py "1" "1" -i 0 "2*pi"`.
- **Result**: Handled gracefully via `_parse_interval_bound`, which parses `sp.sympify` on known constants like `pi` and `e`. Curve evaluated over $[0, 6.28319]$ successfully (exit code 0).
- **Blast Radius**: None. Enhanced usability.

---

## 4. Comprehensive Test Execution Matrix

| Test ID | Category | Command / Invocation | Expected Exit | Actual Exit | Result |
|---|---|---|:---:|:---:|:---:|
| **ACC-01** | Acceptance | `"1" "1" -i 0 6.28` | 0 | 0 | **PASS** |
| **ACC-02** | Acceptance | `"1" -i 0 6.28` | 0 | 0 | **PASS** |
| **ACC-03** | Acceptance | `"1" -i 0 6.28 -o custom_out.html` | 0 | 0 | **PASS** |
| **CURV-01** | Classification | `"0" "0" -i 0 5 -o test_line.html` (reta) | 0 | 0 | **PASS** |
| **CURV-02** | Classification | `"s" "0" -i 0 4 -o test_clothoid.html` (espiral_de_cornu) | 0 | 0 | **PASS** |
| **CURV-03** | Classification | `"1/(s+1)" "0" -i 0 4 -o test_log.html` (espiral_logaritmica) | 0 | 0 | **PASS** |
| **CURV-04** | Classification | `"2*s" "4*s" -i 1 4 -o test_lancret.html` (helice_cilindrica_geral) | 0 | 0 | **PASS** |
| **FLAG-01** | Flags | `-k 2 -t 1 -i 0 3 -n 200 -o test_flags.html` | 0 | 0 | **PASS** |
| **NEG-DOM-01** | Domain Error | `"1" "1" -i 6.28 0` (inverted interval) | 1 | 1 | **PASS** |
| **NEG-DOM-02** | Domain Error | `"1" "1" -i 3.14 3.14` (equal bounds) | 1 | 1 | **PASS** |
| **NEG-DOM-03** | Domain Error | `"1" "1" -n 1` ($N < 2$) | 1 | 1 | **PASS** |
| **NEG-DOM-04** | Domain Error | `"1" "1" -n 0` ($N = 0$) | 1 | 1 | **PASS** |
| **NEG-DOM-05** | Domain Error | `"1" "1" -n -50` ($N < 0$) | 1 | 1 | **PASS** |
| **NEG-DOM-06** | Domain Error | `"1 +* 2" "0"` (syntax error) | 1 | 1 | **PASS** |
| **NEG-DOM-07** | Domain Error | `"x^2 + 1" "0"` (unknown variable) | 1 | 1 | **PASS** |
| **NEG-DOM-08** | Domain Error | `"__import__('os').system('ls')"` (AST disallowed) | 1 | 1 | **PASS** |
| **NEG-DOM-09** | Domain Error | `"1/s" "0" -i 0 5` (zero division singularity) | 1 | 1 | **PASS** |
| **NEG-DOM-10** | Domain Error | `"log(s)" "0" -i -5 -1` (domain singularity) | 1 | 1 | **PASS** |
| **NEG-DOM-11** | Domain Error | `"-1" "0" -i 0 6.28` (negative curvature) | 1 | 1 | **PASS** |
| **NEG-SYN-01** | Syntax Error | *(no arguments)* | 2 | 2 | **PASS** |
| **NEG-SYN-02** | Syntax Error | `"1" "1" "extra_arg"` | 2 | 2 | **PASS** |
| **NEG-SYN-03** | Syntax Error | `-k 1 -t 1 extra_arg` | 2 | 2 | **PASS** |
| **NEG-SYN-04** | Syntax Error | `--unsupported-flag` | 2 | 2 | **PASS** |
| **NEG-SYN-05** | Syntax Error | `"1" -i 0` (incomplete interval) | 2 | 2 | **PASS** |
| **NEG-SYN-06** | Syntax Error | `"1" -i abc def` (non-numeric interval) | 2 | 2 | **PASS** |
| **NEG-SYN-07** | Syntax Error | `"1" -n not_a_number` (non-int points) | 2 | 2 | **PASS** |
| **ADV-01** | Adversarial | `"2 * s + 1" "cos(2 * pi * s)" -i 0 1` | 0 | 0 | **PASS** |
| **ADV-02** | Adversarial | `"1" "1" -i 0 "2*pi"` (symbolic bound) | 0 | 0 | **PASS** |
| **ADV-03** | Adversarial | `"1" "1" -i -10 -5` (negative interval) | 0 | 0 | **PASS** |
| **ADV-04** | Adversarial | `"s^2 + 1" "s/2" -i 0 2` (filename sanitization) | 0 | 0 | **PASS** |
| **ADV-05** | Adversarial | `"1" "1" -i 0 6.28 -n 3000` (high point count) | 0 | 0 | **PASS** |

---

## 5. Unchallenged Areas

- **Client-side GPU memory pressure**: Interactive rendering with WebGL was not benchmarked on low-end hardware devices.
- **Alternative non-POSIX shells**: Verification was performed under macOS zsh / Python 3.11 environment.
