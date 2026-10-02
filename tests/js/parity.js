// Compares the JS engine (app/js) with reference data produced by the Python engine.
// Reads {cases: [...]} from stdin, prints {errors: [...]} as JSON.
const path = require("path");
const Expr = require(path.join(__dirname, "../../app/js/expr.js"));
const Eng = require(path.join(__dirname, "../../app/js/engine.js"));

let input = "";
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  const out = [];
  for (const c of JSON.parse(input).cases) {
    const ka = Expr.parse(c.k), ta = Expr.parse(c.t);
    const d = Eng.reconstruct({ kf: Expr.compile(ka), tf: Expr.compile(ta), params: [1, 1, 1], s0: c.s0, s1: c.s1, n: c.n, sub: 2 });
    const maxErr = (a, ref) => {
      let m = 0;
      for (let i = 0; i < c.n; i++) for (let k = 0; k < 3; k++) m = Math.max(m, Math.abs(a[3 * i + k] - ref[k][i]));
      return m;
    };
    const inv = {};
    for (const idx of c.inv_idx) {
      const v = Eng.associatedInvariants(ka, ta, d.s[idx], c.s1, [1, 1, 1], d.planar);
      for (const key of Object.keys(v)) {
        const ref = c.inv[key][idx];
        if (ref === null || Number.isNaN(v[key])) continue;
        inv[key] = Math.max(inv[key] || 0, Math.abs(v[key] - ref) / (1 + Math.abs(ref)));
      }
    }
    out.push({
      k: c.k, t: c.t, planar: d.planar,
      R: maxErr(d.R, c.R), T: maxErr(d.T, c.T), N: maxErr(d.N, c.N), B: maxErr(d.B, c.B),
      inv, label: Eng.classify(ka, ta, c.s0, c.s1, [1, 1, 1], d.planar)
    });
  }
  console.log(JSON.stringify({ errors: out }));
});
