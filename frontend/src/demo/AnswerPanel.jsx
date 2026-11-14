import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown"; /* images are not rendered: an answer must not load anything from another site */
import { FileIcon } from "./icons.jsx";

const LONG_QUOTE = 150;

function Source({ citation }) {
  const [open, setOpen] = useState(false);
  const long = citation.quote.length > LONG_QUOTE;
  return (
    <li className="source">
      <div className="source-head">
        <FileIcon size={16} />
        <span className="page-pill">Page {citation.page}</span>
      </div>
      <p className="source-name" title={citation.source}>{citation.source}</p>
      <blockquote className={long && !open ? "is-clamped" : undefined}>&ldquo;{citation.quote}&rdquo;</blockquote>
      {long && (
        <button className="more" type="button" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? "Show less" : "Show more"}
        </button>
      )}
    </li>
  );
}

/* One question and its answer, as a short thread. The answer is a live region so screen readers announce it. */
export default function AnswerPanel({ answer, citations, isAsking, askedQuestion, failedMessage }) {
  const askedRef = useRef(null);

  /* bring the new question to the top of the thread so the start of the answer is what the visitor sees */
  useEffect(() => {
    if (!isAsking) return;
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    askedRef.current?.scrollIntoView({ block: "start", behavior: calm ? "auto" : "smooth" });
  }, [isAsking]);

  return (
    <div className="turn" aria-live="polite" aria-busy={isAsking}>
      <p className="asked" ref={askedRef}>{askedQuestion}</p>

      {isAsking && (
        <div className="reply" role="status">
          <div className="skeleton" aria-hidden="true"><span /><span /><span /><span /></div>
          <p className="muted">Reading your documents and writing an answer...</p>
        </div>
      )}

      {!isAsking && !answer && (
        <div className="reply reply-failed">
          <p>{failedMessage || "No answer came back."} Your question is still in the box below, so you can try again.</p>
        </div>
      )}

      {!isAsking && answer && (
        <>
          <div className="reply">
            <div className="markdown"><ReactMarkdown disallowedElements={["img"]}>{answer}</ReactMarkdown></div>
          </div>

          {citations.length > 0 && (
            <section className="sources" aria-label="Sources">
              <h3>Sources <span>{citations.length}</span></h3>
              <ul>
                {citations.map((citation, index) => <Source key={index} citation={citation} />)}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  );
}
