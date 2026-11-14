/* The landing page is one long scroll with six stops for five scenes (the examples scene has two slides).
   The cloud holds one shape per stop: hero, knowledge base, citations, lawyers, scientists, privacy. */
export const STOP_SHAPES = ["brain", "network", "ring", "grid", "spiral", "padlock"];
export const STOP_COUNT = STOP_SHAPES.length;

/* one stop is the height of the first spacer in the scroll track */
export function stopUnit() {
  return document.getElementById("top")?.offsetHeight || window.innerHeight;
}

export const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
