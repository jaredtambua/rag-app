/* Four reversible paths, one between each pair of neighbouring stops. Progress comes from the section position, not wall-clock time.
   Edges 2 and 3 work on screen-fixed positions: a and b arrive already converted into the current frame (see cloud.js), and
   `frame` carries the ring's centre (ca) and the screen centre (g) in that same frame. The ring-to-grid path releases the
   triangles one after another, ordered by particle.i (0 to 1), so the ring peels apart as a stream instead of all at once. */
function smooth(u) { return u * u * (3 - 2 * u); }
function clamp01(v) { return Math.max(0, Math.min(1, v)); }

/* Ring to grid: the ring unspools. Triangles peel off in turn, whip away along the ring's tangent and curve down into their grid square. */
function unspool(t, ax, ay, az, bx, by, bz, particle, frame, out) {
    var start = particle.i * .5, u = clamp01((t - start) / .5), e = smooth(u);
    var dx = ax - frame.ca[0], dy = ay - frame.ca[1], len = Math.hypot(dx, dy) || 1;
    var nx = dx / len, ny = dy / len, tx = -ny, ty = nx;     /* outward and tangent directions at the start point */
    var kx = ax + tx * .55 + nx * .22, ky = ay + ty * .55 + ny * .22;   /* the pulled-out bend of the path */
    var s = 1 - e;
    out.x = s * s * ax + 2 * s * e * kx + e * e * bx;
    out.y = s * s * ay + 2 * s * e * ky + e * e * by;
    out.z = az + (bz - az) * e + Math.sin(Math.PI * e) * particle.w[2] * .25;
    out.spin = Math.sin(Math.PI * e) * 3 * (particle.w[0] > 0 ? 1 : -1);
}

export function position(edge, t, ax, ay, az, bx, by, bz, particle, out, frame) {
    if (t <= 0) { out.x = ax; out.y = ay; out.z = az; out.spin = 0; return; }
    if (t >= 1) { out.x = bx; out.y = by; out.z = bz; out.spin = 0; return; }
    if (edge === 2) { unspool(t, ax, ay, az, bx, by, bz, particle, frame, out); return; }
    var delay = particle.d * .35;
    var u = Math.max(0, Math.min(1, (t - delay) / (1 - delay)));
    var blend = u * u * (3 - 2 * u);
    var wave = Math.sin(Math.PI * u), envelope = wave * wave;
    var phase = particle.ph;
    var x = ax + (bx - ax) * blend;
    var y = ay + (by - ay) * blend;
    var z = az + (bz - az) * blend;
    var spin = 0, angle, radius;
    switch (edge) {
      case 0: // Brain to network: split into five branching streams that settle into linked nodes.
        angle = Math.floor(phase / (Math.PI * 2) * 5) * Math.PI * 2 / 5;
        radius = envelope * (.5 + Math.abs(particle.w[0]) * .4);
        x += Math.cos(angle) * radius;
        y += Math.sin(angle) * radius * .7;
        z += envelope * particle.w[2] * .38;
        spin = envelope * Math.sin(angle) * 1.5;
        break;
      case 1: // Network to ring: one prevailing wind curls the strands into an orbit.
        angle = phase * .2 + u * Math.PI * 1.5;
        x += envelope * (.75 + Math.cos(angle) * .45);
        y += envelope * (Math.sin(angle + ay * 2) * .5 - .16);
        z += envelope * Math.sin(angle + phase) * .35;
        spin = envelope * (u * 4 + phase * .2);
        break;
      case 3: // Grid to lock: draw the strands tightly in to the centre of the screen, then spread out into the lock and key.
        x = frame.g[0] + (x - frame.g[0]) * (1 - envelope * .9);
        y = frame.g[1] + (y - frame.g[1]) * (1 - envelope * .9);
        z *= 1 - envelope * .9;
        x += envelope * Math.cos(phase) * .05;
        y += envelope * Math.sin(phase) * .05;
        spin = envelope * .35;
        break;
    }
    out.x = x; out.y = y; out.z = z; out.spin = spin;
  }
