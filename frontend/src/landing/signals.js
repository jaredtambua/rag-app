/* Incoming signals and their response share the same impact point and clock. */
export function createSignals(points) {
    var channels = [], active = [], origin = null;
    for (var i = 0; i < 6; i++) {
      var j = Math.floor((i + .37) / 6 * points.length / 3) * 3;
      var x = points[j], y = points[j + 1], z = points[j + 2];
      var length = Math.hypot(x, y, z) || 1;
      channels.push({ x: x, y: y, z: z, sx: x + x / length * .65, sy: y + y / length * .65 - .12, sz: z + z / length * .65, period: 3300 + i * 317, offset: i * 479, phase: i * 2.4 });
    }
    return {
      update: function (now, enabled) {
        if (!enabled) { active.length = 0; origin = null; return active; }
        if (origin === null) origin = now;
        active.length = 0;
        channels.forEach(function (channel) {
          var elapsed = now - origin - channel.offset;
          if (elapsed < 0) return;
          var age = elapsed % channel.period;
          if (age < 2500) active.push({ channel: channel, age: age, impact: Math.max(0, age - 900) });
        });
        return active;
      },
      light: function (x, y, z) {
        var light = 0;
        active.forEach(function (event) {
          if (event.age < 900) return;
          var c = event.channel, age = event.impact;
          var distance = Math.hypot(x - c.x, y - c.y, z - c.z);
          var flash = Math.exp(-distance * distance / .009) * Math.exp(-age / 320);
          var ring = Math.exp(-Math.pow((distance - age * .00032) / .045, 2)) * Math.exp(-age / 800);
          light += flash + ring * .6;
        });
        return Math.min(1, light);
      },
      pulse: function () {
        var amount = 0;
        active.forEach(function (event) { if (event.age >= 900) amount += Math.sin(Math.min(1, event.impact / 1100) * Math.PI) * Math.exp(-event.impact / 700); });
        return Math.min(.06, amount * .025);
      }
    };
  }
