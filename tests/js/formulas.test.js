// The algebraic formulas shown in the panel must agree with the numerical engine.
const test = require("node:test");
const assert = require("node:assert");
const path = require("path");
const Expr = require(path.join(__dirname, "../../web/js/expr.js"));
const Eng = require(path.join(__dirname, "../../web/js/engine.js"));
const F = require(path.join(__dirname, "../../web/js/formulas.js"));

const run = (k, t, s0, s1, n = 801) =>
  Eng.reconstruct({ kf: Expr.compile(Expr.parse(k)), tf: Expr.compile(Expr.parse(t)), params: [1, 1, 1], s0, s1, n, sub: 2 });
const ctxOf = (k, t, s0, s1) => {
  const ka = Expr.parse(k), ta = Expr.parse(t), d = run(k, t, s0, s1, 50);
  return { ka, ta, s0, s1, params: [1, 1, 1], planar: d.planar, label: Eng.classify(ka, ta, s0, s1, [1, 1, 1], d.planar) };
};
const blocks = (k, t, s0, s1) => F.build(ctxOf(k, t, s0, s1));
const ids = (b) => b.map((x) => x.id);
const text = (b) => b.map((x) => [x.tex, ...x.aux].join(" ")).join(" ");

// Fresnel integrals by Simpson's rule
function fres(x) {
  const n = Math.max(2000, Math.ceil(Math.abs(x) * 4000)) & ~1, h = x / n;
  let c = 0, s = 0;
  for (let i = 0; i <= n; i++) {
    const w = i === 0 || i === n ? 1 : i % 2 ? 4 : 2, th = (Math.PI * (i * h) ** 2) / 2;
    c += w * Math.cos(th); s += w * Math.sin(th);
  }
  return [(c * h) / 3, (s * h) / 3];
}
const maxDiff = (d, f) => {
  let m = 0;
  for (let i = 0; i < d.n; i++) { const [x, y] = f(d.s[i]); m = Math.max(m, Math.abs(x - d.R[3 * i]), Math.abs(y - d.R[3 * i + 1])); }
  return m;
};

test("circle closed form (also with s0 != 0) matches the engine", () => {
  const k = 1.7, s0 = 2;
  const d = run(String(k), "0", s0, 7);
  assert.ok(maxDiff(d, (s) => [Math.sin(k * (s - s0)) / k, (1 - Math.cos(k * (s - s0))) / k]) < 1e-8);
  const t = text(blocks(String(k), "0", s0, 7));
  assert.match(t, /1\.7/);
  assert.match(t, /\\sin/);
});

test("clothoid Fresnel closed form matches the engine for several (c, d, s0)", () => {
  for (const [c, dd, s0, s1] of [[1, 0, 0, 5], [2, 1, 0, 4], [0.5, 2, 1, 6], [3, 0, 0, 2.5], [-1, 4, 0, 3], [-2, 5, 0.5, 2]]) {
    const d = run(`${c}*s+${dd}`, "0", s0, s1);
    const sg = Math.sign(c), u0 = s0 + dd / c, phi = -(c * u0 * u0) / 2, a = Math.sqrt(Math.abs(c) / Math.PI), pref = Math.sqrt(Math.PI / Math.abs(c));
    const [C0, S0] = fres(a * u0);
    const err = maxDiff(d, (s) => {
      const [C1, S1] = fres(a * (s + dd / c));
      const dx = pref * (C1 - C0), dy = sg * pref * (S1 - S0);
      return [Math.cos(phi) * dx - Math.sin(phi) * dy, Math.sin(phi) * dx + Math.cos(phi) * dy];
    });
    assert.ok(err < 1e-7, `c=${c} d=${dd} s0=${s0}: ${err}`);
    const t = text(blocks(`${c}*s+${dd}`, "0", s0, s1));
    assert.match(t, /C\\!\\left/);                     // the solved integral is displayed
    assert.match(t, /\\sqrt\{[^}]*\\pi/, "pi appears symbolically, not as a decimal");
    assert.ok(!/\d\.\d{4}/.test(blocks(`${c}*s+${dd}`, "0", s0, s1)[0].tex), "no long decimals in r(s)");
    assert.ok(!/\\int_\{[^}]*\}\^\{s\} \\left\( \\cos/.test(blocks(`${c}*s+${dd}`, "0", s0, s1)[0].tex), "no unevaluated integral for r(s)");
  }
});

test("logarithmic spiral closed form matches the engine", () => {
  for (const [a, b, s0, s1] of [[1, 1, 0, 8], [0.5, 2, 1, 9], [2, 3, 0, 6]]) {
    const d = run(`1/(${a}*s+${b})`, "0", s0, s1);
    const p = 1 / a, w0 = a * s0 + b;
    const err = maxDiff(d, (s) => {
      const y = (a * s + b) / w0, th = p * Math.log(y), co = w0 / a / (1 + p * p);
      return [co * (y * (Math.cos(th) + p * Math.sin(th)) - 1), co * (y * (Math.sin(th) - p * Math.cos(th)) + p)];
    });
    assert.ok(err < 1e-7, `a=${a} b=${b} s0=${s0}: ${err}`);
    assert.match(text(blocks(`1/(${a}*s+${b})`, "0", s0, s1)), /\\ln y\(s\)/);
  }
});

test("circular helix canonical form preserves chord and axial advance", () => {
  const k = 1.3, t = 0.8, w = Math.hypot(k, t), d = run(String(k), String(t), 0, 15);
  let err = 0;
  for (let i = 0; i < d.n; i++) {
    const s = d.s[i];
    const canon = [(k / (w * w)) * (1 - Math.cos(w * s)), (k / (w * w)) * Math.sin(w * s), (t / w) * s];
    const dist = (v) => Math.hypot(v[0], v[1], v[2]);
    err = Math.max(err, Math.abs(dist(canon) - dist([d.R[3 * i], d.R[3 * i + 1], d.R[3 * i + 2]])));
  }
  assert.ok(err < 1e-8, "helix chord error " + err);
});

test("every class returns curve, frame, evolute, involute and radii blocks", () => {
  const cases = {
    "1,0": ["curve", "T", "N", "circle", "evolute", "involute", "radii"],
    "0,0": ["curve", "T", "N", "evolute", "involute", "radii"],
    "s,0": ["curve", "T", "N", "circle", "evolute", "involute", "radii"],
    "1/(s+1),0": ["curve", "T", "N", "circle", "evolute", "involute", "radii"],
    "2+sin(3*s),0": ["curve", "T", "N", "circle", "evolute", "involute", "radii"],
    "1,1": ["curve", "T", "N", "B", "plane-osc", "plane-normal", "plane-rect", "circle", "evolute", "involute", "radii"],
    "sqrt(1+s),2*sqrt(1+s)": ["curve", "T", "N", "B", "plane-osc", "plane-normal", "plane-rect", "circle", "evolute", "involute", "radii"],
    "1+sin(s),cos(s)": ["curve", "T", "N", "B", "plane-osc", "plane-normal", "plane-rect", "circle", "evolute", "involute", "radii"]
  };
  for (const [key, want] of Object.entries(cases)) {
    const [k, t] = key.split(",");
    if (k === "sqrt(1+s)") continue;      // checked separately below (its key contains a comma)
    assert.deepStrictEqual(ids(blocks(k, t, 0, 5)), want, key);
  }
  assert.deepStrictEqual(ids(blocks("sqrt(1+s)", "2*sqrt(1+s)", 0, 5)), cases["sqrt(1+s),2*sqrt(1+s)"]);
});

test("the typed kappa and tau are substituted into the algebraic expressions", () => {
  const b = blocks("1+0.5*sin(2*s)", "cos(s)", 0, 6);
  const get = (id) => b.find((x) => x.id === id);
  assert.match(get("T").tex, /1 \+ 0\.5\\,\\sin\\left\(2\\,s\\right\)/);       // T' = kappa(s) N
  assert.match(get("N").tex, /\\cos\\left\(s\\right\)/);                        // tau(s) B in N'
  assert.match(get("evolute").tex, /\\frac\{1\}\{1 \+ 0\.5\\,\\sin/);          // E = r + N / kappa(s)
  assert.match(get("involute").tex, /\(6 - s\)/);                               // s1 = 6
  assert.match(get("radii").tex, /\\sigma\(s\) = \\frac\{1\}\{\\left\|\\cos/);
  const planar = blocks("2+sin(3*s)", "0", 0, 5);
  assert.match(planar.find((x) => x.id === "T").aux[0], /\\theta\(s\) = \\int_\{0\}\^\{s\} 2 \+ \\sin\\left\(3\\,u\\right\)\\,du/);
});

test("closed forms are exact: radicals and fractions instead of decimals", () => {
  const curve = (k, t, s0, s1) => blocks(k, t, s0, s1)[0];
  assert.match(curve("s", "0", 0, 5).tex, /\\sqrt\{\\pi\}.*\\frac\{s\}\{\\sqrt\{\\pi\}\}/);          // sqrt(pi) (C(s/sqrt(pi)), ...)
  assert.match(curve("2*s", "0", 0, 4).tex, /\\sqrt\{\\frac\{\\pi\}\{2\}\}/);                              // sqrt(pi/2)
  assert.match(curve("1.7", "0", 2, 7).tex, /\\frac\{10\}\{17\}/);                                      // 1/kappa = 10/17
  const helix = curve("1.3", "0.8", 0, 15);
  assert.match(helix.tex, /\\frac\{130\}\{233\}/);                                                      // kappa / omega^2
  assert.match(helix.aux[0], /\\frac\{\\sqrt\{233\}\}\{10\}/);                                             // omega, fully reduced
  assert.ok(!/\d+\.\d+/.test(helix.tex + helix.aux.join(" ")), "no decimals left in the helix");
  const theta = blocks("2*s+1", "0", 0, 4).find((x) => x.id === "T").aux[0];
  assert.strictEqual(theta, "\\theta(s) = s^{2} + s");
  const inv = blocks("1/(2*s+3)", "0", 1, 9).find((x) => x.id === "evolute").tex;
  assert.match(inv, /\\left\(2\\,s \+ 3\\right\)/);                                                    // (2s+3) N(s), parenthesised
});

test("theta(s) is integrated symbolically and exactly", () => {
  const P = [1, 1, 1], th = (k, s0 = 0) => F.thetaTeX(Expr.parse(k), s0, P);
  assert.strictEqual(th("2+sin(3*s)"), "2\\,s - \\frac{1}{3}\\cos\\left(3s\\right) + \\frac{1}{3}");
  assert.strictEqual(th("2*s+1"), "s^{2} + s");
  assert.ok(th("exp(s)") && th("1/(s+2)"));
  assert.strictEqual(th("s*sin(s)"), null);
});

test("generic curves show the solved integrals of kappa and tau; planar T and N are explicit", () => {
  const b = blocks("2+sin(3*s)", "1+0.5*cos(5*s)", 0, 4), cur = b.find((y) => y.id === "curve");
  const tx = [cur.tex, ...cur.aux].join(" ");
  assert.match(tx, /\\int_\{0\}\^\{s\} \\kappa\(u\)\\,du = 2\\,s - \\frac\{1\}\{3\}\\cos\\left\(3s\\right\) \+ \\frac\{1\}\{3\}/);
  assert.match(tx, /\\int_\{0\}\^\{s\} \\tau\(u\)\\,du = .*\\sin\\left\(5s\\right\)/);
  assert.ok(!/aligned|Delta|approx/.test(b.map((x) => [x.tex, ...x.aux].join(" ")).join(" ")), "no Taylor series");
  const pl = blocks("2+sin(3*s)", "0", 0, 4);
  assert.match(pl.find((y) => y.id === "T").tex, /\\cos\\left\(2\\,s - \\frac\{1\}\{3\}\\cos/);
  assert.match(pl.find((y) => y.id === "curve").tex, /\\int_\{0\}\^\{s\} .*\\cos\\left\(2\\,u - \\frac\{1\}\{3\}\\cos\\left\(3u/);
});
