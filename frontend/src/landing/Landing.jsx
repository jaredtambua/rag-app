import { useEffect, useRef } from "react";
import Logo from "../components/Logo.jsx";
import DemoLink from "../components/DemoLink.jsx";
import { startCloud } from "./cloud.js";
import { STOP_COUNT } from "./stops.js";
import { useSceneLayers } from "./useSceneLayers.js";
import { FileIcon } from "../demo/icons.jsx";
import { warmUpServer } from "../demo/useRagDemo.js";
import { useStopNavigation } from "./useStopNavigation.js";
import "./landing.css";

/* the stops each link covers: how it works = knowledge base and citations, use cases = the two examples, privacy = the last scene */
const NAV_LINKS = [
  { label: "How it works", stop: 1, stops: "1-2" },
  { label: "Use cases", stop: 3, stops: "3-4" },
  { label: "Privacy", stop: 5, stops: "5-5" },
];

const USE_CASES = [
  { who: "Lawyers", title: "Find the exact quote.", text: "Search every contract and see the page it came from." },
  { who: "Scientists", title: "Find the exact scientific remark.", text: "Ask across your papers and get the passage, with its page." },
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
          <h2 className="head">One knowledge base for you or your team.</h2>
          <div className="small">
            <p className="lede">Add any documents, related or not. Tessel finds the answer.</p>
            <p className="note">The demo is a private, temporary preview.</p>
          </div>
        </div>

        <div className="scene-text t2" data-stop="2">
          <div className="cite">
            <h2 className="h-md">Answers cite the pages they used.</h2>
            <figure className="example" aria-label="Example of an answer with its source">
              <figcaption className="tag">Example</figcaption>
              <p className="ex-q">How much notice is needed to end the agreement?</p>
              <p className="ex-a">Either party can end the agreement with 60 days&rsquo; written notice.</p>
              <div className="ex-source">
                <div className="ex-source-head">
                  <FileIcon size={16} />
                  <span className="ex-pill">Page 9</span>
                </div>
                <p className="ex-name">services-agreement.pdf</p>
                <p className="ex-quote">&ldquo;Either party may terminate this Agreement by giving the other party not less than sixty (60) days&rsquo; prior written notice.&rdquo;</p>
              </div>
            </figure>
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

        <div className="scene-text t5" data-stop="5">
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
