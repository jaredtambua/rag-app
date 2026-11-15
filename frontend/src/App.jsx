import { useCallback, useEffect, useRef, useState } from "react";
import Landing from "./landing/Landing.jsx";
import Workspace from "./demo/Workspace.jsx";
import { reducedMotion, useRoute } from "./routing.js";

const FADE_OUT_MS = 200;
const TITLES = {
  landing: "Tessel: ask your documents anything",
  demo: "Tessel demo: upload a PDF and ask a question",
};

/* Whatever changes the address (a link, the keyboard, Back and Forward, a typed address) gives a new route.
   The page on screen then fades out, the new one takes its place and fades in. With reduced motion it is an instant swap. */
export default function App() {
  const route = useRoute();
  const [settled, setSettled] = useState(route);
  const firstView = useRef(true);
  const still = reducedMotion();
  const shown = still ? route : settled;
  const leaving = shown !== route;

  useEffect(() => {
    if (!leaving) return undefined;
    const timer = setTimeout(() => setSettled(route), FADE_OUT_MS);
    return () => clearTimeout(timer);
  }, [route, leaving]);

  /* the new page starts at the top, and its main area takes focus so keyboard users land in it */
  useEffect(() => {
    document.title = TITLES[shown];
    window.scrollTo({ top: 0, behavior: "instant" });
    if (firstView.current) { firstView.current = false; return; }
    const main = document.getElementById("main");
    if (main && (!document.activeElement || document.activeElement === document.body)) {
      main.setAttribute("tabindex", "-1");
      main.focus({ preventScroll: true });
    }
  }, [shown]);

  const navigate = useCallback((hash) => { window.location.hash = hash; }, []);

  return (
    <div className="view" key={shown} data-leaving={leaving}>
      {shown === "demo" ? <Workspace onNavigate={navigate} /> : <Landing onNavigate={navigate} />}
    </div>
  );
}
