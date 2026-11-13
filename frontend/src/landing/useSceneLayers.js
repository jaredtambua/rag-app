/* Fades each scene's words in and out as the page scrolls. The scenes sit fixed on screen, so this
   writes straight to the elements each frame instead of re-rendering React on every scroll tick. */
import { useEffect } from "react";
import { clamp, stopUnit } from "./stops.js";

export function useSceneLayers(containerRef) {
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const layers = Array.from(containerRef.current.querySelectorAll("[data-stop]")).map((el) => ({ el, stop: +el.dataset.stop, key: "" }));
    const links = Array.from(document.querySelectorAll("[data-stops]"));
    let raf = 0;

    function frame() {
      const still = mq.matches;
      const p = clamp(window.scrollY / stopUnit(), 0, layers.length - 1);
      for (const L of layers) {
        const d = p - L.stop;
        const o = still ? (Math.abs(d) < .5 ? 1 : 0) : clamp((.3 - Math.abs(d)) / .18, 0, 1);
        const key = Math.round(o * 100) + ":" + (still ? 0 : Math.round(d * 20));
        if (L.key === key) continue;
        L.key = key;
        L.el.style.opacity = o;
        L.el.style.visibility = o > .02 ? "visible" : "hidden";
        L.el.style.transform = still ? "" : `translateY(${(-d * 36).toFixed(1)}px)`;
        L.el.classList.toggle("on", o > .5);
      }
      const here = Math.round(p);
      for (const a of links) {
        const [from, to] = a.dataset.stops.split("-").map(Number);
        a.setAttribute("aria-current", here >= from && here <= to ? "true" : "false");
      }
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, [containerRef]);
}
