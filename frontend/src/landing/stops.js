/* The landing page is one long scroll with five stops, one per scene.
   The cloud holds one shape per stop: hero, knowledge base, citations (ring), use cases (grid), privacy. */
export const STOP_SHAPES = ["brain", "network", "ring", "grid", "padlock"];
export const STOP_COUNT = STOP_SHAPES.length;

/* one stop is the height of the first spacer in the scroll track */
export function stopUnit() {
  return document.getElementById("top")?.offsetHeight || window.innerHeight;
}

export const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
