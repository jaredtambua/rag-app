import { useState } from "react";
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

/* One question and its answer. The thread around it is a live region, so a new answer is announced when it arrives. */
export default function AnswerPanel({ turn, onRetry, retryDisabled, innerRef }) {
  const { question, status, answer, citations, message } = turn;
  return (
    <article className="turn" ref={innerRef} aria-busy={status === "pending"}>
      <p className="asked">{question}</p>

      {status === "pending" && (
        <div className="reply" role="status">
          <div className="skeleton" aria-hidden="true"><span /><span /><span /><span /></div>
          <p className="muted">Reading your documents and writing an answer...</p>
        </div>
      )}

      {status === "failed" && (
        <div className="reply reply-failed">
          <p>{message || "No answer came back."}</p>
          <button className="btn btn-ghost btn-small" type="button" disabled={retryDisabled} onClick={onRetry}>Try again</button>
        </div>
      )}

      {status === "done" && (
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
    </article>
  );
}
