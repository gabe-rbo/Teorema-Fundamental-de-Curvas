/*
 * Reconstruction engine: curve r(s) and Frenet frame {T, N, B} from kappa(s), tau(s).
 *
 * The frame obeys F' = Omega(s) F with F = [T; N; B] (rows) and
 *     Omega = [[0, k, 0], [-k, 0, t], [0, -t, 0]].
 * It is advanced with the 4th-order Magnus method (two Gauss points); exp(Omega_h) is a
 * rotation evaluated in closed form (Rodrigues), so the frame stays orthonormal to
 * rounding error without any re-orthonormalization. r(s) is advanced with Simpson's rule
 * on T at the start, midpoint and end of every sub-step. The planar case (tau == 0) goes
 * through the same code: B stays constant and (T, N) rotate by theta(s) = int kappa.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory(require("./expr.js"));
  else (root.Triedro = root.Triedro || {}).Engine = factory(root.Triedro.Expr);
})(typeof self !== "undefined" ? self : this, function (Expr) {
  "use strict";

  var SQ3 = Math.sqrt(3);

  /** exp of the skew matrix [[0,x,y],[-x,0,z],[-y,-z,0]] written into out (row-major 3x3). */
  function expSkew(x, y, z, out) {
    var phi2 = x * x + y * y + z * z;
    var phi = Math.sqrt(phi2);
    var A, Bc;
    if (phi < 1e-4) {
      A = 1 - phi2 / 6;
      Bc = 0.5 - phi2 / 24;
    } else {
      A = Math.sin(phi) / phi;
      Bc = (1 - Math.cos(phi)) / phi2;
    }
    // S = [[0,x,y],[-x,0,z],[-y,-z,0]]; S2 = S*S
    var s00 = -x * x - y * y, s01 = -y * z, s02 = x * z;
    var s10 = -y * z, s11 = -x * x - z * z, s12 = -x * y;
    var s20 = x * z, s21 = -x * y, s22 = -y * y - z * z;
    out[0] = 1 + Bc * s00;      out[1] = A * x + Bc * s01;  out[2] = A * y + Bc * s02;
    out[3] = -A * x + Bc * s10; out[4] = 1 + Bc * s11;      out[5] = A * z + Bc * s12;
    out[6] = -A * y + Bc * s20; out[7] = -A * z + Bc * s21; out[8] = 1 + Bc * s22;
  }

  var _E = new Float64Array(9);

  /** F <- exp(Omega_h) F for one Magnus step of length h starting at s. Returns nothing. */
  function magnusStep(F, kf, tf, s, h, p) {
    var c1 = 0.5 - SQ3 / 6, c2 = 0.5 + SQ3 / 6;
    var k1 = kf(s + c1 * h, p[0], p[1], p[2]), t1 = tf(s + c1 * h, p[0], p[1], p[2]);
    var k2 = kf(s + c2 * h, p[0], p[1], p[2]), t2 = tf(s + c2 * h, p[0], p[1], p[2]);
    // Omega_h = h/2 (A1 + A2) - sqrt(3) h^2 / 12 [A1, A2]; A = [[0,k,0],[-k,0,t],[0,-t,0]]
    // [A1,A2] = A1 A2 - A2 A1 is skew with (x,y,z) = (0, k1*t2 - k2*t1, 0) ... computed below.
    var cx = 0, cy = k1 * t2 - k2 * t1, cz = 0;
    var x = 0.5 * h * (k1 + k2) - (SQ3 * h * h / 12) * cx;
    var y = -(SQ3 * h * h / 12) * cy;
    var z = 0.5 * h * (t1 + t2) - (SQ3 * h * h / 12) * cz;
    expSkew(x, y, z, _E);
    var e = _E;
    var f0 = F[0], f1 = F[1], f2 = F[2], f3 = F[3], f4 = F[4], f5 = F[5], f6 = F[6], f7 = F[7], f8 = F[8];
    F[0] = e[0] * f0 + e[1] * f3 + e[2] * f6; F[1] = e[0] * f1 + e[1] * f4 + e[2] * f7; F[2] = e[0] * f2 + e[1] * f5 + e[2] * f8;
    F[3] = e[3] * f0 + e[4] * f3 + e[5] * f6; F[4] = e[3] * f1 + e[4] * f4 + e[5] * f7; F[5] = e[3] * f2 + e[4] * f5 + e[5] * f8;
    F[6] = e[6] * f0 + e[7] * f3 + e[8] * f6; F[7] = e[6] * f1 + e[7] * f4 + e[8] * f7; F[8] = e[6] * f2 + e[7] * f5 + e[8] * f8;
  }

  /**
   * Reconstruct the curve.
   * spec: { kf, tf (compiled (s,a,b,c)), params [a,b,c], s0, s1, n (points >= 2), sub (substeps >= 1) }
   * Returns { n, s, R, T, N, B, kappa, tau, planar } (flat Float64Arrays, stride 3) or throws.
   */
  function reconstruct(spec) {
    var n = Math.max(2, spec.n | 0);
    var sub = Math.max(1, spec.sub | 0);
    var s0 = spec.s0, s1 = spec.s1;
    if (!(s1 > s0)) throw new Error("O intervalo precisa de s₀ < s₁");
    var kf = spec.kf, tf = spec.tf, p = spec.params || [1, 1, 1];
    var h = (s1 - s0) / (n - 1);
    var hh = h / sub;

    var S = new Float64Array(n), R = new Float64Array(3 * n);
    var T = new Float64Array(3 * n), N = new Float64Array(3 * n), B = new Float64Array(3 * n);
    var kappa = new Float64Array(n), tau = new Float64Array(n);

    var F = new Float64Array([1, 0, 0, 0, 1, 0, 0, 0, 1]);
    var Fm = new Float64Array(9);
    var r0 = 0, r1 = 0, r2 = 0;
    var maxTau = 0;

    for (var i = 0; i < n; i++) {
      var s = s0 + i * h;
      S[i] = s;
      var k = kf(s, p[0], p[1], p[2]), t = tf(s, p[0], p[1], p[2]);
      if (!isFinite(k) || !isFinite(t)) {
        throw new Error("A expressão não é finita em s = " + (+s.toPrecision(5)) + " (divisão por zero ou fora do domínio)");
      }
      kappa[i] = k; tau[i] = t;
      if (Math.abs(t) > maxTau) maxTau = Math.abs(t);
      var o = 3 * i;
      R[o] = r0; R[o + 1] = r1; R[o + 2] = r2;
      T[o] = F[0]; T[o + 1] = F[1]; T[o + 2] = F[2];
      N[o] = F[3]; N[o + 1] = F[4]; N[o + 2] = F[5];
      B[o] = F[6]; B[o + 1] = F[7]; B[o + 2] = F[8];
      if (i === n - 1) break;
      for (var m = 0; m < sub; m++) {
        var sm = s + m * hh;
        var ta0 = F[0], ta1 = F[1], ta2 = F[2];
        for (var q = 0; q < 9; q++) Fm[q] = F[q];
        magnusStep(F, kf, tf, sm, hh / 2, p);
        var tm0 = F[0], tm1 = F[1], tm2 = F[2];
        magnusStep(F, kf, tf, sm + hh / 2, hh / 2, p);
        r0 += (hh / 6) * (ta0 + 4 * tm0 + F[0]);
        r1 += (hh / 6) * (ta1 + 4 * tm1 + F[1]);
        r2 += (hh / 6) * (ta2 + 4 * tm2 + F[2]);
      }
    }
    var scale = 0;
    for (var j = 0; j < n; j++) scale = Math.max(scale, Math.abs(kappa[j]));
    return { n: n, s: S, R: R, T: T, N: N, B: B, kappa: kappa, tau: tau, planar: maxTau < 1e-12, s0: s0, s1: s1 };
  }

  // ------------------------------------------------------- evolute and involute
  /**
   * Evolute E = r + N/kappa (dashed in the UI) and involute I = r + (s1 - s) T as flat arrays.
   * Nothing is clipped by size; evolute points where kappa ~ 0 (no center of curvature)
   * are NaN so the polyline breaks there.
   */
  function associatedCurves(d) {
    var n = d.n;
    var E = new Float64Array(3 * n), I = new Float64Array(3 * n);
    for (var i = 0; i < n; i++) {
      var o = 3 * i, k = d.kappa[i];
      var rho = Math.abs(k) > 1e-9 ? 1 / k : NaN;
      var ok = isFinite(rho);
      var L = d.s1 - d.s[i];
      for (var c = 0; c < 3; c++) {
        E[o + c] = ok ? d.R[o + c] + rho * d.N[o + c] : NaN;
        I[o + c] = d.R[o + c] + L * d.T[o + c];
      }
    }
    return { E: E, I: I };
  }

  // -------------------------------------------------------------- invariants
  function jetEnv(s, p) {
    return { s: Expr.varJet(s), a: Expr.constJet(p[0]), b: Expr.constJet(p[1]), c: Expr.constJet(p[2]) };
  }

  /** Jets of kappa and tau at s. */
  function kappaTauJets(ka, ta, s, p) {
    var env = jetEnv(s, p);
    return { k: Expr.evalJet(ka, env), t: Expr.evalJet(ta, env) };
  }

  /**
   * Curvature, torsion and speed of the evolute and involute at s, parametrized by s,
   * from exact Frenet calculus. For a vector v = (vT, vN, vB) in the moving frame,
   *   Dv = (vT' - k vN, vN' + k vT - t vB, vB' + t vN),
   * E' = (0, -k'/k^2, t/k), I' = (0, (s1 - s) k, 0); a curve with velocity v has
   * curvature |v x Dv| / |v|^3 and torsion (v x Dv) . D^2 v / |v x Dv|^2.
   * Returns { kE, tE, vE, kI, tI, vI } (NaN where undefined).
   */
  function associatedInvariants(ka, ta, s, s1, p, planar) {
    var J = Expr.J;
    var kt = kappaTauJets(ka, ta, s, p);
    var k = kt.k, t = planar ? Expr.constJet(0) : kt.t;
    var zero = Expr.constJet(0);

    function D(v) {
      return [
        J.sub(J.deriv(v[0]), J.mul(k, v[1])),
        J.sub(J.add(J.deriv(v[1]), J.mul(k, v[0])), J.mul(t, v[2])),
        J.add(J.deriv(v[2]), J.mul(t, v[1]))
      ];
    }
    function inv(v1) {
      var v2 = D(v1), v3 = D(v2);
      var a = [v1[0][0], v1[1][0], v1[2][0]], b = [v2[0][0], v2[1][0], v2[2][0]], c3 = [v3[0][0], v3[1][0], v3[2][0]];
      var cr = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
      var c2 = cr[0] * cr[0] + cr[1] * cr[1] + cr[2] * cr[2];
      var sp2 = a[0] * a[0] + a[1] * a[1] + a[2] * a[2];
      return {
        k: Math.sqrt(c2) / Math.pow(sp2, 1.5),
        t: (cr[0] * c3[0] + cr[1] * c3[1] + cr[2] * c3[2]) / c2,
        v: Math.sqrt(sp2)
      };
    }
    var evolute = inv([zero, J.neg(J.div(J.deriv(k), J.mul(k, k))), J.div(t, k)]);
    var L = [s1 - s, -1, 0, 0];
    var involute = inv([zero, J.mul(L, k), zero]);
    var fin = function (x) { return isFinite(x) ? x : NaN; };
    return {
      kE: fin(evolute.k), tE: planar ? (isFinite(evolute.k) ? 0 : NaN) : fin(evolute.t), vE: fin(evolute.v),
      kI: fin(involute.k), tI: planar ? (isFinite(involute.k) ? 0 : NaN) : fin(involute.t), vI: fin(involute.v)
    };
  }

  // ----------------------------------------------------------- classification
  /** Geometric family by exact jets sampled across the interval (labels in Portuguese). */
  function classify(ka, ta, s0, s1, p, planar) {
    var J = Expr.J;
    var samples = [];
    for (var i = 0; i < 9; i++) samples.push(s0 + ((i + 0.5) / 9) * (s1 - s0));
    var tol = 1e-7;
    function all(fn) {
      for (var i = 0; i < samples.length; i++) {
        var ok;
        try { ok = fn(kappaTauJets(ka, ta, samples[i], p)); } catch (e) { ok = false; }
        if (!ok) return false;
      }
      return true;
    }
    var kzero = all(function (j) { return Math.abs(j.k[0]) < 1e-9; });
    if (kzero) return "Reta";
    var kconst = all(function (j) { return Math.abs(j.k[1]) < tol * (1 + Math.abs(j.k[0])); });
    if (planar) {
      if (kconst) return "Círculo";
      if (all(function (j) { return Math.abs(j.k[2]) < tol && Math.abs(j.k[1]) > 1e-6; })) return "Clotoide (espiral de Cornu)";
      if (all(function (j) {
        var q = J.div(Expr.constJet(1), j.k);
        return Math.abs(q[2]) < tol * (1 + Math.abs(q[1])) && Math.abs(q[1]) > 1e-6;
      })) return "Espiral logarítmica";
      return "Curva plana";
    }
    var tconst = all(function (j) { return Math.abs(j.t[1]) < tol * (1 + Math.abs(j.t[0])); });
    if (kconst && tconst) return "Hélice circular";
    if (all(function (j) {
      if (Math.abs(j.k[0]) < 1e-9) return false;
      var r = J.div(j.t, j.k);
      return Math.abs(r[1]) < tol * (1 + Math.abs(r[0])) && Math.abs(r[0]) > 1e-9;
    })) return "Hélice cilíndrica geral (Lancret)";
    return "Curva espacial";
  }

  return {
    reconstruct: reconstruct,
    associatedCurves: associatedCurves,
    associatedInvariants: associatedInvariants,
    kappaTauJets: kappaTauJets,
    classify: classify
  };
});
