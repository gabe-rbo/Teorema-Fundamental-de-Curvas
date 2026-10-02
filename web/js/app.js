/*
 * Interactive panel + gallery. Everything runs in the browser: edits to kappa(s), tau(s),
 * the interval or the sampling recompute the curve (milliseconds) and redraw it.
 *
 * Performance notes
 *  - one recompute per animation frame, however many inputs fire (rAF coalescing);
 *  - typed expressions are parsed once and compiled to plain JS functions;
 *  - the canvas is split in a static layer (curves) and a per-frame layer (apparatus), so
 *    playback and scrubbing never redraw the curves;
 *  - the gallery draws thumbnails lazily, only for cards scrolled into view.
 */
(function () {
  "use strict";
  var Tr = window.Triedro, Expr = Tr.Expr, Eng = Tr.Engine, Viewer = Tr.Viewer, PRESETS = Tr.PRESETS;
  function $(id) { return document.getElementById(id); }

  var DEFAULTS = { k: "2+sin(3*s)", t: "1+0.5*cos(5*s)", s0: 0, s1: 14, n: 700, sub: 2, params: [1, 1, 1], lw: 2.5 };
  var state = JSON.parse(JSON.stringify(DEFAULTS));
  var cache = { k: null, t: null };
  var model = null;           // { ka, ta, data, label }
  var viewer = null;
  var idx = 0, frac = 0, playing = false, speed = 1, lastTs = 0;
  var texK = "", texT = "";
  var SPEEDS = [0.5, 1, 2, 4];

  // ------------------------------------------------------------- small helpers
  function f3(v) { return v === null || v === undefined || !isFinite(v) ? "—" : v.toFixed(3); }
  function inf(v) { return !isFinite(v) ? "—" : v.toFixed(3); }
  function rad(v) { return !isFinite(v) ? "—" : Math.abs(v) < 1e-9 ? "∞" : Math.abs(1 / v).toFixed(3); }
  function vec(A, o, planar) {
    var c = planar ? 2 : 3, out = [];
    for (var i = 0; i < c; i++) out.push(A[o + i].toFixed(planar ? 2 : 3));
    return A[o] !== A[o] ? "—" : "(" + out.join(", ") + ")";
  }
  function setText(id, v) { var el = $(id); if (el.textContent !== v) el.textContent = v; }

  // ----------------------------------------------------------------- TeX
  function renderTexInto(el, tex) {
    if (window.katex) { try { window.katex.render(tex, el, { throwOnError: false }); return; } catch (e) { /* fall through */ } }
    el.textContent = tex;
  }
  function renderTex() {
    if (texK) renderTexInto($("tex-k"), "\\kappa(s) = " + texK);
    if (texT) renderTexInto($("tex-t"), "\\tau(s) = " + texT);
    document.querySelectorAll("[data-tex]").forEach(function (el) { renderTexInto(el, el.getAttribute("data-tex")); });
  }

  // ----------------------------------------------------------------- errors
  var errTimers = {};
  function setFieldError(which, msg) {
    clearTimeout(errTimers[which]);
    var input = $("in-" + which), out = $("err-" + which);
    if (!msg) { out.textContent = ""; input.removeAttribute("aria-invalid"); return; }
    // while typing, show errors only once the user pauses
    errTimers[which] = setTimeout(function () { out.textContent = msg; input.setAttribute("aria-invalid", "true"); }, 550);
  }
  function setCalcError(msg) { $("err-calc").textContent = msg || ""; }

  // ---------------------------------------------------------------- recompute
  var pending = false;
  function schedule() {
    if (pending) return;
    pending = true;
    requestAnimationFrame(function () { pending = false; recompute(); });
  }

  function parseField(which) {
    var src = state[which];
    if (cache[which] === src && cache[which + "f"]) return true;
    try {
      var ast = Expr.parse(src);
      cache[which] = src; cache[which + "ast"] = ast; cache[which + "f"] = Expr.compile(ast);
      if (which === "k") texK = Expr.toTeX(ast); else texT = Expr.toTeX(ast);
      setFieldError(which, "");
      renderTex();
      return true;
    } catch (e) {
      cache[which] = null; cache[which + "f"] = null;
      setFieldError(which, e.message);
      return false;
    }
  }

  function recompute() {
    var okK = parseField("k"), okT = parseField("t");
    if (!okK || !okT) return;                        // keep showing the last valid curve
    if (!(isFinite(state.s0) && isFinite(state.s1) && state.s1 > state.s0)) { setCalcError("O intervalo precisa de s₀ < s₁."); return; }
    var t0 = performance.now(), d;
    try {
      d = Eng.reconstruct({ kf: cache.kf, tf: cache.tf, params: state.params, s0: state.s0, s1: state.s1, n: state.n, sub: state.sub });
    } catch (e) { setCalcError(e.message); return; }
    setCalcError("");
    var ac = Eng.associatedCurves(d);
    d.E = ac.E; d.I = ac.I;
    var label;
    try { label = Eng.classify(cache.kast, cache.tast, state.s0, state.s1, state.params, d.planar); } catch (e) { label = d.planar ? "Curva plana" : "Curva espacial"; }
    var dims = !model || model.data.planar !== d.planar;
    model = { ka: cache.kast, ta: cache.tast, data: d, label: label };
    viewer.setData(d);
    var ms = performance.now() - t0;
    setText("status", d.n + " pontos · " + ms.toFixed(1).replace(".", ",") + " ms");
    if (dims) applyDimensionUi(d.planar);
    setText("badge-class", label);
    setText("badge-dim", d.planar ? "2D" : "3D");
    var slider = $("dock-slider");
    slider.max = d.n - 1;
    setText("dock-smax", "/ " + d.s1.toFixed(3));
    setIndex(Math.round(frac * (d.n - 1)), false);
    scheduleHash();
  }

  // -------------------------------------------------------------- dimension UI
  var TOGGLES = [
    ["curve", "Curva r(s)", ""], ["point", "Ponto ativo", "tf-dot--p"], ["T", "Vetor tangente T", "tf-dot--t"],
    ["N", "Vetor normal N", "tf-dot--n"], ["B", "Vetor binormal B", "tf-dot--b", "3d"],
    ["tline", "Reta tangente", "tf-dot--t"], ["nline", "Reta normal", "tf-dot--n", "2d"],
    ["planes", "Planos osculador, normal e retificante", "tf-dot--b", "3d"],
    ["circle", "Círculo osculador", "tf-dot--p"], ["evolute", "Evoluta E(s)", "tf-dot--e"],
    ["involute", "Involuta I(s)", "tf-dot--i"], ["grid", "Grade e eixos", ""]
  ];
  function buildToggles() {
    var host = $("toggles");
    TOGGLES.forEach(function (t) {
      var lab = document.createElement("label");
      lab.className = "tf-toggle"; lab.dataset.only = t[3] || "";
      lab.innerHTML = '<span class="tf-toggle-left"><span class="tf-dot ' + t[2] + '"></span>' + t[1] +
        '</span><span class="tf-switch"><input type="checkbox" checked aria-label="' + t[1] +
        '"><span class="tf-switch-track"></span></span>';
      lab.querySelector("input").addEventListener("change", function (e) {
        var f = {}; f[t[0]] = e.target.checked; viewer.setShow(f);
      });
      host.appendChild(lab);
    });
  }
  function applyDimensionUi(planar) {
    document.querySelectorAll("#toggles .tf-toggle").forEach(function (l) {
      l.hidden = (l.dataset.only === "3d" && planar) || (l.dataset.only === "2d" && !planar);
    });
    $("row-sigma").hidden = planar; $("row-B").hidden = planar;
    var items = [["", "r(s)"], ["tf-dot--t", "T"], ["tf-dot--n", "N"]];
    if (!planar) items.push(["tf-dot--b", "B"]);
    items.push(["tf-dot--p", "círculo osculador"], ["tf-dot--e", "evoluta"], ["tf-dot--i", "involuta"]);
    $("legend").innerHTML = items.map(function (it) { return '<span><span class="tf-dot ' + it[0] + '"></span>' + it[1] + "</span>"; }).join("");
  }

  // ------------------------------------------------------------------- params
  var PARAM_NAMES = ["a", "b", "c"];
  function buildParams() {
    var host = $("params");
    PARAM_NAMES.forEach(function (name, i) {
      var row = document.createElement("div");
      row.className = "slider-row";
      row.innerHTML = '<span class="name">' + name + '</span><input class="tf-range" type="range" min="-5" max="5" step="0.01" aria-label="Parâmetro ' + name +
        '"><input class="tf-input" type="number" step="any" aria-label="Valor de ' + name + '">';
      var range = row.children[1], num = row.children[2];
      range.addEventListener("input", function () { state.params[i] = parseFloat(range.value); num.value = state.params[i]; schedule(); });
      num.addEventListener("input", function () {
        var v = parseFloat(num.value);
        if (!isFinite(v)) return;
        state.params[i] = v;
        var lim = Math.max(5, Math.ceil(Math.abs(v) * 1.5));
        range.min = -lim; range.max = lim; range.value = v;
        schedule();
      });
      host.appendChild(row);
    });
  }
  function syncParams() {
    var rows = $("params").children;
    for (var i = 0; i < 3; i++) {
      var v = state.params[i], lim = Math.max(5, Math.ceil(Math.abs(v) * 1.5));
      rows[i].children[1].min = -lim; rows[i].children[1].max = lim; rows[i].children[1].value = v;
      rows[i].children[2].value = v;
    }
  }

  function syncInputs() {
    $("in-k").value = state.k; $("in-t").value = state.t;
    $("in-s0").value = state.s0; $("in-s1").value = state.s1;
    $("in-n").value = state.n; setText("out-n", String(state.n));
    $("in-sub").value = String(state.sub);
    $("in-lw").value = state.lw; setText("out-lw", String(state.lw));
    syncParams();
  }

  // ------------------------------------------------------------- index + HUD
  function setIndex(i, fromUser) {
    var d = model && model.data;
    if (!d) return;
    i = Math.max(0, Math.min(d.n - 1, i));
    idx = i;
    if (fromUser !== false) frac = d.n > 1 ? i / (d.n - 1) : 0;
    viewer.setIndex(i);
    var pct = d.n > 1 ? Math.round((i / (d.n - 1)) * 100) : 0;
    $("dock-slider").value = i;
    setText("dock-s", d.s[i].toFixed(3));
    setText("dock-pct", pct + "%");
    $("dock-fill").style.width = pct + "%";
    updateHud();
  }

  function updateHud() {
    var d = model.data, i = idx, o = 3 * i, pl = d.planar;
    var k = d.kappa[i], t = d.tau[i];
    setText("hud-s", d.s[i].toFixed(3));
    setText("hud-r", vec(d.R, o, pl));
    setText("hud-kappa", f3(k));
    setText("hud-tau", pl ? "0.000 (plana)" : f3(t));
    setText("hud-rho", rad(k));
    setText("hud-sigma", rad(t));
    setText("hud-T", vec(d.T, o, pl)); setText("hud-N", vec(d.N, o, pl)); setText("hud-B", vec(d.B, o, false));
    setText("hud-E", vec(d.E, o, pl)); setText("hud-I", vec(d.I, o, pl));
    var v;
    try { v = Eng.associatedInvariants(model.ka, model.ta, d.s[i], d.s1, state.params, pl); }
    catch (e) { v = { kE: NaN, tE: NaN, vE: NaN, kI: NaN, tI: NaN, vI: NaN }; }
    setText("hud-kE", inf(v.kE)); setText("hud-tE", pl ? (isFinite(v.tE) ? "0.000 (plana)" : "—") : inf(v.tE)); setText("hud-vE", inf(v.vE));
    setText("hud-kI", inf(v.kI)); setText("hud-tI", pl ? (isFinite(v.tI) ? "0.000 (plana)" : "—") : inf(v.tI)); setText("hud-vI", inf(v.vI));
  }

  // ----------------------------------------------------------------- playback
  var PLAY_ICON = '<path d="M4.5 2.6v10.8L13 8z"/>', PAUSE_ICON = '<path d="M4 2.8h2.8v10.4H4zM9.2 2.8H12v10.4H9.2z"/>';
  function setPlaying(on) {
    playing = on && !!model;
    $("play-icon").innerHTML = playing ? PAUSE_ICON : PLAY_ICON;
    if (playing) { lastTs = performance.now(); requestAnimationFrame(tick); }
  }
  function tick(ts) {
    if (!playing) return;
    var dt = Math.min(0.1, (ts - lastTs) / 1000); lastTs = ts;
    frac += dt / (14 / speed);          // a full pass takes 14 s at 1x, whatever the number of points
    if (frac > 1) frac -= 1;
    var i = Math.round(frac * (model.data.n - 1));
    if (i !== idx) { var keep = frac; setIndex(i, false); frac = keep; }
    requestAnimationFrame(tick);
  }

  // -------------------------------------------------------------------- hash
  var hashTimer = 0;
  function scheduleHash() { clearTimeout(hashTimer); hashTimer = setTimeout(writeHash, 300); }
  function writeHash() {
    if (currentView() !== "painel") return;
    var q = new URLSearchParams({ k: state.k, t: state.t, s0: state.s0, s1: state.s1, n: state.n, sub: state.sub,
      a: state.params[0], b: state.params[1], c: state.params[2] });
    history.replaceState(null, "", "#/painel?" + q.toString());
  }
  function applyQuery(qs) {
    var q = new URLSearchParams(qs), num = function (key, dflt) { var v = parseFloat(q.get(key)); return isFinite(v) ? v : dflt; };
    if (q.has("k")) state.k = q.get("k");
    if (q.has("t")) state.t = q.get("t");
    state.s0 = num("s0", state.s0); state.s1 = num("s1", state.s1);
    state.n = Math.max(50, Math.min(10000, Math.round(num("n", state.n))));
    state.sub = [1, 2, 4, 8].indexOf(num("sub", state.sub)) >= 0 ? num("sub", state.sub) : state.sub;
    state.params = [num("a", state.params[0]), num("b", state.params[1]), num("c", state.params[2])];
    syncInputs();
  }

  // -------------------------------------------------------------------- views
  function currentView() { return /^#\/galeria/.test(location.hash) ? "galeria" : "painel"; }
  function route() {
    var gal = currentView() === "galeria";
    $("view-painel").hidden = gal; $("view-galeria").hidden = !gal;
    $("nav-painel").setAttribute("aria-current", gal ? "false" : "page");
    $("nav-galeria").setAttribute("aria-current", gal ? "page" : "false");
    document.title = (gal ? "Galeria de curvas" : "Painel interativo") + " — Triedro";
    if (gal) { setPlaying(false); renderVisibleThumbs(); return; }
    var m = /^#\/painel\?(.*)$/.exec(location.hash);
    if (m) applyQuery(m[1]);
    viewer.resize();
    schedule();
  }

  function loadPreset(p) {
    state.k = p.k; state.t = p.t; state.s0 = p.s0; state.s1 = p.s1; state.params = p.params.slice();
    frac = 0; viewer.userMoved = false;
    syncInputs();
    setPlaying(false);
    if (currentView() !== "painel") location.hash = "#/painel"; else schedule();
  }

  // ----------------------------------------------------------------- gallery
  var cards = [];
  function dimOf(p) { return p.t.trim() === "0" ? "2D" : "3D"; }
  function buildGallery() {
    var grid = $("grid");
    PRESETS.forEach(function (p) {
      var card = document.createElement("button");
      card.className = "card"; card.type = "button"; card.dataset.dim = dimOf(p);
      card.setAttribute("aria-label", "Abrir " + p.name + " no painel");
      var tex = function (s) { return s.replace(/\*\*/g, "^").replace(/\*/g, "·").replace(/&/g, "&amp;").replace(/</g, "&lt;"); };
      card.innerHTML = '<div class="cardtop"><span class="tf-badge tf-badge--class">' + (dimOf(p) === "2D" ? "Plana" : "Espacial") + "</span>" +
        '<span class="tf-badge tf-badge--dim">' + dimOf(p) + "</span></div>" +
        '<div class="thumb"><canvas></canvas></div><h2>' + p.name + "</h2>" +
        '<p class="fx">κ(s) = ' + tex(p.k) + "<br>τ(s) = " + tex(p.t) + "<br><span>s ∈ [" + p.s0 + ", " + p.s1 + "]</span></p>" +
        '<p class="note">' + p.note + "</p>";
      card.addEventListener("click", function () { loadPreset(p); });
      grid.appendChild(card);
      cards.push({ el: card, p: p, drawn: false, visible: false });
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var c = cards.filter(function (x) { return x.el === en.target; })[0];
        c.visible = en.isIntersecting;
        if (c.visible && !c.drawn) drawThumb(c);
      });
    }, { rootMargin: "200px" });
    cards.forEach(function (c) { io.observe(c.el); });
    document.querySelectorAll(".chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var f = chip.dataset.filter;
        document.querySelectorAll(".chip").forEach(function (o) { o.setAttribute("aria-pressed", String(o === chip)); });
        cards.forEach(function (c) { c.el.hidden = !(f === "all" || c.el.dataset.dim === f); });
        renderVisibleThumbs();
      });
    });
  }
  function drawThumb(c) {
    try {
      var p = c.p, d = Eng.reconstruct({ kf: Expr.compile(Expr.parse(p.k)), tf: Expr.compile(Expr.parse(p.t)),
        params: p.params, s0: p.s0, s1: p.s1, n: 360, sub: 2 });
      var canvas = c.el.querySelector("canvas");
      Viewer.thumbnail(canvas, d, { lineWidth: 2 });
      c.drawn = true;
    } catch (e) { c.drawn = true; }
  }
  function renderVisibleThumbs() {
    requestAnimationFrame(function () {
      cards.forEach(function (c) {
        if (c.el.hidden) return;
        var r = c.el.getBoundingClientRect(), vis = r.bottom > -200 && r.top < window.innerHeight + 200;
        if (vis && !c.drawn) drawThumb(c);
      });
    });
  }
  $("view-galeria").addEventListener("scroll", renderVisibleThumbs, { passive: true });

  // ------------------------------------------------------------------- theme
  function applyTheme(name) {
    document.documentElement.setAttribute("data-theme", name);
    $("theme-icon").innerHTML = name === "dark"
      ? '<circle cx="8" cy="8" r="2.6"/><path d="M8 1.8v1.6M8 12.6v1.6M1.8 8h1.6M12.6 8h1.6M3.6 3.6l1.1 1.1M11.3 11.3l1.1 1.1M3.6 12.4l1.1-1.1M11.3 4.7l1.1-1.1"/>'
      : '<path d="M13 9.6A5.4 5.4 0 0 1 6.4 3a5.4 5.4 0 1 0 6.6 6.6z"/>';
    try { localStorage.setItem("triedro-theme", name); } catch (e) { /* ignore */ }
    if (viewer) viewer.refreshTheme();
    cards.forEach(function (c) { c.drawn = false; });
    if (currentView() === "galeria") renderVisibleThumbs();
  }

  // -------------------------------------------------------------------- init
  function init() {
    buildToggles(); buildParams(); buildGallery();
    var sel = $("in-preset");
    PRESETS.forEach(function (p) { var o = document.createElement("option"); o.value = p.id; o.textContent = p.name; sel.appendChild(o); });
    sel.addEventListener("change", function () {
      var p = PRESETS.filter(function (x) { return x.id === sel.value; })[0];
      sel.value = ""; if (p) loadPreset(p);
    });

    viewer = new Viewer({ bg: $("cv-bg"), fg: $("cv-fg"),
      onPick: function (i) { setIndex(i, true); },
      onView: function () {} });
    viewer.insetBottom = 96;
    window.addEventListener("resize", function () { viewer.resize(); });
    if (window.ResizeObserver) new ResizeObserver(function () { viewer.resize(); }).observe($("plot-container"));

    $("in-k").addEventListener("input", function (e) { state.k = e.target.value; schedule(); });
    $("in-t").addEventListener("input", function (e) { state.t = e.target.value; schedule(); });
    $("in-s0").addEventListener("input", function (e) { state.s0 = parseFloat(e.target.value); schedule(); });
    $("in-s1").addEventListener("input", function (e) { state.s1 = parseFloat(e.target.value); schedule(); });
    $("in-n").addEventListener("input", function (e) { state.n = parseInt(e.target.value, 10); setText("out-n", String(state.n)); schedule(); });
    $("in-sub").addEventListener("change", function (e) { state.sub = parseInt(e.target.value, 10); schedule(); });
    $("in-lw").addEventListener("input", function (e) { state.lw = parseFloat(e.target.value); setText("out-lw", String(state.lw)); viewer.setLineWidth(state.lw); });

    $("dock-slider").addEventListener("input", function (e) { setIndex(parseInt(e.target.value, 10), true); });
    $("btn-first").addEventListener("click", function () { setIndex(0, true); });
    $("btn-last").addEventListener("click", function () { if (model) setIndex(model.data.n - 1, true); });
    $("btn-prev").addEventListener("click", function () { setIndex(idx - Math.max(1, Math.round(model.data.n / 100)), true); });
    $("btn-next").addEventListener("click", function () { setIndex(idx + Math.max(1, Math.round(model.data.n / 100)), true); });
    $("btn-play").addEventListener("click", function () { setPlaying(!playing); });
    $("btn-speed").addEventListener("click", function (e) {
      speed = SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length]; e.currentTarget.textContent = speed + "×";
    });
    $("btn-fit").addEventListener("click", function () { viewer.resetView(); });
    document.addEventListener("keydown", function (e) {
      if (currentView() !== "painel" || /^(INPUT|SELECT|TEXTAREA|BUTTON)$/.test(e.target.tagName)) return;
      if (e.key === " ") { e.preventDefault(); setPlaying(!playing); }
      else if (e.key === "ArrowRight") setIndex(idx + 1, true);
      else if (e.key === "ArrowLeft") setIndex(idx - 1, true);
    });

    $("theme-toggle-btn").addEventListener("click", function () {
      applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
    });
    function setSidebar(collapsed) {
      $("sidebar").classList.toggle("collapsed", collapsed);
      $("sidebar-expand-btn").style.display = collapsed ? "inline-flex" : "none";
      var start = performance.now();
      (function step(now) { viewer.resize(); if (now - start < 340) requestAnimationFrame(step); })(start);
    }
    $("sidebar-toggle-btn").addEventListener("click", function () { setSidebar(true); });
    $("sidebar-expand-btn").addEventListener("click", function () { setSidebar(false); });

    applyTheme(document.documentElement.getAttribute("data-theme") || "light");
    syncInputs();
    if (window.innerWidth < 860) setSidebar(true);      // phones start with the curve in view
    window.addEventListener("hashchange", route);
    if (!location.hash) history.replaceState(null, "", "#/painel");
    route();
    renderTex();
  }

  Tr.App = { renderTex: renderTex, state: state, get model() { return model; }, get viewer() { return viewer; }, recompute: recompute };
  init();
})();
