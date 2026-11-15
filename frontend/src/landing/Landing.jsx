import { useEffect, useRef } from "react";
import Logo from "../components/Logo.jsx";
import DemoLink from "../components/DemoLink.jsx";
import { startCloud } from "./cloud.js";
import { STOP_COUNT } from "./stops.js";
import { useSceneLayers } from "./useSceneLayers.js";
import { warmUpServer } from "../demo/useRagDemo.js";
import { useStopNavigation } from "./useStopNavigation.js";
import "./landing.css";

/* the stops each link covers: how it works = knowledge base and citations, use cases = the quotes scene, privacy = the last scene */
const NAV_LINKS = [
  { label: "How it works", stop: 1, stops: "1-2" },
  { label: "Use cases", stop: 3, stops: "3-3" },
  { label: "Privacy", stop: 4, stops: "4-4" },
];

const USE_CASES = [
  { who: "Lawyers", text: "Search every contract and see the page it came from." },
  { who: "Scientists", text: "Ask across your papers and get the passage, with its page." },
  { who: "Consultants", text: "Find the exact line in a client report, with its page." },
  { who: "New hires", text: "Ask what a company term means and get the page that explains it." },
];

export default function Landing({ onNavigate }) {
  const cloudRef = useRef(null);
  const ambientRef = useRef(null);
  const scenesRef = useRef(null);
  const { index, busy, goTo, previous, next } = useStopNavigation();

  useEffect(() => startCloud(cloudRef.current, ambientRef.current), []);
  useSceneLayers(scenesRef);

  /* wake the demo server in the background so it is ready by the time someone opens the demo */
  useEffect(() => { warmUpServer(); }, []);

  function jump(event, stop) {
    event.preventDefault();
    goTo(stop);
  }

  return (
    <div className="landing">
      <a className="skip" href="#/demo" onClick={(e) => { e.preventDefault(); onNavigate("#/demo"); }}>Skip to the demo</a>
      <canvas ref={ambientRef} id="ambient" aria-hidden="true" />
      <canvas ref={cloudRef} id="cloud" role="img" aria-label="A cloud of small triangles that changes shape as you scroll. Drag it to spin it." />

      <header className="top">
        <nav className="nav" aria-label="Main">
          <a className="logo-link" href="#/" aria-label="Tessel, back to the top" onClick={(e) => jump(e, 0)}><Logo /></a>
          <div className="nav-links">
            {NAV_LINKS.map((l) => (
              <a key={l.label} href="#/" data-stops={l.stops} onClick={(e) => jump(e, l.stop)}>{l.label}</a>
            ))}
          </div>
          <DemoLink onNavigate={onNavigate} />
        </nav>
      </header>

      <main id="main" ref={scenesRef}>
        <div className="scene-text t0" data-stop="0">
          <div className="copy">
            <p className="eyebrow">Live demo</p>
            <h1 className="h-lg">Ask your documents anything.</h1>
            <p className="lede">Tessel reads the PDFs you give it and answers with the page it found it on. No hunting through folders: answers point to the pages they came from.</p>
            <DemoLink onNavigate={onNavigate} />
          </div>
        </div>

        <div className="scene-text t1" data-stop="1">
          <div className="copy">
            <h2 className="h-md">One knowledge base for you or your team.</h2>
            <p className="lede">Add any documents, related or not. Tessel finds the answer.</p>
            <p className="note">The demo is a private, temporary preview.</p>
          </div>
        </div>

        <div className="scene-text t2" data-stop="2">
          <div className="copy">
            <h2 className="h-md">Answers cite the pages they used.</h2>
            <p className="lede">Every answer shows the file and page it came from.</p>
          </div>
        </div>

        <div className="scene-text t3" data-stop="3">
          <div className="copy">
            <h2 className="h-md">Find the exact quote. Or explain your own jargon.</h2>
            <ul className="audiences">
              {USE_CASES.map((c) => (
                <li key={c.who}>
                  <p className="who">{c.who}</p>
                  <p className="what">{c.text}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="scene-text t4" data-stop="4">
          <div className="copy">
            <h2 className="h-md">Try it with your own files.</h2>
            <p className="lede">Your files stay private to you and are deleted after 30 minutes. Their text is sent to an AI service to build the index and write answers.</p>
            <DemoLink onNavigate={onNavigate} />
          </div>
        </div>

        {/* the scrolling track: one screen per stop */}
        <div className="track" aria-hidden="true">
          {Array.from({ length: STOP_COUNT }, (_, i) => <div className="spacer" id={i === 0 ? "top" : undefined} key={i} />)}
        </div>
      </main>

      <nav className="section-controls" aria-label="Section navigation">
        <button type="button" aria-label="Previous section" aria-disabled={busy || index === 0} onClick={previous}>&#8592; Previous</button>
        <span className="position" aria-live="polite" aria-atomic="true">{index + 1} / {STOP_COUNT}</span>
        <button type="button" aria-label="Next section" aria-disabled={busy || index === STOP_COUNT - 1} onClick={next}>Next &#8594;</button>
      </nav>
    </div>
  );
}
