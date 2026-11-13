/* Seven reversible paths. Progress comes from the section position, not wall-clock time. */
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
      case 0: // Brain to files: lift apart in sheets, then lower into the stack.
        x += envelope * (particle.w[0] * .28 + lane * .12);
        y += envelope * (lane * .25 - .22);
        z += envelope * particle.w[2] * .22;
        spin = envelope * lane * .2;
        break;
      case 1: // Files to ring: one prevailing wind curls into an orbit.
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
      case 4: // Spiral to network: split into five branching streams.
        angle = Math.floor(phase / (Math.PI * 2) * 5) * Math.PI * 2 / 5;
        radius = envelope * (.5 + Math.abs(particle.w[0]) * .4);
        x += Math.cos(angle) * radius;
        y += Math.sin(angle) * radius * .7;
        z += envelope * particle.w[2] * .38;
        spin = envelope * Math.sin(angle) * 1.5;
        break;
      case 5: // Network to lock: draw the strands tightly inward, then assemble.
        x *= 1 - envelope * .88;
        y *= 1 - envelope * .88;
        z *= 1 - envelope * .88;
        x += envelope * Math.cos(phase) * .055;
        y -= envelope * .12;
        spin = envelope * .35;
        break;
      case 6: // Lock to sphere: open two halves, release a broad burst, gather again.
        var half = ax < 0 ? -1 : 1;
        var release = Math.sin(Math.PI * Math.min(1, u * 1.5));
        x += envelope * (half * .62 + particle.w[0] * .5);
        y += envelope * (particle.w[1] * .65 - release * .25);
        z += envelope * particle.w[2] * .7;
        spin = envelope * half * 2.5;
        break;
    }
    out.x = x; out.y = y; out.z = z; out.spin = spin;
  }
