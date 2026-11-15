/* The shapes the Tessel cloud can take. Each shape returns one point [x, y, z] inside a box of about -0.5 to 0.5,
   or null to try again. TesselShapes.sample(name, count) gives a flat list of points for a shape. */
  function rnd(a, b) { return a + Math.random() * (b - a); }

  /* ---- a brain: two hemispheres with a groove between them and folds across the surface, a lobe underneath
     on each side, a ridged cerebellum at the back and a brainstem. Front is to the left. ---- */
  function unit() { var z = Math.random() * 2 - 1, a = Math.random() * 6.283, r = Math.sqrt(1 - z * z); return [r * Math.cos(a), z, r * Math.sin(a)]; }
  function folds(x, y, z) { var g = Math.sin(22 * x + 4 * Math.sin(12 * y + 7 * z) + 3 * Math.sin(10 * z)); return .08 + .92 * Math.exp(-g * g * 9); }
  function brain(scale) {
    var r = Math.random(), u = unit(), x, y, z, keep;
    if (r < .66) {                                   /* the two hemispheres: rounded on top, flatter underneath */
      x = u[0] * .40; y = (u[1] > 0 ? u[1] * .55 : u[1]) * .28 - .05; z = u[2] * .29;
      z += (z < 0 ? -1 : 1) * .012;                  /* the groove down the middle */
      keep = folds(x, y, z);
    } else if (r < .80) {                            /* a lobe underneath on each side */
      var side = Math.random() < .5 ? -1 : 1;
      x = -.07 + u[0] * .17; y = .13 + u[1] * .065; z = side * .14 + u[2] * .09;
      keep = folds(x * 1.3, y * 1.3, z * 1.3);
    } else if (r < .92) {                            /* the cerebellum, with strong fine ridges */
      x = .26 + u[0] * .14; y = .15 + u[1] * .095; z = u[2] * .16;
      var g = Math.sin(y * 110); keep = .1 + .9 * Math.exp(-g * g * 6);
    } else {                                         /* the brainstem: short and slim */
      var h = Math.random(), t = Math.random() * 6.283;
      x = .09 + h * .05 + .022 * Math.cos(t); y = .12 + h * .17; z = .022 * Math.sin(t); keep = 1;
    }
    if (Math.random() > keep) return null;
    return [x * scale, y * scale, z * scale];
  }

  /* ---- a padlock: a solid body and a curved shackle ---- */
  function padlock() {
    var r = Math.random();
    if (r < .6) {
      var hx = .26, hy = .17, hz = .12, cy = .14, ax = hy * hz, ay = hx * hz, az = hx * hy, t = Math.random() * (ax + ay + az), x, y, z;
      if (t < ax) { x = Math.random() < .5 ? -hx : hx; y = rnd(-hy, hy); z = rnd(-hz, hz); }
      else if (t < ax + ay) { y = Math.random() < .5 ? -hy : hy; x = rnd(-hx, hx); z = rnd(-hz, hz); }
      else { z = Math.random() < .5 ? -hz : hz; x = rnd(-hx, hx); y = rnd(-hy, hy); }
      return [x, y + cy, z];
    }
    var R = .15, tube = .018, ox, oy, oz;
    var v = [rnd(-1, 1), rnd(-1, 1), rnd(-1, 1)], l = Math.hypot(v[0], v[1], v[2]) || 1;
    ox = v[0] / l * tube; oy = v[1] / l * tube; oz = v[2] / l * tube;
    if (r < .85) { var a = Math.random() * Math.PI; return [R * Math.cos(a) + ox, -.11 - R * Math.sin(a) + oy, oz]; }
    return [(Math.random() < .5 ? -R : R) + ox, rnd(-.11, -.03) + oy, oz];
  }

  /* ---- a key: a round bow with a hole, a straight shaft and three teeth. Drawn upright, then tilted. ---- */
  function key() {
    var r = Math.random(), x, y, z = rnd(-.02, .02), t;
    if (r < .38) {                                   /* the bow: a ring */
      t = Math.random() * 6.283; x = .085 * Math.cos(t) + rnd(-.012, .012); y = -.2 + .085 * Math.sin(t) + rnd(-.012, .012);
    } else if (r < .72) {                            /* the shaft */
      x = rnd(-.02, .02); y = rnd(-.115, .28);
    } else {                                         /* three teeth, stepping out to one side */
      var k = (Math.random() * 3) | 0, len = k === 1 ? .14 : .1;
      y = .26 - k * .09 + rnd(-.02, .02); x = rnd(0, len);
      if (Math.random() < .25) { x = len; y = .26 - k * .09 + rnd(-.04, .04); }
    }
    var tilt = .42, c = Math.cos(tilt), sn = Math.sin(tilt), size = .7;   /* the key is drawn at 70% of its first size */
    return [.31 + (x * c - y * sn) * size, .02 + (x * sn + y * c) * size, z * size];
  }

  /* ---- a padlock with a key beside it: the privacy scene ---- */
  function lockAndKey() {
    if (Math.random() < .27) return key();
    var p = padlock();
    if (!p) return null;
    return [p[0] * .8 - .2, p[1] * .8 - .02, p[2] * .8];
  }

  function ring() { var a = Math.random() * 6.283, r = .36 + rnd(-.04, .04); return [r * Math.cos(a), r * Math.sin(a), rnd(-.06, .06)]; }
  function grid() {
    var cw = .17, gap = .06, i = (Math.random() * 4) | 0, j = (Math.random() * 3) | 0, cx = (i - 1.5) * (cw + gap), cy = (j - 1) * (cw + gap), side = (Math.random() * 4) | 0, t = rnd(-cw / 2, cw / 2), h = cw / 2;
    var p = side === 0 ? [t, -h] : side === 1 ? [h, t] : side === 2 ? [t, h] : [-h, t];
    return [cx + p[0], cy + p[1], rnd(-.02, .02)];
  }
  var NET = (function () {
    var s = 7, nodes = [], edges = [], i, v;
    function r() { s = (s * 16807) % 2147483647; return s / 2147483647; }
    for (i = 0; i < 16; i++) { do { v = [r() - .5, r() - .5, (r() - .5) * .6]; } while (Math.hypot(v[0], v[1], v[2] * 1.6) > .44); nodes.push(v); }
    nodes.forEach(function (a, i) {
      var d = nodes.map(function (b, j) { return [j, Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2])]; }).filter(function (x) { return x[0] !== i; }).sort(function (p, q) { return p[1] - q[1]; });
      edges.push([i, d[0][0]]); edges.push([i, d[1][0]]); edges.push([i, d[2][0]]);
    });
    return { nodes: nodes, edges: edges };
  })();
  function network() {
    if (Math.random() < .3) { var n = NET.nodes[(Math.random() * NET.nodes.length) | 0]; return [n[0] + rnd(-.035, .035), n[1] + rnd(-.035, .035), n[2] + rnd(-.035, .035)]; }
    var e = NET.edges[(Math.random() * NET.edges.length) | 0], a = NET.nodes[e[0]], b = NET.nodes[e[1]], t = Math.random();
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
  }
  function scatter() { return [rnd(-1.1, 1.1), rnd(-.9, .9), rnd(-.8, .8)]; }
  var GEN = {
    "brain": function () { return brain(1); }, "brain-s": function () { return brain(.78); },
    "padlock": lockAndKey, "ring": ring, "grid": grid, "network": network, "scatter": scatter
  };
export const TesselShapes = {
    sample: function (name, count) {
      var arr = new Float32Array(count * 3), gen = GEN[name];
      for (var i = 0; i < count; i++) { var p = null, tries = 0; while (!p && tries++ < 500) p = gen(); p = p || [0, 0, 0]; arr[i * 3] = p[0]; arr[i * 3 + 1] = p[1]; arr[i * 3 + 2] = p[2]; }
      return arr;
    }
  };
