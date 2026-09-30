# Handoff Report: Challenger M4-1 (Adversarial Verification)

**Verdict**: **REQUEST_CHANGES**
**Overall Risk Assessment**: **CRITICAL**

---

## 1. Observation

### Observation 1.1: Arbitrary Code Execution (RCE) via `-i` / `--intervalo` Parameter
- **Location**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/teorema-fundamental-curvas.py`, lines 54–66:
```python
def _parse_interval_bound(val: str) -> float:
    """Safely parse an interval bound as float or symbolic constant (e.g., 'pi', '2*pi')."""
    try:
        return float(val)
    except ValueError:
        try:
            parsed = sp.sympify(val, locals={"pi": sp.pi, "e": sp.E, "E": sp.E})
            return float(parsed.evalf())
        except Exception as e:
            raise argparse.ArgumentTypeError(
                f"Valor de intervalo inválido '{val}': deve ser numérico ou constante válida."
            ) from e
```
- **Execution Command & Empirical Proof**:
```bash
python3 teorema-fundamental-curvas.py "1" "0" -i 0 "__import__('pathlib').Path('pwned.txt').touch()"
```
- **Result**: `pwned.txt` was created on disk in the working directory before argparse returned exit code 2.
- **Automated Test**: `tests/test_adversarial_m4.py::TestExpressionSecurity::test_interval_bound_security_injection` fails with:
```
FAILED tests/test_adversarial_m4.py::TestExpressionSecurity::test_interval_bound_security_injection - AssertionError: CRITICAL: Arbitrary code execution occurred via -i argument parsing!
```

### Observation 1.2: Adaptive ODE Solver Hang on Non-Sampled Interior Singularities
- **Location**: `/Users/gabrielribeiro/Repositórios/Teorema-Fundamental-de-Curvas/curva_engine.py`, lines 497–505 and 539–548:
  The domain check evaluates finiteness only on the discrete points:
  ```python
  s_vals = np.linspace(s0_f, s1_f, int(num_points))
  kappa_vals = kappa_eval(s_vals)
  tau_vals = tau_eval(s_vals)
  if not np.all(np.isfinite(kappa_vals)) or not np.all(np.isfinite(tau_vals)):
      raise ValueError(...)
  ```
- **Execution Command**:
```bash
python3 teorema-fundamental-curvas.py "1/(s - 2)^2" "0" -i 0 4 -n 500
```
- **Result**: Because $s = 2.0$ falls strictly between grid points ($s_k \approx 1.996$ and $s_{k+1} \approx 2.004$), the finite check passes. During `solve_ivp` integration with `DOP853`, adaptive step reduction causes the process to loop indefinitely ($h \to 0$), hanging execution until killed (ran for >6 minutes before manual termination).

### Observation 1.3: Robust Handling of Textbook Families and Geometric Limits
The following empirical tests in `tests/test_adversarial_m4.py` passed with 100% compliance:
- Extremely small interval: `-i 0 0.001 -n 10` -> Exit code 0, valid HTML.
- High resolution: `-n 2000` -> Exit code 0, valid HTML.
- Zero curvature ($\kappa = 0, \tau = 0$): Classified as `reta`, osculating circle suppressed cleanly without division by zero.
- Straight line with torsion ($\kappa = 0, \tau = 1$): Classified as `reta`, trajectory along x-axis $[s, 0, 0]$, orthonormal moving frame preserved.
- General cylindrical helix (Lancret's Theorem $\tau/\kappa = \text{const}$): Expressions like $\kappa=2+\cos(s), \tau=4+2\cos(s)$ and $\kappa=1+s^2, \tau=3(1+s^2)$ correctly classified as `helice_cilindrica_geral`.
- Clothoid ($\kappa = s, \tau = 0$ and $\kappa = 2s+1, \tau=0$): Correctly classified as `espiral_de_cornu`.
- Negative curvature rejection ($\kappa = -1$, $\kappa = s - 2$, $\kappa = \cos(s)$): Exits with code 1 and user-friendly error without uncaught exceptions.
- Malicious expressions in $\kappa(s)$ and $\tau(s)$ (`__import__`, `open`, `eval`, `exec`, `lambda`, `.__class__`): Blocked by AST whitelist parser in `curva_engine.py`, exit code 1.
- Argparse syntax errors (missing curvature, extra positionals, unrecognized flags, malformed interval): Exit code 2 with standard usage diagnostics.

---

## 2. Logic Chain

1. **Premise 1**: The system must be secure against arbitrary code execution when parsing user input.
2. **Premise 2**: In `teorema-fundamental-curvas.py`, `_parse_interval_bound` passes untrusted user strings to SymPy's `sp.sympify(val)`.
3. **Premise 3**: In SymPy, `sp.sympify(val)` evaluates strings via Python's `eval()` unless restricted by AST validation.
4. **Premise 4**: An attacker or untrusted user supplying `-i 0 "__import__('os').system('...')"` achieves arbitrary remote code execution on the host system.
5. **Inference 1**: Despite strong AST whitelist protection inside `curva_engine.py` for $\kappa$ and $\tau$, the CLI input parsing layer introduced a critical remote code execution backdoor in the interval argument parsing.
6. **Premise 5**: In `curva_engine.py`, domain validation checks $\kappa(s)$ and $\tau(s)$ only on the $N$ user-specified discretization nodes.
7. **Inference 2**: When an expression contains an interior pole that does not coincide with a sampled node, `solve_ivp` suffers step-size collapse and hangs indefinitely.
8. **Conclusion**: The codebase cannot be approved for Milestone M4 completion until the Critical RCE vulnerability is mitigated.

---

## 3. Caveats

- The AST whitelist in `curva_engine.py` for curvature and torsion expressions is solid and successfully blocked all 8 injection vectors tested. The vulnerability exists strictly in `teorema-fundamental-curvas.py`'s interval helper function `_parse_interval_bound`.
- For the ODE solver hang, this only occurs when an interior pole is placed precisely between grid points and the function remains positive on all sampled grid points.

---

## 4. Conclusion & Required Changes

**Verdict**: **REQUEST_CHANGES**

### Actionable Remediation Required:

1. **Fix Critical RCE in `teorema-fundamental-curvas.py`**:
   Replace the dangerous `sp.sympify(val)` call in `_parse_interval_bound` with safe parsing using `curva_engine.parse_and_validate_expression` or pure float conversion, ensuring no free symbols other than constants (`pi`, `e`) are permitted:
   ```python
   def _parse_interval_bound(val: str) -> float:
       """Safely parse an interval bound as float or symbolic constant (e.g., 'pi', '2*pi')."""
       try:
           return float(val)
       except ValueError:
           try:
               expr = curva_engine.parse_and_validate_expression(val)
               if expr.free_symbols - {sp.Symbol("pi"), sp.Symbol("e"), sp.Symbol("E")}:
                   raise ValueError("Interval bound cannot contain variable 's'.")
               val_eval = float(expr.evalf())
               if not np.isfinite(val_eval):
                   raise ValueError("Interval bound evaluated to non-finite value.")
               return val_eval
           except Exception as e:
               raise argparse.ArgumentTypeError(
                   f"Valor de intervalo inválido '{val}': deve ser numérico ou constante válida."
               ) from e
   ```

2. **Add Dense Pole Pre-check or Solver Step Safeguard in `curva_engine.py`**:
   Sample $\kappa(s)$ and $\tau(s)$ over a dense grid (e.g., 2000 points) or configure `max_step` / catch integration step failures gracefully to prevent infinite loops on unaligned interior poles.

3. **Verify All Tests Pass**:
   Ensure `pytest tests/test_adversarial_m4.py` passes cleanly (26/26).

---

## 5. Verification Method

To verify the vulnerability and its remediation:

```bash
# 1. Reproduce the Critical RCE vulnerability:
pytest -v tests/test_adversarial_m4.py -k test_interval_bound_security_injection

# 2. Run the complete adversarial test suite:
pytest -v tests/test_adversarial_m4.py

# 3. Run the full repository test suite:
pytest -v
```
Invalidation condition: If `test_interval_bound_security_injection` passes without executing code when the vulnerability is patched, the finding is resolved.
