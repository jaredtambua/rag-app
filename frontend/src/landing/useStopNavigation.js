/* Moves between the landing page's stops: prev/next buttons, the dots, nav links and the arrow keys.
   Scrolling is animated by hand so it can be cancelled the moment the visitor scrolls themselves. */
import { useCallback, useEffect, useRef, useState } from "react";
import { STOP_COUNT, clamp, stopUnit } from "./stops.js";

const DURATION = 2400;

export function useStopNavigation() {
  const [index, setIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const animation = useRef(null);

  const current = () => clamp(Math.round(window.scrollY / stopUnit()), 0, STOP_COUNT - 1);

  const cancel = useCallback(() => {
    if (animation.current !== null) cancelAnimationFrame(animation.current);
    animation.current = null;
    setBusy(false);
  }, []);

  const goTo = useCallback((stop) => {
    if (animation.current !== null) return;
    const target = clamp(stop, 0, STOP_COUNT - 1);
    const from = window.scrollY, to = stopUnit() * target;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (still || Math.abs(to - from) < 1) {
      window.scrollTo({ top: to, behavior: "instant" });
      return;
    }
    const started = performance.now();
    setBusy(true);
    const step = (now) => {
      const progress = clamp((now - started) / DURATION, 0, 1);
      const eased = progress * progress * (3 - 2 * progress);
      window.scrollTo({ top: from + (to - from) * eased, behavior: "instant" });
      if (progress < 1) animation.current = requestAnimationFrame(step);
      else { animation.current = null; setBusy(false); }
    };
    animation.current = requestAnimationFrame(step);
  }, []);

  useEffect(() => {
    const onScroll = () => setIndex(current());
    const onKey = (e) => {
      if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      const el = e.target;
      if (el && (el.isContentEditable || el.closest?.("input, textarea, select, [role='slider'], [role='tablist'], [role='listbox'], [role='menu']"))) return;
      e.preventDefault();
      if (!e.repeat) goTo(current() + (e.key === "ArrowRight" ? 1 : -1));
    };
    const onResize = () => { cancel(); onScroll(); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("wheel", cancel, { passive: true });
    window.addEventListener("touchstart", cancel, { passive: true });
    window.addEventListener("resize", onResize);
    window.addEventListener("keydown", onKey);
    return () => {
      cancel();
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("wheel", cancel);
      window.removeEventListener("touchstart", cancel);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("keydown", onKey);
    };
  }, [goTo, cancel]);

  return { index, busy, goTo, previous: () => goTo(current() - 1), next: () => goTo(current() + 1) };
}
