/* The Tessel cloud: one set of triangles drawn on a fixed canvas.
   Scroll position picks which shape it forms; between shapes the same triangles break apart and rebuild.
   startCloud() returns a function that stops everything, so React can mount and unmount it cleanly. */
import { TesselShapes } from "./shapes.js";
import { position } from "./transitions.js";
import { createSignals } from "./signals.js";
import { STOP_SHAPES, stopUnit } from "./stops.js";

const COLORS = ["#8052ff", "#ffb829", "#15846e", "#d94fd0", "#4f8dff"];
/* where the cloud sits at each stop: [centre x, centre y, size, widest as a share of the width, tallest as a share of the height], as fractions of the screen */
const RECT_DESKTOP = [[.72, .5, .9, .6, 1], [.29, .52, .8, .56, 1], [.5, .5, .94, .72, 1], [.29, .5, .8, .56, 1], [.5, .34, .55, 1, 1]];
const RECT_PHONE = [[.5, .27, .85, 1, .5], [.5, .3, 1, 1, .56], [.5, .5, 1.2, 1.2, .64], [.5, .23, .9, 1, .4], [.5, .26, .7, 1, .4]];
const LAST = STOP_SHAPES.length - 1;

const rnd = (a, b) => a + Math.random() * (b - a);
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

/* The stagger transitions release triangles in index order, so the points of the shapes they join are put in an order
   that makes the release read as a sweep: the ring by angle around its centre, the grid left to right. */
function sortPoints(arr, name) {
  const n = arr.length / 3, key = [];
  if (name === "ring") for (let k = 0; k < n; k++) key.push(Math.atan2(arr[k * 3 + 1], arr[k * 3]));
  else if (name === "grid") for (let k = 0; k < n; k++) key.push(arr[k * 3] + arr[k * 3 + 1] * .001);
  else return arr;
  const order = key.map((_, k) => k).sort((p, q) => key[p] - key[q]), out = new Float32Array(arr.length);
  order.forEach((from, to) => { out[to * 3] = arr[from * 3]; out[to * 3 + 1] = arr[from * 3 + 1]; out[to * 3 + 2] = arr[from * 3 + 2]; });
  return out;
}

function tri(ctx, x, y, s, rot) {
  ctx.moveTo(x + Math.cos(rot) * s, y + Math.sin(rot) * s);
  ctx.lineTo(x + Math.cos(rot + 2.094) * s, y + Math.sin(rot + 2.094) * s);
  ctx.lineTo(x + Math.cos(rot + 4.189) * s, y + Math.sin(rot + 4.189) * s);
  ctx.closePath();
}

/* faint triangles drifting behind the whole page */
function startAmbient(canvas, dpr, reduced) {
  const g = canvas.getContext("2d");
  let w, h, items = [], raf = 0;
  function size() {
    w = window.innerWidth; h = window.innerHeight;
    canvas.width = w * dpr; canvas.height = h * dpr; items = [];
    const n = w < 700 ? 18 : 36;
    for (let i = 0; i < n; i++) {
      items.push({ x: Math.random() * w, y: Math.random() * h, vx: rnd(-.06, .06), vy: rnd(-.06, .06), s: 6 + Math.random() * 12, r: Math.random() * 6.283, vr: rnd(-.001, .001), c: COLORS[(Math.random() * COLORS.length) | 0] });
    }
  }
  function draw() {
    g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, h); g.globalAlpha = .16; g.lineWidth = 1;
    const still = reduced.matches;
    for (const a of items) {
      if (!still) {
        a.x += a.vx; a.y += a.vy; a.r += a.vr;
        if (a.x < -30) a.x = w + 30; if (a.x > w + 30) a.x = -30;
        if (a.y < -30) a.y = h + 30; if (a.y > h + 30) a.y = -30;
      }
      g.beginPath(); g.strokeStyle = a.c; tri(g, a.x, a.y, a.s, a.r); g.stroke();
    }
    raf = requestAnimationFrame(draw);
  }
  size(); window.addEventListener("resize", size); draw();
  return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", size); };
}

export function startCloud(canvas, ambientCanvas) {
  const ctx = canvas.getContext("2d");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const stopAmbient = startAmbient(ambientCanvas, dpr, reduced);
  let W, H, phone, unit, raf = 0;

  function resize() {
    W = window.innerWidth; H = window.innerHeight; phone = W <= 900;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    unit = stopUnit();
    RECT_DESKTOP[0][0] = clamp(.72 - (W - 1000) / 400 * .06, .66, .72); /* the brain sits a little nearer the middle on wide screens */
  }
  resize(); window.addEventListener("resize", resize);

  const N = phone ? 1200 : 3200;
  const shapes = STOP_SHAPES.map((n) => sortPoints(TesselShapes.sample(n, N), n));
  const scatter = TesselShapes.sample("scatter", N);
  const P = [];
  for (let i = 0; i < N; i++) {
    P.push({ s: 1.8 + Math.random() * 2.4, r: Math.random() * 6.283, c: (Math.random() * COLORS.length) | 0, ph: Math.random() * 6.283, d: Math.random() * .35, w: [rnd(-1, 1), rnd(-1, 1), rnd(-1, 1)], i: i / N });
  }
  const brainSignals = createSignals(shapes[0]);
  const motionPoint = { x: 0, y: 0, z: 0, spin: 0 };
  const frameInfo = { ca: [0, 0], g: [0, 0] };
  const rectSide = (r) => Math.min(r[2] * Math.min(W, H), r[3] * W, r[4] * H);
  let t0 = null, yawBase = 0, pitch = 0, vYaw = 0, vPitch = 0, lean = 0, leanT = 0, dragging = false, last = null;

  function frame(now) {
    const still = reduced.matches;
    const p = clamp(window.scrollY / unit, 0, LAST);
    const i = Math.min(LAST - 1, Math.floor(p)), u = p - i;
    const m = still ? (u < .5 ? 0 : 1) : u;
    const R = phone ? RECT_PHONE : RECT_DESKTOP, ra = R[i], rb = R[i + 1];
    const cx = (ra[0] + (rb[0] - ra[0]) * m) * W, cy = (ra[1] + (rb[1] - ra[1]) * m) * H;
    const lerp = (k) => ra[k] + (rb[k] - ra[k]) * m;
    const side = Math.min(lerp(2) * Math.min(W, H), lerp(3) * W, lerp(4) * H);
    if (t0 === null) t0 = now;
    const A = shapes[i], B = shapes[i + 1], D = side * 2.4, Zr = side * .3;
    /* where the two shapes sit and where the screen centre is, measured in the current frame (units of the current size) */
    const sa = rectSide(ra) / side, sb = rectSide(rb) / side;
    const oax = (ra[0] * W - cx) / side, oay = (ra[1] * H - cy) / side, obx = (rb[0] * W - cx) / side, oby = (rb[1] * H - cy) / side;
    frameInfo.ca[0] = oax; frameInfo.ca[1] = oay;
    frameInfo.g[0] = (W / 2 - cx) / side; frameInfo.g[1] = (H / 2 - cy) / side;
    const anchored = i > 1;
    const brainWeight = still ? 0 : clamp(1 - p * 4, 0, 1);
    const brainEvents = brainSignals.update(now, brainWeight > 0 && now - t0 > 2200);
    const lit = [];
    let theta = .32, tilt = .12;
    if (!still) {
      if (!dragging) { yawBase += vYaw; vYaw *= .95; pitch += vPitch; vPitch *= .95; pitch *= .996; }
      lean += (leanT - lean) * .05;
      theta = yawBase + .5 * Math.sin(now / 5200) + lean; tilt = .12 + .04 * Math.sin(now / 7000) + pitch;
    }
    const cs = Math.cos(theta), sn = Math.sin(theta), ct = Math.cos(tilt), st = Math.sin(tilt), bands = [[], [], []];
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
    for (let k = 0; k < N; k++) {
      const q = P[k], j = k * 3;
      if (anchored) position(i, m, oax + A[j] * sa, oay + A[j + 1] * sa, A[j + 2] * sa, obx + B[j] * sb, oby + B[j + 1] * sb, B[j + 2] * sb, q, motionPoint, frameInfo);
      else position(i, m, A[j], A[j + 1], A[j + 2], B[j], B[j + 1], B[j + 2], q, motionPoint, frameInfo);
      let x = motionPoint.x, y = motionPoint.y, z = motionPoint.z;
      if (!still) { /* at the start the triangles gather in from a wide scatter */
        const ie = 1 - Math.pow(1 - clamp((now - t0 - q.d * 700) / 2000, 0, 1), 3);
        x = scatter[j] + (x - scatter[j]) * ie; y = scatter[j + 1] + (y - scatter[j + 1]) * ie; z = scatter[j + 2] + (z - scatter[j + 2]) * ie;
      }
      const brightness = brainSignals.light(x, y, z) * brainWeight;
      let X = x * side, Y = y * side;
      const Z = z * side;
      if (!still && (m === 0 || m === 1)) { X += Math.sin(now / 1100 + q.ph) * 2; Y += Math.cos(now / 1300 + q.ph) * 2; }
      const x1 = X * cs + Z * sn, z1 = -X * sn + Z * cs, y1 = Y * ct - z1 * st, z2 = Y * st + z1 * ct;
      const fz = D / (D - z2), depth = clamp((z2 + Zr) / (2 * Zr), 0, 1);
      if (brightness > .08) lit.push([cx + x1 * fz, cy + y1 * fz, q.s * fz * (1 + brightness * .7), q.r, brightness]);
      bands[depth < .34 ? 0 : depth < .67 ? 1 : 2].push([cx + x1 * fz, cy + y1 * fz, q.s * fz * (.7 + depth * .6), q.r + (still ? 0 : now / 4000 * (q.ph > 3 ? 1 : -1) * .3 + motionPoint.spin), q.c]);
    }
    const alphas = [.28, .6, 1], widths = [.7, 1, 1.4];
    for (let b = 0; b < 3; b++) {
      for (let ci = 0; ci < COLORS.length; ci++) {
        ctx.beginPath(); ctx.strokeStyle = COLORS[ci]; ctx.globalAlpha = alphas[b]; ctx.lineWidth = widths[b];
        for (const t of bands[b]) if (t[4] === ci) tri(ctx, t[0], t[1], t[2], t[3]);
        ctx.stroke();
      }
    }
    /* batch the lit regions; the expensive glow is kept for the few arriving signals */
    ctx.strokeStyle = "#bdedff"; ctx.lineWidth = 1.8;
    for (let level = 0; level < 3; level++) {
      ctx.beginPath(); ctx.globalAlpha = .25 + level * .3;
      for (const pt of lit) if (Math.min(2, Math.floor(pt[4] * 3)) === level) tri(ctx, pt[0], pt[1], pt[2], pt[3]);
      ctx.stroke();
    }
    const project = (x, y, z) => {
      const X = x * side, Y = y * side, Z = z * side;
      const rx = X * cs + Z * sn, rz = -X * sn + Z * cs;
      const ry = Y * ct - rz * st, depth = Y * st + rz * ct, scale = D / (D - depth);
      return [cx + rx * scale, cy + ry * scale];
    };
    const drawSignals = (events, weight) => {
      if (!weight) return;
      for (const event of events) {
        if (event.age >= 900) continue;
        const c = event.channel, travel = event.age / 900;
        const path = (t) => {
          const curve = Math.sin(t * Math.PI) * .13;
          return project(c.sx + (c.x - c.sx) * t + curve * Math.cos(c.phase), c.sy + (c.y - c.sy) * t + curve * Math.sin(c.phase), c.sz + (c.z - c.sz) * t);
        };
        const head = path(travel), tail = path(Math.max(0, travel - .13));
        ctx.globalAlpha = weight * Math.min(1, travel * 7); ctx.strokeStyle = "#99dcff"; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(tail[0], tail[1]); ctx.lineTo(head[0], head[1]); ctx.stroke();
        ctx.shadowColor = "#91cfff"; ctx.shadowBlur = 12; ctx.fillStyle = "#e8faff";
        ctx.beginPath(); ctx.arc(head[0], head[1], 2.4, 0, Math.PI * 2); ctx.fill(); ctx.shadowBlur = 0;
      }
    };
    drawSignals(brainEvents, brainWeight);
    ctx.globalAlpha = 1;
    raf = requestAnimationFrame(frame);
  }
  raf = requestAnimationFrame(frame);

  /* a tiny lean toward the pointer, and drag to spin (sideways only on touch, so scrolling is never blocked) */
  const onMove = (e) => { if (e.pointerType === "mouse" && !dragging) leanT = (e.clientX / W - .5) * .3; };
  const onDown = (e) => {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    dragging = true; last = { x: e.clientX, y: e.clientY }; vYaw = vPitch = 0; canvas.classList.add("grabbing");
    try { canvas.setPointerCapture(e.pointerId); } catch { /* not supported */ }
  };
  const onDrag = (e) => {
    if (!dragging || !last) return;
    const dx = e.clientX - last.x, dy = e.clientY - last.y; last = { x: e.clientX, y: e.clientY };
    yawBase += dx * .01; vYaw = dx * .01;
    if (e.pointerType !== "touch") { pitch += dy * .01; vPitch = dy * .01; }
  };
  const release = () => { dragging = false; last = null; canvas.classList.remove("grabbing"); };
  window.addEventListener("pointermove", onMove);
  canvas.addEventListener("pointerdown", onDown);
  canvas.addEventListener("pointermove", onDrag);
  canvas.addEventListener("pointerup", release);
  canvas.addEventListener("pointercancel", release);

  return () => {
    cancelAnimationFrame(raf); stopAmbient();
    window.removeEventListener("resize", resize);
    window.removeEventListener("pointermove", onMove);
    canvas.removeEventListener("pointerdown", onDown);
    canvas.removeEventListener("pointermove", onDrag);
    canvas.removeEventListener("pointerup", release);
    canvas.removeEventListener("pointercancel", release);
  };
}
