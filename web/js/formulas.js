/*
 * Algebraic formulas for the side panel: the curve r(s), the frame T, N, B, the three
 * planes, the osculating circle, the evolute E(s), the involute I(s) and the radii, with
 * the user's kappa(s) and tau(s) substituted into them.
 *
 * Closed forms are given when they exist (line, circle, circular helix, clothoid through
 * Fresnel integrals, logarithmic spiral); otherwise the formulas are the integral and
 * Frenet-Serret expressions written with the typed functions. Every closed form is
 * checked against the numerical engine in tests/js/formulas.test.js.
 *
 * build() returns blocks: { id, title, tag, cls, tex, aux: [tex...] }.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory(require("./expr.js"), require("./engine.js"));
  else (root.Triedro = root.Triedro || {}).Formulas = factory(root.Triedro.Expr, root.Triedro.Engine);
})(typeof self !== "undefined" ? self : this, function (Expr, Eng) {
  "use strict";

  var num = Expr.num;
  function tex(strings) {                       // String.raw with interpolation
    var out = strings.raw[0];
    for (var i = 1; i < strings.raw.length; i++) out += arguments[i] + strings.raw[i];
    return out;
  }
  function sgn(v) { return v < 0 ? "-" : "+"; }

  // ---- exact arithmetic for the numbers that appear in closed forms ------------------
  /** [p, q] (q > 0, lowest terms) when x is a small rational, else null. */
  function rat(x) {
    if (!isFinite(x)) return null;
    if (Number.isInteger(x)) return [x, 1];
    var tol = 1e-9 * Math.max(1, Math.abs(x));
    for (var q = 2; q <= 2000; q++) {
      var p = Math.round(x * q);
      if (Math.abs(p / q - x) <= tol) { var g = gcd(Math.abs(p), q); return [p / g, q / g]; }
    }
    return null;
  }
  function gcd(a, b) { while (b) { var t = a % b; a = b; b = t; } return a || 1; }
  /** A number as TeX: integer, fraction or (if irrational) a decimal. */
  function T(x) {
    var r = rat(x);
    if (!r) return num(x);
    if (r[1] === 1) return String(r[0]);
    return (r[0] < 0 ? "-" : "") + "\\frac{" + Math.abs(r[0]) + "}{" + r[1] + "}";
  }
  /** Like T but parenthesised when it carries a sign or a fraction, for use as a factor. */
  function TF(x) {
    var t = T(x);
    return x < 0 || t.indexOf("\\frac") >= 0 ? "\\left(" + t + "\\right)" : t;
  }
  /** sqrt of a positive rational as TeX with squares extracted (null if x is not rational). */
  function SQ(x) {
    var r = rat(x);
    if (!r || x <= 0) return null;
    var n = r[0] * r[1], out = 1, inn = n;
    for (var f = 2; f * f <= inn; f++) while (inn % (f * f) === 0) { inn /= f * f; out *= f; }
    var q = r[1], g = gcd(out, q);
    out /= g; q /= g;
    var root = inn === 1 ? "" : "\\sqrt{" + inn + "}";
    var top = (out === 1 && root ? "" : String(out)) + root;
    return q === 1 ? top : "\\frac{" + top + "}{" + q + "}";
  }
  /** A multiplicative coefficient: "" for 1, "-" for -1, otherwise the number as a factor. */
  function coef(x) {
    if (Math.abs(x - 1) < 1e-12) return "";
    if (Math.abs(x + 1) < 1e-12) return "-";
    var t = T(x);
    if (x < 0) return "\\left(" + t + "\\right)" + (t.indexOf("\\frac") >= 0 ? "" : "\\,");
    return t + (t.indexOf("\\frac") >= 0 ? "" : "\\,");
  }
  /** Polynomial c2 s^2 + c1 s + c0 with exact coefficients (zero terms omitted). */
  function poly(c2, c1, c0) {
    var terms = [[c2, "s^{2}"], [c1, "s"], [c0, ""]], out = "";
    terms.forEach(function (tm) {
      var v = tm[0];
      if (Math.abs(v) < 1e-12) return;
      var t = T(Math.abs(v)), body = (Math.abs(Math.abs(v) - 1) < 1e-12 && tm[1]) ? tm[1] : t + (tm[1] && t.indexOf("\\frac") < 0 ? "\\," : "") + tm[1];
      out += (out ? (v < 0 ? " - " : " + ") : (v < 0 ? "-" : "")) + body;
    });
    return out || "0";
  }
  /** 1/kappa written without a nested fraction when kappa is itself 1/x. */
  function invTeX(ast) {
    if (ast.t === "bin" && ast.op === "/" && ast.a.t === "num" && ast.a.v === 1) return wrap(ast.b, Expr.toTeX(ast.b));
    return "\\frac{1}{" + Expr.toTeX(ast) + "}";
  }
  /** Signed sqrt(x^2 * w) helper: sign(v) * sqrt(v^2 / w). */
  function SQs(v, w) { var q = SQ(v * v / w); return q === null ? num(v / Math.sqrt(w)) : (v < 0 ? "-" : "") + q; }

  /** The shifted variable (s - s0) written for a numeric s0. */
  function shifted(s0) {
    if (Math.abs(s0) < 1e-12) return "s";
    return "\\left(s " + sgn(-s0) + " " + T(Math.abs(s0)) + "\\right)";
  }
  /** Wrap a typed expression in parentheses unless it is atomic. */
  function wrap(ast, t) { return ast.t === "num" || ast.t === "var" || ast.t === "call" ? t : "\\left(" + t + "\\right)"; }

  function block(id, title, tag, cls, texStr, aux) {
    return { id: id, title: title, tag: tag, cls: cls, tex: texStr, aux: aux || [] };
  }

  function cases(label) {
    if (label === "Reta") return "line";
    if (label === "Círculo") return "circle";
    if (label.indexOf("Clotoide") === 0) return "clothoid";
    if (label.indexOf("Espiral log") === 0) return "logspiral";
    if (label.indexOf("Hélice circular") === 0) return "helix";
    if (label.indexOf("Hélice cilíndrica") === 0) return "lancret";
    return label === "Curva plana" ? "planar" : "spatial";
  }

  /** Numeric data the closed forms need (read from exact jets at the interval midpoint). */
  function constants(ctx) {
    var sm = (ctx.s0 + ctx.s1) / 2;
    var j = Eng.kappaTauJets(ctx.ka, ctx.ta, sm, ctx.params);
    var q = Expr.J.div(Expr.constJet(1), j.k);
    return {
      k0: j.k[0], t0: j.t[0],
      c: j.k[1], d: j.k[0] - j.k[1] * sm,                    // kappa = c s + d
      la: q[1], lb: q[0] - q[1] * sm,                        // 1/kappa = a s + b
      ratio: j.k[0] !== 0 ? j.t[0] / j.k[0] : NaN
    };
  }


  // ---- symbolic antiderivative of kappa(s) (for theta(s) = integral of kappa) --------
  function pAdd(a, b, k) { var n = Math.max(a.length, b.length), o = []; for (var i = 0; i < n; i++) o.push((a[i] || 0) + k * (b[i] || 0)); return o; }
  function pMul(a, b) { var o = []; for (var i = 0; i < a.length + b.length - 1; i++) o.push(0); a.forEach(function (x, i) { b.forEach(function (y, j) { o[i + j] += x * y; }); }); return o; }
  function pTrim(a) { var n = a.length; while (n > 1 && Math.abs(a[n - 1]) < 1e-14) n--; return a.slice(0, n); }
  /** Coefficients [c0, c1, ...] of a polynomial in s (parameters a, b, c substituted), else null. */
  function polyOf(ast, P) {
    switch (ast.t) {
      case "num": return [ast.v];
      case "var": return ast.n === "s" ? [0, 1] : [P[{ a: 0, b: 1, c: 2 }[ast.n]]];
      case "neg": { var q = polyOf(ast.a, P); return q && pAdd([0], q, -1); }
      case "bin": {
        var x = polyOf(ast.a, P), y = polyOf(ast.b, P);
        if (ast.op === "^") {
          if (!x || !ast.b || ast.b.t !== "num" || !Number.isInteger(ast.b.v) || ast.b.v < 0 || ast.b.v > 8) return null;
          var r = [1]; for (var i = 0; i < ast.b.v; i++) r = pMul(r, x); return r;
        }
        if (!x || !y) return null;
        if (ast.op === "+") return pAdd(x, y, 1);
        if (ast.op === "-") return pAdd(x, y, -1);
        if (ast.op === "*") return pMul(x, y);
        y = pTrim(y); return y.length === 1 && y[0] !== 0 ? x.map(function (v) { return v / y[0]; }) : null;
      }
    }
    return null;
  }
  /** Linear form a s + b of an argument, else null. */
  function linOf(ast, P) { var q = polyOf(ast, P); if (!q) return null; q = pTrim(q); return q.length <= 2 ? { a: q[1] || 0, b: q[0] } : null; }
  function linTeX(a, b, v) {
    var lead = Math.abs(a - 1) < 1e-12 ? "" : Math.abs(a + 1) < 1e-12 ? "-" : T(a);
    return lead + v + (Math.abs(b) < 1e-12 ? "" : " " + sgn(b) + " " + T(Math.abs(b)));
  }
  /** "c body" with its sign, for building sums term by term. */
  function addTerm(acc, c, body) {
    if (Math.abs(c) < 1e-12) return acc;
    var t = T(Math.abs(c)), lead = Math.abs(Math.abs(c) - 1) < 1e-12 && body ? "" : t + (body && t.indexOf("\\frac") < 0 ? "\\," : "");
    return acc + (acc ? (c < 0 ? " - " : " + ") : (c < 0 ? "-" : "")) + lead + body;
  }
  /**
   * Primitive F of kappa as TeX plus a numeric F(x), for sums of polynomials and of
   * sin, cos, exp, sinh, cosh, tanh, sqrt and 1/linear of linear arguments. null otherwise.
   */
  function antiderivative(ast, P, v) {
    v = v || "s";
    var tf = [], poly = [0], ok = true;
    function go(a, k) {
      if (!ok) return;
      var pl = polyOf(a, P);
      if (pl) { poly = pAdd(poly, pl, k); return; }
      if (a.t === "neg") return go(a.a, -k);
      if (a.t === "bin" && (a.op === "+" || a.op === "-")) { go(a.a, k); go(a.b, a.op === "+" ? k : -k); return; }
      if (a.t === "bin" && a.op === "*") {
        var pa = polyOf(a.a, P), pb = polyOf(a.b, P);
        if (pa && pTrim(pa).length === 1) return go(a.b, k * pa[0]);
        if (pb && pTrim(pb).length === 1) return go(a.a, k * pb[0]);
        ok = false; return;
      }
      if (a.t === "bin" && a.op === "/") {
        var d = polyOf(a.b, P), nn = polyOf(a.a, P);
        if (d && pTrim(d).length === 1 && d[0] !== 0) return go(a.a, k / d[0]);
        var L = linOf(a.b, P);
        if (nn && pTrim(nn).length === 1 && L && L.a !== 0) {
          var cc = k * nn[0] / L.a;
          tf.push({ c: cc, body: "\\ln\\left|" + linTeX(L.a, L.b, v) + "\\right|", f: function (x) { return cc * Math.log(Math.abs(L.a * x + L.b)); } });
          return;
        }
        ok = false; return;
      }
      if (a.t === "call") {
        var m = linOf(a.a, P);
        if (!m) { ok = false; return; }
        var A = m.a, B = m.b, g = linTeX(A, B, v), cc2 = k / A;
        if (Math.abs(A) < 1e-12) { ok = false; return; }
        var spec = {
          sin: ["\\cos", -1, function (z) { return Math.cos(z); }],
          cos: ["\\sin", 1, function (z) { return Math.sin(z); }],
          sinh: ["\\cosh", 1, function (z) { return Math.cosh(z); }],
          cosh: ["\\sinh", 1, function (z) { return Math.sinh(z); }],
          tanh: ["\\ln\\cosh", 1, function (z) { return Math.log(Math.cosh(z)); }]
        }[a.f];
        if (spec) {
          var c3 = cc2 * spec[1];
          tf.push({ c: c3, body: spec[0] + "\\left(" + g + "\\right)", f: function (x) { return c3 * spec[2](A * x + B); } });
        } else if (a.f === "exp") {
          tf.push({ c: cc2, body: "e^{" + g + "}", f: function (x) { return cc2 * Math.exp(A * x + B); } });
        } else if (a.f === "sqrt") {
          var c4 = 2 * cc2 / 3;
          tf.push({ c: c4, body: "\\left(" + g + "\\right)^{3/2}", f: function (x) { return c4 * Math.pow(A * x + B, 1.5); } });
        } else ok = false;
        return;
      }
      ok = false;
    }
    go(ast, 1);
    if (!ok) return null;
    poly = pTrim(poly);
    var tex_ = "";
    for (var i = poly.length - 1; i >= 0; i--) tex_ = addTerm(tex_, poly[i] / (i + 1), i === 0 ? v : v + "^{" + (i + 1) + "}");
    tf.forEach(function (t) { tex_ = addTerm(tex_, t.c, t.body); });
    return {
      tex: tex_ || "0",
      at: function (x) {
        var v = 0; poly.forEach(function (c, i) { v += c / (i + 1) * Math.pow(x, i + 1); });
        tf.forEach(function (t) { v += t.f(x); });
        return v;
      }
    };
  }
  /** theta(s) = integral of kappa from s0, as TeX, or null if no elementary primitive was found. */
  function thetaTeX(ka, s0, P, v) {
    var F;
    try { F = antiderivative(ka, P, v); } catch (e) { F = null; }
    if (!F) return null;
    var c0 = -F.at(s0);
    if (!isFinite(c0)) return null;
    var t = F.tex;
    return Math.abs(c0) < 1e-12 ? t : t + " " + sgn(c0) + " " + T(Math.abs(c0));
  }

  function build(ctx) {
    var kind = cases(ctx.label), planar = ctx.planar;
    var s0 = ctx.s0, s1 = ctx.s1, S = shifted(s0), n = num;
    var kT = Expr.toTeX(ctx.ka), tT = Expr.toTeX(ctx.ta), kU = Expr.toTeX(ctx.ka, { s: "u" });
    var kW = wrap(ctx.ka, kT), tW = wrap(ctx.ta, tT);
    var K;
    try { K = constants(ctx); } catch (e) { K = {}; }
    var out = [], P = ctx.params;
    var thS = thetaTeX(ctx.ka, s0, P);
    var thU = thetaTeX(ctx.ka, s0, P, "u"), phS = planar ? null : thetaTeX(ctx.ta, s0, P);

    // ------------------------------------------------------------ r(s), T, N, B
    var theta = tex`\theta(s) = \int_{${T(s0)}}^{s} ${kU}\,du`;
    switch (kind) {
      case "line":
        out.push(block("curve", "Curva reconstruída", "r", "tf-tag--r", tex`r(s) = r(s_0) + ${S}\,T_0`));
        out.push(block("T", "Vetor tangente", "T", "tf-tag--t", tex`T(s) = T_0 = \text{const}`));
        out.push(block("N", "Vetor normal principal", "N", "tf-tag--n", tex`N(s) = N_0 = \text{const}`));
        if (!planar) out.push(block("B", "Vetor binormal", "B", "tf-tag--b", tex`B(s) = B_0 = \text{const}`));
        break;
      case "circle": {
        var k = K.k0, kS = tex`${T(k)}\,${S}`, cf = coef(1 / k);
        out.push(block("curve", "Curva reconstruída", "r", "tf-tag--r",
          tex`r(s) = \left( ${cf}\sin\left(${kS}\right),\ ${cf}\left(1-\cos\left(${kS}\right)\right) \right)`));
        out.push(block("T", "Vetor tangente", "T", "tf-tag--t", tex`T(s) = \left( \cos\left(${kS}\right),\ \sin\left(${kS}\right) \right)`));
        out.push(block("N", "Vetor normal principal", "N", "tf-tag--n", tex`N(s) = \left( -\sin\left(${kS}\right),\ \cos\left(${kS}\right) \right)`));
        break;
      }
      case "clothoid": {
        // kappa = c s + d, theta(s0) = 0:  theta = c (s^2 - s0^2)/2 + d (s - s0)
        var c = K.c, d = K.d, u0 = s0 + d / c, phi = -c * u0 * u0 / 2, sig = c < 0 ? -1 : 1, ac = Math.abs(c);
        var cr = rat(ac), exact = !!(cr && rat(d) && rat(s0));
        var pref, aT;
        if (exact) {                               // sqrt(pi/|c|) and sqrt(|c|/pi), |c| = p/q
          var cp = cr[0], cq = cr[1], one = cp === 1 && cq === 1;
          pref = one ? tex`\sqrt{\pi}` : tex`\sqrt{\frac{${cq === 1 ? "" : cq}\pi}{${cp}}}`;
          aT = one ? tex`\frac{1}{\sqrt{\pi}}` : tex`\sqrt{\frac{${cp}}{${cq === 1 ? "" : cq}\pi}}`;
        } else { pref = n(Math.sqrt(Math.PI / ac)); aT = n(Math.sqrt(ac / Math.PI)); }
        var pure = Math.abs(u0) < 1e-12;           // u0 = s0 + d/c = 0: no shift, no rotation
        var argTex = pure
          ? (exact && cr[0] === 1 && cr[1] === 1 ? tex`\frac{s}{\sqrt{\pi}}` : tex`${aT}\,s`)
          : tex`${aT}\left(s ${sgn(d / c)} ${T(Math.abs(d / c))}\right)`;
        var x0Tex = tex`${aT}\cdot ${TF(u0)}`;
        var sgnS = sig < 0 ? "-" : "";
        var thetaFull = poly(c / 2, d, -(c * s0 * s0 / 2 + d * s0));
        var curveTex = pure
          ? tex`r(s) = ${pref}\left( C\!\left(${argTex}\right),\ ${sgnS}S\!\left(${argTex}\right) \right)`
          : tex`r(s) = R_{${T(phi)}}\,${pref}\left( C\!\left(${argTex}\right) - C\!\left(${x0Tex}\right),\ ${sgnS}\left[ S\!\left(${argTex}\right) - S\!\left(${x0Tex}\right) \right] \right)`;
        var fres = tex`C(x) = \int_0^x \cos\frac{\pi t^2}{2}\,dt,\quad S(x) = \int_0^x \sin\frac{\pi t^2}{2}\,dt`;
        if (!pure) fres += tex`,\quad R_\varphi = \begin{pmatrix} \cos\varphi & -\sin\varphi \\ \sin\varphi & \cos\varphi \end{pmatrix}`;
        out.push(block("curve", "Curva reconstruída", "r", "tf-tag--r", curveTex, [fres]));
        out.push(block("T", "Vetor tangente", "T", "tf-tag--t", tex`T(s) = \left( \cos\theta(s),\ \sin\theta(s) \right)`, [tex`\theta(s) = ${thetaFull}`]));
        out.push(block("N", "Vetor normal principal", "N", "tf-tag--n", tex`N(s) = \left( -\sin\theta(s),\ \cos\theta(s) \right)`));
        break;
      }
      case "logspiral": {
        // 1/kappa = a s + b  ->  theta = (1/a) ln y,  y = (a s + b) / w0
        var la = K.la, lb = K.lb, p = 1 / la, w0 = la * s0 + lb;
        var y = tex`y(s) = \frac{${coef(la)}s ${sgn(lb)} ${T(Math.abs(lb))}}{${T(w0)}}`;
        var th = tex`\theta(s) = ${coef(p)}\ln y(s)`;
        var kcoef = coef(w0 / la / (1 + p * p)), pT = T(p);
        out.push(block("curve", "Curva reconstruída", "r", "tf-tag--r",
          tex`r(s) = ${kcoef}\left( y\left(\cos\theta + ${coef(p)}\sin\theta\right) - 1,\ \ y\left(\sin\theta - ${coef(p)}\cos\theta\right) + ${pT} \right)`, [y, th]));
        out.push(block("T", "Vetor tangente", "T", "tf-tag--t", tex`T(s) = \left( \cos\theta(s),\ \sin\theta(s) \right)`));
        out.push(block("N", "Vetor normal principal", "N", "tf-tag--n", tex`N(s) = \left( -\sin\theta(s),\ \cos\theta(s) \right)`));
        break;
      }
      case "planar": {
        var thArg = thS ? tex`\left(${thS}\right)` : "\\theta(s)";
        var thArgU = thU ? tex`\left(${thU}\right)` : "\\theta(u)";
        out.push(block("curve", "Curva reconstruída", "r", "tf-tag--r",
          tex`r(s) = r(s_0) + \int_{${T(s0)}}^{s} \left( \cos${thArgU},\ \sin${thArgU} \right) du`,
          thS ? [] : [theta]));
        out.push(block("T", "Vetor tangente", "T", "tf-tag--t", tex`T(s) = \left( \cos${thArg},\ \sin${thArg} \right)`,
          thS ? [tex`\theta(s) = \int_{${T(s0)}}^{s} ${kU}\,du = ${thS}`] : [theta]));
        out.push(block("N", "Vetor normal principal", "N", "tf-tag--n", tex`N(s) = \left( -\sin${thArg},\ \cos${thArg} \right)`));
        break;
      }
      case "helix": {
        var kk = K.k0, tt = K.t0, W = kk * kk + tt * tt;
        var omT = SQ(W) || num(Math.sqrt(W));                     // omega = sqrt(kappa^2 + tau^2)
        var Rr = T(kk / W), A = SQs(kk, W), Bt = SQs(tt, W), nA = A.charAt(0) === "-" ? A.slice(1) : "-" + A;
        var oS = tex`${omT}\,${S}`;
        out.push(block("curve", "Curva reconstruída", "r", "tf-tag--r",
          tex`r(s) = \left( ${coef(kk / W)}\left(1-\cos\left(${oS}\right)\right),\ ${coef(kk / W)}\sin\left(${oS}\right),\ ${Bt}\,${S} \right)`,
          [tex`\omega = \sqrt{\kappa^2+\tau^2} = ${omT},\quad R = \frac{\kappa}{\omega^2} = ${Rr},\quad \text{passo } 2\pi\frac{\tau}{\omega^2} = ${coef(2 * tt / W)}\pi`,
            tex`\text{(forma canônica, a menos de um movimento rígido)}`]));
        out.push(block("T", "Vetor tangente", "T", "tf-tag--t", tex`T(s) = \left( ${A}\sin\left(${oS}\right),\ ${A}\cos\left(${oS}\right),\ ${Bt} \right)`));
        out.push(block("N", "Vetor normal principal", "N", "tf-tag--n", tex`N(s) = \left( \cos\left(${oS}\right),\ -\sin\left(${oS}\right),\ 0 \right)`));
        out.push(block("B", "Vetor binormal", "B", "tf-tag--b", tex`B(s) = \left( ${Bt}\sin\left(${oS}\right),\ ${Bt}\cos\left(${oS}\right),\ ${nA} \right)`));
        break;
      }
      default: {                                  // lancret + generic spatial: Frenet-Serret
        var aux0 = kind === "lancret"
          ? [tex`\frac{\tau}{\kappa} = ${T(K.ratio)} = \text{const},\quad \langle T, u_0\rangle = \cos\alpha = ${SQs(K.ratio, 1 + K.ratio * K.ratio)}`]
          : [];
        var solved = [];
        if (thS) solved.push(tex`\int_{${T(s0)}}^{s} \kappa(u)\,du = ${thS}`);
        if (phS) solved.push(tex`\int_{${T(s0)}}^{s} \tau(u)\,du = ${phS}`);
        out.push(block("curve", "Curva reconstruída", "r", "tf-tag--r", tex`r(s) = r(s_0) + \int_{${T(s0)}}^{s} T(u)\,du`, aux0.concat(solved)));
        out.push(block("T", "Vetor tangente", "T", "tf-tag--t", tex`T'(s) = ${kW}\,N(s)`, [tex`T(s) = \frac{dr}{ds}`]));
        out.push(block("N", "Vetor normal principal", "N", "tf-tag--n", tex`N'(s) = -${kW}\,T(s) + ${tW}\,B(s)`));
        out.push(block("B", "Vetor binormal", "B", "tf-tag--b", tex`B'(s) = -${tW}\,N(s)`, [tex`B(s) = T(s)\times N(s)`]));
      }
    }

    // ------------------------------------------------- planes and osculating circle
    if (!planar) {
      out.push(block("plane-osc", "Plano osculador (T, N)", "B", "tf-tag--b", tex`\langle x - r(s),\ B(s)\rangle = 0`));
      out.push(block("plane-normal", "Plano normal (N, B)", "T", "tf-tag--t", tex`\langle x - r(s),\ T(s)\rangle = 0`));
      out.push(block("plane-rect", "Plano retificante (T, B)", "N", "tf-tag--n", tex`\langle x - r(s),\ N(s)\rangle = 0`));
    }
    if (kind !== "line") {
      out.push(block("circle", "Círculo osculador", "ρ", "tf-tag--p",
        tex`C(\theta) = r(s) + \frac{1}{\kappa}\,N(s)\,(1-\cos\theta) + \rho(s)\,T(s)\sin\theta`,
        [tex`\text{centro } c(s) = r(s) + ${invTeX(ctx.ka)}\,N(s),\quad \rho(s) = \frac{1}{\left|${kT}\right|}`]));
    }

    // ------------------------------------------------------------ evolute / involute
    var eAux = [], iAux = [];
    var evo = tex`E(s) = r(s) + ${invTeX(ctx.ka)}\,N(s)`;
    if (kind === "line") {
      evo = tex`E(s) \to \infty`;
    } else if (kind === "circle") {
      evo = tex`E(s) = \left( 0,\ ${T(1 / K.k0)} \right) = \text{const}`;
    } else if (planar) {
      eAux.push(tex`\kappa_E = \frac{\kappa^3}{|\kappa'|},\quad \tau_E = 0`);
      iAux.push(tex`\kappa_I = \frac{1}{s_1 - s},\quad \tau_I = 0`);
    } else {
      eAux.push(tex`E'(s) = -\frac{\kappa'}{\kappa^2}\,N + \frac{\tau}{\kappa}\,B`);
      iAux.push(tex`\kappa_I = \frac{\sqrt{\kappa^2+\tau^2}}{(s_1-s)\,\kappa},\quad \tau_I = \frac{\kappa\tau' - \kappa'\tau}{(s_1-s)\,\kappa\,(\kappa^2+\tau^2)}`);
    }
    out.push(block("evolute", "Evoluta (centros de curvatura)", "E", "tf-tag--e", evo, eAux));
    out.push(block("involute", "Involuta (evolvente de corda)", "I", "tf-tag--i",
      kind === "line" ? tex`I(s) = r(s_1) = \text{const}` : tex`I(s) = r(s) + (${T(s1)} - s)\,T(s)`, iAux));

    // ------------------------------------------------------------------- radii
    out.push(block("radii", "Raios característicos", "ρ", "tf-tag--p",
      tex`\rho(s) = \frac{1}{\left|${kT}\right|}` + (planar ? tex`,\quad \sigma(s) = \infty` : tex`,\quad \sigma(s) = \frac{1}{\left|${tT}\right|}`)));
    return out;
  }

  return { build: build, cases: cases, thetaTeX: thetaTeX };
});
