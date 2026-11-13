/* The landing page is one long scroll with eight stops (five scenes; "how it works" has two stops and
   "who it's for" has three slides). The cloud holds one shape per stop. */
export const STOP_SHAPES = ["brain", "stack", "ring", "grid", "spiral", "network", "padlock", "sphere"];
export const STOP_COUNT = STOP_SHAPES.length;

/* one stop is the height of the first spacer in the scroll track */
export function stopUnit() {
  return document.getElementById("top")?.offsetHeight || window.innerHeight;
}

export const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
