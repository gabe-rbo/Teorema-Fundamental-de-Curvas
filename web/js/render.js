/*
 * Lightweight canvas renderer for planar (2D) and spatial (3D) curves.
 *
 * Two stacked canvases keep playback cheap:
 *   bg  grid, axes, curve, evolute, involute (redrawn only when data or view changes)
 *   fg  active point, frame vectors, osculating circle/planes (redrawn every frame)
 * Drawing is driven by requestAnimationFrame with dirty flags; polylines are decimated
 * while the user drags a large curve. No dependencies.
 */
(function (root) {
  "use strict";

  var TAU = Math.PI * 2;
  var COLOR_VARS = ["canvas", "ink", "ink-body", "ink-muted", "rule", "edge", "plot-grid", "plot-axis",
    "curve", "tangent", "normal", "binormal", "point", "evolute", "involute",
    "plane-osculating", "plane-normal", "plane-rectifying"];

  function readColors() {
    var cs = getComputedStyle(document.documentElement);
    var out = {};
    COLOR_VARS.forEach(function (v) { out[v] = cs.getPropertyValue("--" + v).trim() || "#888"; });
    out.font = cs.getPropertyValue("--font-mono").trim() || "monospace";
    return out;
  }

  /** 1-2-5 grid step giving about `target` pixels between lines. */
  function niceStep(unitsPerTarget) {
    var p = Math.pow(10, Math.floor(Math.log10(unitsPerTarget)));
    var m = unitsPerTarget / p;
    return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
  }
  function fmtTick(v, step) {
    if (Math.abs(v) < step * 1e-6) return "0";
    var d = Math.max(0, -Math.floor(Math.log10(step)));
    return v.toFixed(Math.min(d, 6));
  }

  function Viewer(opts) {
    this.bg = opts.bg;
    this.fg = opts.fg || null;
    this.onPick = opts.onPick || function () {};
    this.onView = opts.onView || function () {};
    this.interactive = opts.interactive !== false;
    this.bgx = this.bg.getContext("2d");
    this.fgx = this.fg ? this.fg.getContext("2d") : null;
    this.d = null;            // reconstruction data + E/I
    this.idx = 0;
    this.show = { curve: true, point: true, T: true, N: true, B: true, tline: true, nline: true,
      circle: true, planes: true, evolute: true, involute: true, grid: true };
    this.lineWidth = 2.5;
    this.ortho = false;       // axonometric (parallel) projection: no vanishing point
    this.dirty = { bg: true, fg: true };
    this.raf = 0;
    this.interacting = false;
    this.userMoved = false;
    this.cam2 = { cx: 0, cy: 0, scale: 100 };
    this.cam3 = { yaw: 0.85, pitch: 0.5, dist: 5, tx: 0, ty: 0, tz: 0 };
    this.bounds = null;
    this.colors = readColors();
    this.w = 0; this.h = 0; this.dpr = 1;
    this.insetBottom = 0;     // px reserved for the floating dock
    if (this.interactive && this.fg) this._bindEvents();
    this.resize();
  }

  var P = Viewer.prototype;

  P.refreshTheme = function () { this.colors = readColors(); this.requestDraw(); };

  P.resize = function () {
    var el = this.bg.parentElement;
    var w = Math.max(1, el.clientWidth), h = Math.max(1, el.clientHeight);
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (w === this.w && h === this.h && dpr === this.dpr) return;
    this.w = w; this.h = h; this.dpr = dpr;
    [this.bg, this.fg].forEach(function (c) {
      if (!c) return;
      c.width = Math.round(w * dpr); c.height = Math.round(h * dpr);
      c.style.width = w + "px"; c.style.height = h + "px";
    });
    if (this.d && !this.userMoved) this._fit();
    this.requestDraw();
  };

  P.requestDraw = function (which) {
    if (!which || which === "bg") this.dirty.bg = true;
    if (!which || which === "fg") this.dirty.fg = true;
    if (!this.raf) {
      var self = this;
      this.raf = requestAnimationFrame(function () { self.raf = 0; self._draw(); });
    }
  };

  P.setIndex = function (i) { this.idx = i; this.requestDraw("fg"); };
  P.setShow = function (flags) { for (var k in flags) this.show[k] = flags[k]; this.requestDraw(); };
  P.setLineWidth = function (w) { this.lineWidth = w; this.requestDraw(); };
  P.setOrtho = function (on) { this.ortho = !!on; this.requestDraw(); };

  P.setData = function (d) {
    var was2 = this.d ? this.d.planar : null;
    this.d = d;
    if (this.idx >= d.n) this.idx = d.n - 1;
    this._computeBounds();
    if (was2 !== d.planar) this.userMoved = false;   // switching 2D <-> 3D always refits
    if (!this.userMoved) this._fit();
    this.requestDraw();
  };

  P.resetView = function () { this.userMoved = false; this._fit(); this.onView(false); this.requestDraw(); };

  P._computeBounds = function () {
    var R = this.d.R, n = this.d.n;
    var mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    for (var i = 0; i < n; i++) for (var c = 0; c < 3; c++) {
      var v = R[3 * i + c];
      if (v < mn[c]) mn[c] = v;
      if (v > mx[c]) mx[c] = v;
    }
    var span = Math.max(mx[0] - mn[0], mx[1] - mn[1], this.d.planar ? 0 : mx[2] - mn[2], 1e-6);
    this.bounds = { mn: mn, mx: mx, span: span,
      c: [(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2] };
    this.lvec = Math.min(Math.max(0.12 * span, 1e-6), 5 * span);
  };

  P._fit = function () {
    if (!this.bounds) return;
    var b = this.bounds, w = this.w, h = Math.max(1, this.h - this.insetBottom);
    if (this.d.planar) {
      var dx = Math.max(b.mx[0] - b.mn[0], b.span * 0.05), dy = Math.max(b.mx[1] - b.mn[1], b.span * 0.05);
      this.cam2.scale = Math.min((w * 0.82) / dx, (h * 0.8) / dy);
      this.cam2.cx = b.c[0]; this.cam2.cy = b.c[1];
    } else {
      this._fit3();
    }
  };

  /** Fit the 3D camera to the projected bounding box of the curve (two refinement passes). */
  P._fit3 = function () {
    var b = this.bounds, c = this.cam3, n = this.d.n, R = this.d.R, q = [0, 0, 0];
    var diag = Math.sqrt(Math.pow(b.mx[0] - b.mn[0], 2) + Math.pow(b.mx[1] - b.mn[1], 2) + Math.pow(b.mx[2] - b.mn[2], 2));
    c.dist = (0.55 * diag) / Math.sin(0.31) * 1.2;
    c.tx = b.c[0]; c.ty = b.c[1]; c.tz = b.c[2];
    var availH = Math.max(1, this.h - this.insetBottom), step = Math.max(1, Math.floor(n / 500));
    for (var pass = 0; pass < 3; pass++) {
      this._setupProjection();
      var x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      for (var i = 0; i < n; i += step) {
        var o = 3 * i;
        if (!this._p3(R[o], R[o + 1], R[o + 2], q)) continue;
        if (q[0] < x0) x0 = q[0]; if (q[0] > x1) x1 = q[0];
        if (q[1] < y0) y0 = q[1]; if (q[1] > y1) y1 = q[1];
      }
      if (!(x1 > x0 || y1 > y0)) return;
      var bw = Math.max(x1 - x0, 1), bh = Math.max(y1 - y0, 1);
      var f = Math.min((this.w * 0.78) / bw, (availH * 0.74) / bh);
      // re-center: move the target by the pixel offset of the box centre
      var p = this.pr, k = c.dist / p.focal;
      var dx = ((x0 + x1) / 2 - p.ox) * k, dy = (p.oy - (y0 + y1) / 2) * k;
      c.tx += dx * p.rx + dy * p.ux; c.ty += dx * p.ry + dy * p.uy; c.tz += dx * p.rz + dy * p.uz;
      c.dist = Math.max(b.span * 0.05, Math.min(b.span * 80, c.dist / f));
    }
  };

  // ------------------------------------------------------------- projection
  P._setupProjection = function () {
    var c = this.cam3, cp = Math.cos(c.pitch), sp = Math.sin(c.pitch), cy = Math.cos(c.yaw), sy = Math.sin(c.yaw);
    // camera position on a sphere around the target, z up
    var ex = c.tx + c.dist * cp * cy, ey = c.ty + c.dist * cp * sy, ez = c.tz + c.dist * sp;
    var fx = -cp * cy, fy = -cp * sy, fz = -sp;                 // forward
    var rx = -sy, ry = cy, rz = 0;                               // right = f x up(0,0,1) normalised
    var ux = ry * fz - rz * fy, uy = rz * fx - rx * fz, uz = rx * fy - ry * fx; // up = right x forward... fixed below
    // up = right x forward gives the camera up vector
    ux = ry * fz - rz * fy; uy = rz * fx - rx * fz; uz = rx * fy - ry * fx;
    this.pr = { ex: ex, ey: ey, ez: ez, fx: fx, fy: fy, fz: fz, rx: rx, ry: ry, rz: rz, ux: ux, uy: uy, uz: uz,
      focal: (Math.max(1, this.h - this.insetBottom) / 2) / Math.tan(0.31),
      ortho: this.ortho,
      ox: this.w / 2, oy: Math.max(1, this.h - this.insetBottom) / 2 + 8 };
    // pixels per world unit at the target distance: switching projection keeps the scale
    this.pr.so = this.pr.focal / c.dist;
  };
  /** Project into out = [px, py, depth]. */
  P._p3 = function (x, y, z, out) {
    var p = this.pr, dx = x - p.ex, dy = y - p.ey, dz = z - p.ez;
    var depth = dx * p.fx + dy * p.fy + dz * p.fz;
    if (p.ortho) {
      out[0] = p.ox + (dx * p.rx + dy * p.ry + dz * p.rz) * p.so;
      out[1] = p.oy - (dx * p.ux + dy * p.uy + dz * p.uz) * p.so;
      out[2] = depth;
      return true;
    }
    var f = p.focal / (depth > 1e-9 ? depth : 1e-9);
    out[0] = p.ox + (dx * p.rx + dy * p.ry + dz * p.rz) * f;
    out[1] = p.oy - (dx * p.ux + dy * p.uy + dz * p.uz) * f;
    out[2] = depth;
    return depth > 1e-6;
  };
  P._p2 = function (x, y, out) {
    var c = this.cam2;
    out[0] = this.w / 2 + (x - c.cx) * c.scale;
    out[1] = (this.h - this.insetBottom) / 2 + 6 - (y - c.cy) * c.scale;
    out[2] = 1;
    return true;
  };
  P._proj = function (x, y, z, out) { return this.d.planar ? this._p2(x, y, out) : this._p3(x, y, z, out); };

  // ----------------------------------------------------------------- drawing
  P._draw = function () {
    if (!this.d) return;
    if (this.dirty.bg) { this._drawBg(); this.dirty.bg = false; }
    if (this.dirty.fg && this.fgx) { this._drawFg(); this.dirty.fg = false; }
  };

  P._polyline = function (ctx, A, n, color, width, dash) {
    var cap = this.interacting ? 1500 : 6000;
    var step = Math.max(1, Math.ceil(n / cap));
    var q = [0, 0, 0], pen = false, planar = this.d.planar;
    ctx.beginPath();
    for (var i = 0; i < n; i += step) {
      var o = 3 * i, x = A[o];
      var ok = x === x && this._proj(x, A[o + 1], A[o + 2], q);
      if (!ok) { pen = false; continue; }
      if (pen) ctx.lineTo(q[0], q[1]); else { ctx.moveTo(q[0], q[1]); pen = true; }
    }
    if (step > 1 && n > 1) {          // always finish on the last sample
      var l = 3 * (n - 1);
      if (A[l] === A[l] && this._proj(A[l], A[l + 1], A[l + 2], q) && pen) ctx.lineTo(q[0], q[1]);
    }
    ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineJoin = "round"; ctx.lineCap = "round";
    ctx.setLineDash(dash || []);
    ctx.stroke();
    ctx.setLineDash([]);
  };

  P._drawBg = function () {
    var ctx = this.bgx, col = this.colors;
    ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    ctx.clearRect(0, 0, this.w, this.h);
    if (!this.d.planar) this._setupProjection();
    if (this.show.grid) { if (this.d.planar) this._grid2(ctx); else this._grid3(ctx); }
    var d = this.d, lw = this.lineWidth;
    if (this.show.involute && d.I) this._polyline(ctx, d.I, d.n, col.involute, Math.max(1.4, lw * 0.7));
    if (this.show.evolute && d.E) this._polyline(ctx, d.E, d.n, col.evolute, Math.max(1.4, lw * 0.7));
    if (this.show.curve) this._polyline(ctx, d.R, d.n, col.curve, lw + 0.5);
  };

  P._grid2 = function (ctx) {
    var c = this.cam2, col = this.colors, w = this.w, h = this.h;
    var step = niceStep(90 / c.scale);
    var x0 = c.cx - (w / 2) / c.scale, x1 = c.cx + (w / 2) / c.scale;
    var cyp = (h - this.insetBottom) / 2 + 6;
    var y0 = c.cy - (h - cyp) / c.scale, y1 = c.cy + cyp / c.scale;
    var q = [0, 0, 0];
    ctx.lineWidth = 1; ctx.font = "11px " + col.font; ctx.fillStyle = col["ink-muted"];
    ctx.strokeStyle = col["plot-grid"];
    ctx.beginPath();
    var i;
    for (i = Math.ceil(x0 / step); i * step <= x1; i++) { this._p2(i * step, 0, q); ctx.moveTo(Math.round(q[0]) + 0.5, 0); ctx.lineTo(Math.round(q[0]) + 0.5, h); }
    for (i = Math.ceil(y0 / step); i * step <= y1; i++) { this._p2(0, i * step, q); ctx.moveTo(0, Math.round(q[1]) + 0.5); ctx.lineTo(w, Math.round(q[1]) + 0.5); }
    ctx.stroke();
    ctx.strokeStyle = col["plot-axis"];
    ctx.beginPath();
    this._p2(0, 0, q);
    if (q[0] > 0 && q[0] < w) { ctx.moveTo(Math.round(q[0]) + 0.5, 0); ctx.lineTo(Math.round(q[0]) + 0.5, h); }
    if (q[1] > 0 && q[1] < h) { ctx.moveTo(0, Math.round(q[1]) + 0.5); ctx.lineTo(w, Math.round(q[1]) + 0.5); }
    ctx.stroke();
    var by = h - this.insetBottom - 6;
    ctx.textAlign = "center"; ctx.textBaseline = "bottom";
    for (i = Math.ceil(x0 / step); i * step <= x1; i++) { this._p2(i * step, 0, q); if (q[0] > 24 && q[0] < w - 24) ctx.fillText(fmtTick(i * step, step), q[0], by); }
    ctx.textAlign = "left"; ctx.textBaseline = "middle";
    for (i = Math.ceil(y0 / step); i * step <= y1; i++) { this._p2(0, i * step, q); if (q[1] > 14 && q[1] < by - 14) ctx.fillText(fmtTick(i * step, step), 8, q[1]); }
  };

  P._grid3 = function (ctx) {
    var b = this.bounds, col = this.colors, H = b.span * 0.62;
    var cx = b.c[0], cy = b.c[1], cz = b.c[2];
    var x0 = cx - H, x1 = cx + H, y0 = cy - H, y1 = cy + H, z0 = cz - H, z1 = cz + H;
    var step = niceStep((2 * H) / 6);
    var q = [0, 0, 0], r = [0, 0, 0], self = this;
    function seg(ax, ay, az, bx, by, bz) {
      if (self._p3(ax, ay, az, q) && self._p3(bx, by, bz, r)) { ctx.moveTo(q[0], q[1]); ctx.lineTo(r[0], r[1]); }
    }
    ctx.lineWidth = 1;
    ctx.strokeStyle = col["plot-grid"];
    ctx.beginPath();
    var i;
    for (i = Math.ceil(x0 / step); i * step <= x1; i++) seg(i * step, y0, z0, i * step, y1, z0);
    for (i = Math.ceil(y0 / step); i * step <= y1; i++) seg(x0, i * step, z0, x1, i * step, z0);
    ctx.stroke();
    ctx.strokeStyle = col["plot-axis"];
    ctx.beginPath();
    seg(x0, y0, z0, x1, y0, z0); seg(x1, y0, z0, x1, y1, z0); seg(x1, y1, z0, x0, y1, z0); seg(x0, y1, z0, x0, y0, z0);
    seg(x0, y0, z1, x1, y0, z1); seg(x1, y0, z1, x1, y1, z1); seg(x1, y1, z1, x0, y1, z1); seg(x0, y1, z1, x0, y0, z1);
    seg(x0, y0, z0, x0, y0, z1); seg(x1, y0, z0, x1, y0, z1); seg(x1, y1, z0, x1, y1, z1); seg(x0, y1, z0, x0, y1, z1);
    ctx.stroke();
    // tick labels on the bottom edges nearest to the viewer
    var p = this.pr, fy = p.ey > cy ? y1 : y0, fx = p.ex > cx ? x1 : x0;
    ctx.font = "11px " + col.font; ctx.fillStyle = col["ink-muted"]; ctx.textAlign = "center"; ctx.textBaseline = "top";
    var off = H * 0.06;
    for (i = Math.ceil(x0 / step); i * step <= x1; i++) if (this._p3(i * step, fy + (fy > cy ? off : -off), z0, q)) ctx.fillText(fmtTick(i * step, step), q[0], q[1]);
    for (i = Math.ceil(y0 / step); i * step <= y1; i++) if (this._p3(fx + (fx > cx ? off : -off), i * step, z0, q)) ctx.fillText(fmtTick(i * step, step), q[0], q[1]);
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    for (i = Math.ceil(z0 / step); i * step <= z1; i++) if (this._p3(fx, fy, i * step, q)) ctx.fillText(fmtTick(i * step, step), q[0] - 8, q[1]);
    ctx.fillStyle = col["ink-body"]; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.font = "italic 13px " + (getComputedStyle(document.documentElement).getPropertyValue("--font-display") || "serif");
    if (this._p3((x0 + x1) / 2, fy + (fy > cy ? 3.2 * off : -3.2 * off), z0, q)) ctx.fillText("x", q[0], q[1]);
    if (this._p3(fx + (fx > cx ? 3.2 * off : -3.2 * off), (y0 + y1) / 2, z0, q)) ctx.fillText("y", q[0], q[1]);
    if (this._p3(fx, fy, z1 + off * 2, q)) ctx.fillText("z", q[0] - 10, q[1]);
  };

  P._arrow = function (ctx, ax, ay, bx, by, color, width) {
    var dx = bx - ax, dy = by - ay, len = Math.sqrt(dx * dx + dy * dy);
    if (len < 2) return;
    var ux = dx / len, uy = dy / len, head = Math.min(10, len * 0.5);
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = width; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx - ux * head * 0.6, by - uy * head * 0.6); ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(bx, by);
    ctx.lineTo(bx - ux * head - uy * head * 0.45, by - uy * head + ux * head * 0.45);
    ctx.lineTo(bx - ux * head + uy * head * 0.45, by - uy * head - ux * head * 0.45);
    ctx.closePath(); ctx.fill();
  };

  P._drawFg = function () {
    var ctx = this.fgx, d = this.d, col = this.colors, sh = this.show, i = this.idx, o = 3 * i;
    ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    ctx.clearRect(0, 0, this.w, this.h);
    var planar = d.planar, L = this.lvec, span = this.bounds.span;
    var P0 = [d.R[o], d.R[o + 1], d.R[o + 2]];
    var T = [d.T[o], d.T[o + 1], d.T[o + 2]], N = [d.N[o], d.N[o + 1], d.N[o + 2]], Bv = [d.B[o], d.B[o + 1], d.B[o + 2]];
    var k = d.kappa[i];
    var q = [0, 0, 0], r = [0, 0, 0], self = this, lw = this.lineWidth;
    if (!planar) this._setupProjection();
    function pr(v, out) { return self._proj(v[0], v[1], v[2], out); }
    function at(base, dir, t) { return [base[0] + dir[0] * t, base[1] + dir[1] * t, base[2] + dir[2] * t]; }

    // translucent frame planes (3D)
    if (!planar && sh.planes) {
      var W = 1.2 * L;
      var quads = [[T, N, col["plane-osculating"]], [N, Bv, col["plane-normal"]], [T, Bv, col["plane-rectifying"]]];
      for (var qi = 0; qi < 3; qi++) {
        var a = quads[qi][0], b = quads[qi][1], pts = [[-1, -1], [1, -1], [1, 1], [-1, 1]], ok = true;
        ctx.beginPath();
        for (var m = 0; m < 4; m++) {
          var c = [P0[0] + W * (pts[m][0] * a[0] + pts[m][1] * b[0]), P0[1] + W * (pts[m][0] * a[1] + pts[m][1] * b[1]), P0[2] + W * (pts[m][0] * a[2] + pts[m][1] * b[2])];
          if (!pr(c, q)) ok = false;
          if (m === 0) ctx.moveTo(q[0], q[1]); else ctx.lineTo(q[0], q[1]);
        }
        ctx.closePath();
        if (ok) { ctx.fillStyle = quads[qi][2]; ctx.fill(); }
      }
    }
    // osculating circle
    if (sh.circle && Math.abs(k) > 1e-6) {
      var rho = 1 / Math.abs(k);
      {
        var ctr = at(P0, N, 1 / k);
        ctx.beginPath();
        for (var s2 = 0; s2 <= 72; s2++) {
          var th = (s2 / 72) * TAU, ct = Math.cos(th), st = Math.sin(th);
          var cp = [ctr[0] - (1 / k) * N[0] * ct + rho * T[0] * st, ctr[1] - (1 / k) * N[1] * ct + rho * T[1] * st, ctr[2] - (1 / k) * N[2] * ct + rho * T[2] * st];
          if (pr(cp, q)) { if (s2 === 0) ctx.moveTo(q[0], q[1]); else ctx.lineTo(q[0], q[1]); }
        }
        ctx.strokeStyle = col.point; ctx.lineWidth = Math.max(1.4, lw * 0.7); ctx.stroke();
        if (pr(ctr, q) && (d.E && d.E[o] === d.E[o])) {   // center of curvature = evolute point
          ctx.fillStyle = col.evolute; ctx.beginPath(); ctx.arc(q[0], q[1], 3.5, 0, TAU); ctx.fill();
        }
      }
    }
    // tangent / normal lines (dashed)
    ctx.setLineDash([6, 5]);
    if (sh.tline) this._seg(ctx, at(P0, T, -2 * L), at(P0, T, 2 * L), col.tangent, 1.4, 0.55);
    if (sh.nline && planar) this._seg(ctx, at(P0, N, -2 * L), at(P0, N, 2 * L), col.normal, 1.4, 0.55);
    ctx.setLineDash([]);
    // involute point
    if (sh.involute && d.I && pr([d.I[o], d.I[o + 1], d.I[o + 2]], q)) {
      ctx.fillStyle = col.involute; ctx.beginPath(); ctx.arc(q[0], q[1], 3.5, 0, TAU); ctx.fill();
    }
    // frame arrows
    if (!pr(P0, q)) return;
    var qx = q[0], qy = q[1];
    var vecs = [["T", T, col.tangent], ["N", N, col.normal]];
    if (!planar) vecs.push(["B", Bv, col.binormal]);
    for (var v = 0; v < vecs.length; v++) {
      if (!sh[vecs[v][0]]) continue;
      if (pr(at(P0, vecs[v][1], L), r)) this._arrow(ctx, qx, qy, r[0], r[1], vecs[v][2], Math.max(2, lw));
    }
    if (sh.point) {
      ctx.beginPath(); ctx.arc(qx, qy, 6, 0, TAU);
      ctx.fillStyle = col.point; ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = col.canvas; ctx.stroke();
    }
  };

  P._seg = function (ctx, a, b, color, width, alpha) {
    var q = [0, 0, 0], r = [0, 0, 0];
    if (!this._proj(a[0], a[1], a[2], q) || !this._proj(b[0], b[1], b[2], r)) return;
    ctx.globalAlpha = alpha; ctx.strokeStyle = color; ctx.lineWidth = width;
    ctx.beginPath(); ctx.moveTo(q[0], q[1]); ctx.lineTo(r[0], r[1]); ctx.stroke();
    ctx.globalAlpha = 1;
  };

  // ------------------------------------------------------------- picking
  P.pick = function (px, py) {
    var d = this.d, q = [0, 0, 0], best = -1, bd = 14 * 14;
    if (!d.planar) this._setupProjection();
    for (var i = 0; i < d.n; i++) {
      var o = 3 * i;
      if (!this._proj(d.R[o], d.R[o + 1], d.R[o + 2], q)) continue;
      var dx = q[0] - px, dy = q[1] - py, dd = dx * dx + dy * dy;
      if (dd < bd) { bd = dd; best = i; }
    }
    return best;
  };

  // ------------------------------------------------------------- interaction
  P._bindEvents = function () {
    var self = this, el = this.fg, ptrs = {}, last = null, moved = 0, startX = 0, startY = 0, pinch = 0;
    el.style.touchAction = "none";
    el.addEventListener("contextmenu", function (e) { e.preventDefault(); });

    function touch() { self.userMoved = true; self.onView(true); }

    el.addEventListener("pointerdown", function (e) {
      el.setPointerCapture(e.pointerId);
      ptrs[e.pointerId] = { x: e.clientX, y: e.clientY };
      last = { x: e.clientX, y: e.clientY };
      startX = e.clientX; startY = e.clientY; moved = 0;
      self.interacting = true;
      var ids = Object.keys(ptrs);
      if (ids.length === 2) { var a = ptrs[ids[0]], b = ptrs[ids[1]]; pinch = Math.hypot(a.x - b.x, a.y - b.y); }
    });
    el.addEventListener("pointermove", function (e) {
      if (!ptrs[e.pointerId]) return;
      ptrs[e.pointerId] = { x: e.clientX, y: e.clientY };
      var ids = Object.keys(ptrs);
      if (ids.length === 2) {
        var a = ptrs[ids[0]], b = ptrs[ids[1]], dist = Math.hypot(a.x - b.x, a.y - b.y);
        if (pinch > 0) self._zoom(pinch / dist, (a.x + b.x) / 2, (a.y + b.y) / 2);
        pinch = dist; moved = 99; touch();
        return;
      }
      var dx = e.clientX - last.x, dy = e.clientY - last.y;
      last = { x: e.clientX, y: e.clientY };
      moved += Math.abs(dx) + Math.abs(dy);
      if (moved < 4 && Math.hypot(e.clientX - startX, e.clientY - startY) < 4) return;
      var pan = e.shiftKey || (e.buttons & 2) || (e.buttons & 4);
      if (self.d.planar || pan) self._pan(dx, dy);
      else { var c = self.cam3; c.yaw -= dx * 0.008; c.pitch = Math.max(-1.5, Math.min(1.5, c.pitch + dy * 0.008)); }
      touch();
      self.requestDraw();
    });
    function up(e) {
      var wasClick = moved < 4;
      delete ptrs[e.pointerId];
      pinch = 0;
      if (!Object.keys(ptrs).length) {
        self.interacting = false;
        self.requestDraw("bg");
        if (wasClick && e.type === "pointerup") {
          var rect = el.getBoundingClientRect();
          var i = self.pick(e.clientX - rect.left, e.clientY - rect.top);
          if (i >= 0) self.onPick(i);
        }
      }
    }
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    el.addEventListener("wheel", function (e) {
      e.preventDefault();
      var rect = el.getBoundingClientRect();
      self._zoom(Math.exp(e.deltaY * (e.deltaMode ? 0.05 : 0.0016)), e.clientX - rect.left, e.clientY - rect.top);
      touch();
      self.interacting = true;
      clearTimeout(self._wheelT);
      self._wheelT = setTimeout(function () { self.interacting = false; self.requestDraw("bg"); }, 160);
    }, { passive: false });
    el.addEventListener("dblclick", function () { self.resetView(); });
  };

  P._pan = function (dx, dy) {
    if (this.d.planar) { this.cam2.cx -= dx / this.cam2.scale; this.cam2.cy += dy / this.cam2.scale; return; }
    var c = this.cam3, f = (2 * c.dist * Math.tan(0.31)) / Math.max(1, this.h);
    var p = this.pr || (this._setupProjection(), this.pr);
    c.tx -= (dx * p.rx - dy * p.ux) * f; c.ty -= (dx * p.ry - dy * p.uy) * f; c.tz -= (dx * p.rz - dy * p.uz) * f;
  };

  P._zoom = function (factor, px, py) {
    if (this.d.planar) {
      var c = this.cam2, q = [0, 0, 0];
      var wx = c.cx + (px - this.w / 2) / c.scale, wy = c.cy - (py - ((this.h - this.insetBottom) / 2 + 6)) / c.scale;
      c.scale = Math.max(1e-6, Math.min(1e9, c.scale / factor));
      c.cx = wx - (px - this.w / 2) / c.scale; c.cy = wy + (py - ((this.h - this.insetBottom) / 2 + 6)) / c.scale;
    } else {
      this.cam3.dist = Math.max(this.bounds.span * 0.05, Math.min(this.bounds.span * 80, this.cam3.dist * factor));
    }
    this.requestDraw();
  };

  /** Draw a small static preview (gallery thumbnails): curve only, default view. */
  Viewer.thumbnail = function (canvas, d, opts) {
    var v = new Viewer({ bg: canvas, interactive: false });
    v.show.grid = false; v.lineWidth = (opts && opts.lineWidth) || 2;
    v.setData(d);
    v._draw();
    return v;
  };

  root.Triedro = root.Triedro || {};
  root.Triedro.Viewer = Viewer;
})(typeof self !== "undefined" ? self : this);
