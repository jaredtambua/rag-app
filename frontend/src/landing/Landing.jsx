import { useEffect, useRef } from "react";
import Logo from "../components/Logo.jsx";
import DemoLink from "../components/DemoLink.jsx";
import { startCloud } from "./cloud.js";
import { STOP_COUNT } from "./stops.js";
import { useSceneLayers } from "./useSceneLayers.js";
import { warmUpServer } from "../demo/useRagDemo.js";
import { useStopNavigation } from "./useStopNavigation.js";
import "./landing.css";

const NAV_LINKS = [
  { label: "How it works", stop: 1, stops: "1-2" },
  { label: "Use cases", stop: 3, stops: "3-5" },
  { label: "Privacy", stop: 6, stops: "6-6" },
];

const USE_CASES = [
  { who: "Lawyers", title: "Find the clause across your contracts.", text: "And see exactly where it came from." },
  { who: "Researchers", title: "Ask a pile of papers one question.", text: "Get the answer with the passage attached." },
  { who: "Small teams", title: "Make your team’s documents answer back.", text: "Turn the folder nobody can search into something that can." },
];
const FIRST_USE_STOP = 3;

function Dots({ active, onSelect }) {
  return (
    <div className="dots">
      {USE_CASES.map((_, i) => (
        <button
          key={i}
          className="dot"
          type="button"
          aria-label={`Show slide ${i + 1} of ${USE_CASES.length}`}
          aria-current={i === active ? "true" : undefined}
          onClick={() => onSelect(FIRST_USE_STOP + i)}
        />
      ))}
    </div>
  );
}

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
          <h2 className="head">Create your personal knowledge base.</h2>
          <p className="small lede">Add the files you already have, then ask in plain words. This is a demo: Tessel as a product would keep your knowledge base, built from your own documents.</p>
        </div>

        <div className="scene-text t2" data-stop="2">
          <h2 className="head h-md">Answers cite the pages they used.</h2>
          <div className="passage">
            <p className="tag">Example</p>
            <p className="where">Page 14, clause 7.2</p>
            <p className="quote">Either party may end this agreement with sixty days&rsquo; written notice.</p>
          </div>
        </div>

        {USE_CASES.map((c, i) => (
          <div className="scene-text t3" data-stop={FIRST_USE_STOP + i} key={c.who}>
            <div className="copy">
              <p className="eyebrow">{c.who}</p>
              <h2 className="h-md">{c.title}</h2>
              <p className="lede">{c.text}</p>
              <Dots active={i} onSelect={goTo} />
            </div>
          </div>
        ))}

        <div className="scene-text t6" data-stop="6">
          <div className="copy">
            <h2 className="h-md">Keep it to files you can share.</h2>
            <p className="lede">Uploads are private to your browser and deleted 30 minutes after you add them. Their text is sent to an AI service to build the search index and write answers.</p>
          </div>
        </div>

        <div className="scene-text t7" data-stop="7">
          <div className="copy">
            <h2 className="h-lg">Try it with your own files.</h2>
            <p className="lede">The demo is live. Upload a PDF you know well, ask a question and see the page the answer came from.</p>
            <DemoLink onNavigate={onNavigate} />
          </div>
        </div>

        {/* the scrolling track: one screen per stop (three for the use-case slides) */}
        <div className="track" aria-hidden="true">
          <div className="spacer" id="top" />
          <div className="spacer" />
          <div className="spacer" />
          <div className="spacer spacer-3" />
          <div className="spacer" />
          <div className="spacer" />
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
