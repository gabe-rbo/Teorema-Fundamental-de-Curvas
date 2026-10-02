// Unit tests for the browser engine, run with: node --test tests/js
const test = require("node:test");
const assert = require("node:assert");
const path = require("path");
const Expr = require(path.join(__dirname, "../../web/js/expr.js"));
const Eng = require(path.join(__dirname, "../../web/js/engine.js"));

const run = (k, t, s0, s1, n, params = [1, 1, 1]) =>
  Eng.reconstruct({ kf: Expr.compile(Expr.parse(k)), tf: Expr.compile(Expr.parse(t)), params, s0, s1, n, sub: 2 });

test("parser rejects unknown names, bad syntax and empty input", () => {
  for (const bad of ["", "   ", "1+", "foo(s)", "x+1", "sin s", "2 $ 3", "(1+s", "1+)", "s s s )"]) {
    assert.throws(() => Expr.parse(bad), (e) => e.name === "ExprError", bad);
  }
});

test("parser never evaluates code: identifiers outside the whitelist are rejected", () => {
  for (const bad of ["process", "constructor", "__proto__", "Math.sin(s)", "alert(1)", "this", "eval(s)"]) {
    assert.throws(() => Expr.parse(bad), (e) => e.name === "ExprError", bad);
  }
});

test("precedence, implicit multiplication and unary minus", () => {
  const f = (src, s = 2) => Expr.compile(Expr.parse(src))(s, 1, 2, 3);
  assert.strictEqual(f("2+3*s"), 8);
  assert.strictEqual(f("-s^2"), -4);          // -(s^2)
  assert.strictEqual(f("2^3^2", 0), 512);     // right associative
  assert.strictEqual(f("2s"), 4);
  assert.strictEqual(f("(s+1)(s-1)"), 3);
  assert.strictEqual(f("1/2*s"), 1);
  assert.ok(Math.abs(f("a+b*cos(c*s)") - (1 + 2 * Math.cos(6))) < 1e-14);
  assert.ok(Math.abs(f("2*pi", 0) - 2 * Math.PI) < 1e-14);
  assert.ok(Math.abs(f("1e-3*s") - 0.002) < 1e-15);
});

test("jets give exact derivatives (checked against finite differences)", () => {
  const exprs = ["1+0.5*sin(s)", "exp(-s^2)", "sqrt(1+s)", "1/(1+s^2)", "tanh(s-1)", "atan(s)", "asin(s/3)", "log(2+s)", "abs(s)+1", "s^3*cos(s)"];
  for (const src of exprs) {
    const ast = Expr.parse(src), f = Expr.compile(ast), s = 0.7;
    const jet = Expr.evalJet(ast, { s: Expr.varJet(s), a: Expr.constJet(1), b: Expr.constJet(1), c: Expr.constJet(1) });
    const h = 1e-3, g = (x) => f(x, 1, 1, 1);
    const d1 = (g(s + h) - g(s - h)) / (2 * h);
    const d2 = (g(s + h) - 2 * g(s) + g(s - h)) / (h * h);
    assert.ok(Math.abs(jet[0] - g(s)) < 1e-12, src);
    assert.ok(Math.abs(jet[1] - d1) < 1e-5, src + " f'");
    assert.ok(Math.abs(2 * jet[2] - d2) < 1e-4, src + " f''");
  }
});

test("circle closes and the frame stays orthonormal", () => {
  const d = run("1", "0", 0, 2 * Math.PI, 400);
  assert.ok(d.planar);
  assert.ok(Math.hypot(d.R[3 * 399], d.R[3 * 399 + 1]) < 1e-7);
  const h = run("1.3", "0.8", 0, 30, 1500);
  let err = 0;
  for (let i = 0; i < h.n; i++) {
    const o = 3 * i, dot = (A, B) => A[o] * B[o] + A[o + 1] * B[o + 1] + A[o + 2] * B[o + 2];
    err = Math.max(err, Math.abs(dot(h.T, h.T) - 1), Math.abs(dot(h.N, h.N) - 1), Math.abs(dot(h.T, h.N)), Math.abs(dot(h.N, h.B)), Math.abs(dot(h.T, h.B)));
  }
  assert.ok(err < 1e-10, "orthonormality error " + err);
});

test("circular helix: chord and axial advance match the closed form", () => {
  // With T0 = x the helix advances (tau/w) s along its axis and its radial chord from the
  // start point is (k/w^2) sqrt(2 (1 - cos(w s))), with w = sqrt(k^2 + tau^2).
  const k = 1, t = 0.5, w = Math.hypot(k, t);
  const d = run(String(k), String(t), 0, 4 * Math.PI, 1200);
  let maxdev = 0;
  for (let i = 0; i < d.n; i++) {
    const axial = (t / w) * d.s[i];
    const dist2 = d.R[3 * i] ** 2 + d.R[3 * i + 1] ** 2 + d.R[3 * i + 2] ** 2;
    const radial = Math.sqrt(Math.max(dist2 - axial * axial, 0));
    const chord = (k / (w * w)) * Math.sqrt(2 * (1 - Math.cos(w * d.s[i])));
    maxdev = Math.max(maxdev, Math.abs(radial - chord));
  }
  assert.ok(maxdev < 1e-6, "helix deviation " + maxdev);
});

test("non-finite expressions and bad intervals are reported, not drawn", () => {
  assert.throws(() => run("1/s", "0", 0, 1, 50), /não é finita/);
  assert.throws(() => run("1", "0", 2, 1, 50), /s₀ < s₁/);
});

test("signed curvature is accepted for planar curves", () => {
  const d = run("2*sin(s)", "0", 0, 12.5, 600);
  assert.ok(d.planar);
  assert.ok(d.kappa.some((v) => v < 0) && d.kappa.some((v) => v > 0));
  for (let i = 0; i < d.n; i++) assert.ok(Number.isFinite(d.R[3 * i]) && Number.isFinite(d.R[3 * i + 1]));
});

test("evolute and involute invariants match closed forms for planar curves", () => {
  const ka = Expr.parse("1+0.3*sin(s)"), ta = Expr.parse("0");
  const s = 1.7, s1 = 6;
  const v = Eng.associatedInvariants(ka, ta, s, s1, [1, 1, 1], true);
  const k = 1 + 0.3 * Math.sin(s), dk = 0.3 * Math.cos(s);
  assert.ok(Math.abs(v.kE - (k ** 3) / Math.abs(dk)) < 1e-9);     // kappa_E = kappa^3 / |kappa'|
  assert.ok(Math.abs(v.kI - 1 / (s1 - s)) < 1e-12);               // kappa_I = 1 / (s1 - s)
  assert.strictEqual(v.tE, 0);
  assert.strictEqual(v.tI, 0);
});

test("classification", () => {
  const c = (k, t, planar, s1 = 5) => Eng.classify(Expr.parse(k), Expr.parse(t), 0, s1, [1, 1, 1], planar);
  assert.strictEqual(c("0", "0", true), "Reta");
  assert.strictEqual(c("1", "0", true), "Círculo");
  assert.match(c("s", "0", true), /Clotoide/);
  assert.strictEqual(c("1/(s+1)", "0", true), "Espiral logarítmica");
  assert.strictEqual(c("1+sin(s)", "0", true), "Curva plana");
  assert.strictEqual(c("1", "1", false), "Hélice circular");
  assert.match(c("sqrt(1+s)", "2*sqrt(1+s)", false), /Lancret/);
  assert.strictEqual(c("1+sin(s)", "cos(s)", false), "Curva espacial");
});

test("5000 points reconstruct well under a frame budget", () => {
  const t0 = process.hrtime.bigint();
  for (let i = 0; i < 10; i++) run("1+0.5*sin(s)", "cos(2*s)", 0, 25, 5000);
  const ms = Number(process.hrtime.bigint() - t0) / 1e6 / 10;
  assert.ok(ms < 40, "average " + ms.toFixed(1) + " ms");
});
