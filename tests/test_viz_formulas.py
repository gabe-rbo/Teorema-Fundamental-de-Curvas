"""The generated viewer shows solved integrals with the user's kappa and tau substituted."""
import curva_engine as ce
import curva_viz as cv


def formulas(k, t, planar, s1=4.0):
    res = ce.reconstruct_curve(k, t, s0=0.0, s1=s1, num_points=80)
    return cv._build_curve_formulas(res, planar)


def test_spatial_curve_shows_solved_integrals_of_kappa_and_tau():
    f = formulas("2+sin(3*s)", "1+0.5*cos(5*s)", False)
    assert r"\int_{0}^{s} \kappa(u)\,du = 2 s - \frac{\cos{\left(3 s \right)}}{3} + \frac{1}{3}" in f["curve_aux"]
    assert r"\int_{0}^{s} \tau(u)\,du = s + \frac{\sin{\left(5 s \right)}}{10}" in f["curve_aux"]
    assert r"T'(s) = \left(\sin{\left(3 s \right)} + 2\right)\,N(s)" == f["vec_t"]
    assert "\\kappa(s)" not in f["vec_t"] + f["vec_n"] + f["vec_b"]


def test_planar_curve_has_explicit_theta_in_T_N_and_r():
    f = formulas("2+sin(3*s)", "0", True)
    th = r"2 s - \frac{\cos{\left(3 s \right)}}{3} + \frac{1}{3}"
    assert th in f["vec_t"] and th in f["vec_n"] and th in f["curve_aux"]
    assert r"\theta(s)" not in f["vec_t"]
    assert r"2 u - \frac{\cos{\left(3 u \right)}}{3} + \frac{1}{3}" in f["curve_r"]


def test_clothoid_with_negative_slope_and_helix_are_exact():
    f = formulas("4-s", "0", True)
    assert "-\\left[ S" in f["curve_r"] and r"\sqrt{\pi}" in f["curve_r"]
    h = formulas("1", "1", False)
    assert r"\sqrt{2}" in h["vec_t"] and r"\omega" in h["curve_aux"]
    assert "." not in h["vec_t"].replace("\\left", "")


def test_evolute_has_no_stray_plus_minus():
    for k in ("4-s", "1/(2*s+3)", "1+s"):
        f = formulas(k, "0", True)
        assert "+ -" not in f["evolute"] and "+  " not in f["evolute"]
