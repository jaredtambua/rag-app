/* Five reversible paths, one between each pair of neighbouring stops. Progress comes from the section position, not wall-clock time. */
export function position(edge, t, ax, ay, az, bx, by, bz, particle, out) {
    if (t <= 0) { out.x = ax; out.y = ay; out.z = az; out.spin = 0; return; }
    if (t >= 1) { out.x = bx; out.y = by; out.z = bz; out.spin = 0; return; }
    var delay = particle.d * .35;
    var u = Math.max(0, Math.min(1, (t - delay) / (1 - delay)));
    var blend = u * u * (3 - 2 * u);
    var wave = Math.sin(Math.PI * u), envelope = wave * wave;
    var phase = particle.ph, lane = Math.floor(phase / (Math.PI * 2) * 5) - 2;
    var x = ax + (bx - ax) * blend;
    var y = ay + (by - ay) * blend;
    var z = az + (bz - az) * blend;
    var spin = 0, angle, radius, turn;
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
      case 2: // Ring to grid: loose ribbons unfurl and flatten into rows.
        x += envelope * particle.w[0] * .8;
        y += envelope * (lane * .16 + Math.sin(u * Math.PI * 3 + ax * 5) * .23);
        z += envelope * Math.cos(u * Math.PI * 2 + phase) * .32;
        spin = envelope * Math.sin(u * Math.PI * 2 + lane);
        break;
      case 3: // Grid to spiral: wind the entire field into a travelling vortex.
        turn = envelope * Math.PI * 1.35;
        radius = 1 + envelope * .65;
        x = (ax + (bx - ax) * blend) * Math.cos(turn) - y * Math.sin(turn);
        y = (ax + (bx - ax) * blend) * Math.sin(turn) + y * Math.cos(turn);
        x = x * radius + envelope * Math.cos(phase + u * 7) * .28;
        y = y * radius + envelope * Math.sin(phase + u * 7) * .28;
        z += envelope * Math.sin(phase + u * Math.PI * 2) * .55;
        spin = turn;
        break;
      case 4: // Spiral to lock: draw the strands tightly inward, then assemble.
        x *= 1 - envelope * .88;
        y *= 1 - envelope * .88;
        z *= 1 - envelope * .88;
        x += envelope * Math.cos(phase) * .055;
        y -= envelope * .12;
        spin = envelope * .35;
        break;
    }
    out.x = x; out.y = y; out.z = z; out.spin = spin;
  }
