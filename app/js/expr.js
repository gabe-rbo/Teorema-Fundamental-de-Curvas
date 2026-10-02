/*
 * Safe math-expression engine for kappa(s) and tau(s).
 *
 *  - parse():   tokenizer + recursive-descent parser -> AST (whitelisted names only)
 *  - compile(): AST -> fast scalar function (s, a, b, c). The JS source is emitted from
 *               the validated AST (numbers, whitelisted names and Math.* calls only);
 *               user text is never evaluated.
 *  - evalJet(): AST evaluated on truncated Taylor series (order 3), giving exact
 *               derivatives f', f'', f''' with no finite differences.
 *  - toTeX():   AST -> LaTeX for the live formula preview.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else (root.Triedro = root.Triedro || {}).Expr = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var FUNCS = ["sin", "cos", "tan", "exp", "log", "ln", "sqrt", "sinh", "cosh", "tanh", "asin", "acos", "atan", "abs"];
  var VARS = ["s", "a", "b", "c"];
  var CONSTS = { pi: Math.PI, e: Math.E };

  function ExprError(message, pos) {
    var err = new Error(message);
    err.name = "ExprError";
    err.pos = pos;
    return err;
  }

  // ---------------------------------------------------------------- tokenizer
  function tokenize(src) {
    var toks = [];
    var i = 0;
    var n = src.length;
    while (i < n) {
      var ch = src[i];
      if (/\s/.test(ch)) { i++; continue; }
      var m;
      if ((m = /^(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?/.exec(src.slice(i)))) {
        toks.push({ t: "num", v: parseFloat(m[0]), pos: i });
        i += m[0].length;
      } else if ((m = /^[A-Za-z_][A-Za-z_0-9]*/.exec(src.slice(i)))) {
        toks.push({ t: "id", v: m[0], pos: i });
        i += m[0].length;
      } else if (src.substr(i, 2) === "**") {
        toks.push({ t: "op", v: "^", pos: i });
        i += 2;
      } else if ("+-*/^()".indexOf(ch) >= 0) {
        toks.push({ t: "op", v: ch, pos: i });
        i++;
      } else {
        throw ExprError("Caractere inesperado '" + ch + "'", i);
      }
    }
    return toks;
  }

  // ------------------------------------------------------------------- parser
  function parse(src) {
    if (typeof src !== "string" || !src.trim()) throw ExprError("Expressão vazia", 0);
    var toks = tokenize(src);
    var p = 0;

    function peek() { return toks[p]; }
    function isOp(v) { var t = toks[p]; return t && t.t === "op" && t.v === v; }

    function startsOperand(t) {
      return t && (t.t === "num" || t.t === "id" || (t.t === "op" && t.v === "("));
    }

    function parseExpr() {
      var left = parseTerm();
      while (isOp("+") || isOp("-")) {
        var op = toks[p++].v;
        left = { t: "bin", op: op, a: left, b: parseTerm() };
      }
      return left;
    }

    function parseTerm() {
      var left = parseUnary();
      for (;;) {
        if (isOp("*") || isOp("/")) {
          var op = toks[p++].v;
          left = { t: "bin", op: op, a: left, b: parseUnary() };
        } else if (startsOperand(peek())) {
          // implicit multiplication: 2s, 2(s+1), (s+1)(s-1), s(s+1)
          left = { t: "bin", op: "*", a: left, b: parseUnary() };
        } else {
          return left;
        }
      }
    }

    function parseUnary() {
      if (isOp("-")) { p++; return { t: "neg", a: parseUnary() }; }
      if (isOp("+")) { p++; return parseUnary(); }
      return parsePower();
    }

    function parsePower() {
      var base = parseAtom();
      if (isOp("^")) { p++; return { t: "bin", op: "^", a: base, b: parseUnary() }; }
      return base;
    }

    function parseAtom() {
      var t = toks[p];
      if (!t) throw ExprError("Expressão incompleta", src.length);
      if (t.t === "num") { p++; return { t: "num", v: t.v }; }
      if (t.t === "id") {
        p++;
        var name = t.v.toLowerCase();
        if (FUNCS.indexOf(name) >= 0) {
          if (!isOp("(")) throw ExprError("Use parênteses após '" + t.v + "', por exemplo " + t.v + "(s)", t.pos);
          p++;
          var arg = parseExpr();
          if (!isOp(")")) throw ExprError("Parêntese não fechado", peek() ? peek().pos : src.length);
          p++;
          return { t: "call", f: name === "ln" ? "log" : name, a: arg };
        }
        if (VARS.indexOf(name) >= 0) return { t: "var", n: name };
        if (Object.prototype.hasOwnProperty.call(CONSTS, name)) return { t: "num", v: CONSTS[name], name: name };
        throw ExprError("Nome desconhecido '" + t.v + "' (use s, a, b, c, pi, e e funções como sin, cos, exp)", t.pos);
      }
      if (t.v === "(") {
        p++;
        var inner = parseExpr();
        if (!isOp(")")) throw ExprError("Parêntese não fechado", peek() ? peek().pos : src.length);
        p++;
        return inner;
      }
      throw ExprError("Símbolo inesperado '" + t.v + "'", t.pos);
    }

    var ast = parseExpr();
    if (p < toks.length) throw ExprError("Símbolo inesperado '" + toks[p].v + "'", toks[p].pos);
    return ast;
  }

  /** True if the AST references the named variable. */
  function usesVar(ast, name) {
    switch (ast.t) {
      case "var": return ast.n === name;
      case "num": return false;
      case "neg": case "call": return usesVar(ast.a, name);
      default: return usesVar(ast.a, name) || usesVar(ast.b, name);
    }
  }

  // ------------------------------------------------------------ scalar compile
  var MATH = {
    sin: "Math.sin", cos: "Math.cos", tan: "Math.tan", exp: "Math.exp", log: "Math.log",
    sqrt: "Math.sqrt", sinh: "Math.sinh", cosh: "Math.cosh", tanh: "Math.tanh",
    asin: "Math.asin", acos: "Math.acos", atan: "Math.atan", abs: "Math.abs"
  };

  function emit(ast) {
    switch (ast.t) {
      case "num": return "(" + String(ast.v) + ")";
      case "var": return ast.n;
      case "neg": return "(-" + emit(ast.a) + ")";
      case "call": return MATH[ast.f] + "(" + emit(ast.a) + ")";
      case "bin":
        if (ast.op === "^") return "Math.pow(" + emit(ast.a) + "," + emit(ast.b) + ")";
        return "(" + emit(ast.a) + ast.op + emit(ast.b) + ")";
    }
    throw new Error("bad node");
  }

  /** Compile a validated AST to a function (s, a, b, c) -> number. */
  function compile(ast) {
    // eslint-disable-next-line no-new-func
    return new Function("s", "a", "b", "c", "return " + emit(ast) + ";");
  }

  // --------------------------------------------------------------------- jets
  // A jet is [c0, c1, c2, c3]: f(s0 + t) = c0 + c1 t + c2 t^2 + c3 t^3.
  var K = 4;
  function constJet(v) { return [v, 0, 0, 0]; }
  function varJet(v) { return [v, 1, 0, 0]; }

  var J = {
    add: function (x, y) { return [x[0] + y[0], x[1] + y[1], x[2] + y[2], x[3] + y[3]]; },
    sub: function (x, y) { return [x[0] - y[0], x[1] - y[1], x[2] - y[2], x[3] - y[3]]; },
    neg: function (x) { return [-x[0], -x[1], -x[2], -x[3]]; },
    scale: function (x, k) { return [x[0] * k, x[1] * k, x[2] * k, x[3] * k]; },
    mul: function (x, y) {
      var r = [0, 0, 0, 0];
      for (var k = 0; k < K; k++) {
        var acc = 0;
        for (var i = 0; i <= k; i++) acc += x[i] * y[k - i];
        r[k] = acc;
      }
      return r;
    },
    div: function (x, y) {
      var q = [0, 0, 0, 0];
      for (var k = 0; k < K; k++) {
        var acc = x[k];
        for (var i = 1; i <= k; i++) acc -= y[i] * q[k - i];
        q[k] = acc / y[0];
      }
      return q;
    },
    deriv: function (x) { return [x[1], 2 * x[2], 3 * x[3], 0]; },
    exp: function (x) {
      var e = [Math.exp(x[0]), 0, 0, 0];
      for (var k = 1; k < K; k++) {
        var acc = 0;
        for (var j = 1; j <= k; j++) acc += j * x[j] * e[k - j];
        e[k] = acc / k;
      }
      return e;
    },
    log: function (x) {
      var l = [Math.log(x[0]), 0, 0, 0];
      for (var k = 1; k < K; k++) {
        var acc = x[k];
        for (var j = 1; j < k; j++) acc -= (j * l[j] * x[k - j]) / k;
        l[k] = acc / x[0];
      }
      return l;
    },
    sincos: function (x) {
      var s = [Math.sin(x[0]), 0, 0, 0];
      var c = [Math.cos(x[0]), 0, 0, 0];
      for (var k = 1; k < K; k++) {
        var as = 0, ac = 0;
        for (var j = 1; j <= k; j++) { as += j * x[j] * c[k - j]; ac += j * x[j] * s[k - j]; }
        s[k] = as / k;
        c[k] = -ac / k;
      }
      return { s: s, c: c };
    },
    sinhcosh: function (x) {
      var sh = [Math.sinh(x[0]), 0, 0, 0];
      var ch = [Math.cosh(x[0]), 0, 0, 0];
      for (var k = 1; k < K; k++) {
        var as = 0, ac = 0;
        for (var j = 1; j <= k; j++) { as += j * x[j] * ch[k - j]; ac += j * x[j] * sh[k - j]; }
        sh[k] = as / k;
        ch[k] = ac / k;
      }
      return { sh: sh, ch: ch };
    },
    // integrate g = y' (valid to order 2) with y(0) = y0
    integ: function (g, y0) { return [y0, g[0], g[1] / 2, g[2] / 3]; },
    pow: function (x, y) {
      var constExp = y[1] === 0 && y[2] === 0 && y[3] === 0;
      if (constExp && Number.isInteger(y[0]) && Math.abs(y[0]) <= 64) {
        var n = Math.abs(y[0]);
        var r = constJet(1);
        for (var i = 0; i < n; i++) r = J.mul(r, x);
        return y[0] < 0 ? J.div(constJet(1), r) : r;
      }
      return J.exp(J.mul(y, J.log(x)));
    }
  };

  function applyJet(f, x) {
    var one = constJet(1);
    switch (f) {
      case "sin": return J.sincos(x).s;
      case "cos": return J.sincos(x).c;
      case "tan": var sc = J.sincos(x); return J.div(sc.s, sc.c);
      case "exp": return J.exp(x);
      case "log": return J.log(x);
      case "sqrt": return J.pow(x, constJet(0.5));
      case "sinh": return J.sinhcosh(x).sh;
      case "cosh": return J.sinhcosh(x).ch;
      case "tanh": var hc = J.sinhcosh(x); return J.div(hc.sh, hc.ch);
      case "atan": return J.integ(J.div(J.deriv(x), J.add(one, J.mul(x, x))), Math.atan(x[0]));
      case "asin": return J.integ(J.div(J.deriv(x), J.pow(J.sub(one, J.mul(x, x)), constJet(0.5))), Math.asin(x[0]));
      case "acos": return J.integ(J.neg(J.div(J.deriv(x), J.pow(J.sub(one, J.mul(x, x)), constJet(0.5)))), Math.acos(x[0]));
      case "abs": return x[0] < 0 ? J.neg(x) : x.slice();
    }
    throw new Error("bad function " + f);
  }

  /** Evaluate an AST on jets; env maps variable names to jets. */
  function evalJet(ast, env) {
    switch (ast.t) {
      case "num": return constJet(ast.v);
      case "var": return env[ast.n];
      case "neg": return J.neg(evalJet(ast.a, env));
      case "call": return applyJet(ast.f, evalJet(ast.a, env));
      case "bin":
        var x = evalJet(ast.a, env), y = evalJet(ast.b, env);
        switch (ast.op) {
          case "+": return J.add(x, y);
          case "-": return J.sub(x, y);
          case "*": return J.mul(x, y);
          case "/": return J.div(x, y);
          case "^": return J.pow(x, y);
        }
    }
    throw new Error("bad node");
  }

  // --------------------------------------------------------------------- TeX
  var PREC = { "+": 1, "-": 1, "*": 2, "/": 2, "^": 4 };
  function prec(ast) {
    if (ast.t === "bin") return PREC[ast.op];
    if (ast.t === "neg") return 3;
    return 9;
  }
  function paren(ast, min) {
    var s = toTeX(ast);
    return prec(ast) < min ? "\\left(" + s + "\\right)" : s;
  }
  function num(v) {
    if (Number.isInteger(v)) return String(v);
    var s = String(+v.toPrecision(6));
    return s.indexOf("e") >= 0 ? s.replace(/e([+-]?)(\d+)/, "\\cdot 10^{$1$2}") : s;
  }
  function toTeX(ast) {
    switch (ast.t) {
      case "num": return ast.name === "pi" ? "\\pi" : ast.name === "e" ? "e" : num(ast.v);
      case "var": return ast.n;
      case "neg": return "-" + paren(ast.a, 3);
      case "call":
        if (ast.f === "sqrt") return "\\sqrt{" + toTeX(ast.a) + "}";
        if (ast.f === "abs") return "\\left|" + toTeX(ast.a) + "\\right|";
        if (ast.f === "exp") return "e^{" + toTeX(ast.a) + "}";
        if (ast.f === "log") return "\\ln\\left(" + toTeX(ast.a) + "\\right)";
        var nm = { asin: "\\arcsin", acos: "\\arccos", atan: "\\arctan" }[ast.f] || "\\" + ast.f;
        return nm + "\\left(" + toTeX(ast.a) + "\\right)";
      case "bin":
        if (ast.op === "/") return "\\frac{" + toTeX(ast.a) + "}{" + toTeX(ast.b) + "}";
        if (ast.op === "^") return paren(ast.a, 5) + "^{" + toTeX(ast.b) + "}";
        if (ast.op === "*") {
          var implicit = ast.a.t === "num" && (ast.b.t === "var" || ast.b.t === "call" || (ast.b.t === "bin" && ast.b.op === "^"));
          return paren(ast.a, 2) + (implicit ? "\\," : " \\cdot ") + paren(ast.b, 3);
        }
        if (ast.op === "-") return paren(ast.a, 1) + " - " + paren(ast.b, 2);
        return paren(ast.a, 1) + " + " + paren(ast.b, 1);
    }
    return "";
  }

  return {
    FUNCS: FUNCS, VARS: VARS, ExprError: ExprError,
    parse: parse, compile: compile, evalJet: evalJet, toTeX: toTeX, usesVar: usesVar,
    J: J, constJet: constJet, varJet: varJet
  };
});
