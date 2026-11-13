/* Tiny hash router. "#/demo" is the app; anything else is the landing page.
   Hash routes need no server rewrite rules, so the build works on any static host. */
import { useEffect, useState } from "react";

export const DEMO_PATH = "#/demo";
export const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function readRoute() {
  const hash = window.location.hash;
  return hash === DEMO_PATH || hash === `${DEMO_PATH}/` ? "demo" : "landing";
}

export function useRoute() {
  const [route, setRoute] = useState(readRoute);
  useEffect(() => {
    const onChange = () => setRoute(readRoute());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
