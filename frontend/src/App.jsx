import { useCallback, useEffect, useRef, useState } from "react";
import Landing from "./landing/Landing.jsx";
import Workspace from "./demo/Workspace.jsx";
import { reducedMotion, useRoute } from "./routing.js";

const CURTAIN_MS = 420;
const TITLES = {
  landing: "Tessel: ask your documents anything",
  demo: "Tessel demo: upload a PDF and ask a question",
};

export default function App() {
  const route = useRoute();
  const [curtain, setCurtain] = useState(false);
  const timer = useRef(0);

  useEffect(() => {
    document.title = TITLES[route];
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [route]);

  useEffect(() => () => clearTimeout(timer.current), []);

  /* a dark curtain fades in, the address changes underneath it, then it fades away */
  const navigate = useCallback((hash) => {
    clearTimeout(timer.current);
    if (reducedMotion()) { window.location.hash = hash; return; }
    setCurtain(true);
    timer.current = setTimeout(() => {
      window.location.hash = hash;
      requestAnimationFrame(() => setCurtain(false));
    }, CURTAIN_MS);
  }, []);

  /* Back/Forward during the fade wins: drop the pending jump and lift the curtain */
  useEffect(() => {
    const onHash = () => { clearTimeout(timer.current); setCurtain(false); };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  return (
    <>
      <div className="view" key={route}>
        {route === "demo" ? <Workspace onNavigate={navigate} /> : <Landing onNavigate={navigate} />}
      </div>
      <div className="curtain" data-on={curtain} aria-hidden="true">
        <svg width="44" height="40" viewBox="0 0 22 20"><path d="M11 1.5 20.5 18.5H1.5Z" fill="none" stroke="#8052ff" strokeWidth="1.5" strokeLinejoin="round" /></svg>
      </div>
    </>
  );
}
