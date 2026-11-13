import ReactMarkdown from "react-markdown";
import { FileIcon } from "./icons.jsx";

/* the answer area is a live region so screen readers announce the result when it arrives */
export default function AnswerPanel({ answer, citations, isAsking, askedQuestion }) {
  return (
    <section className="panel answer" aria-labelledby="answer-title" aria-live="polite" aria-busy={isAsking}>
      <h2 id="answer-title" className="panel-title">3. Answer and sources</h2>

      {isAsking && (
        <div className="thinking" role="status">
          <p className="asked">{askedQuestion}</p>
          <div className="skeleton" aria-hidden="true"><span /><span /><span /></div>
          <p className="muted">Reading your documents and writing an answer...</p>
        </div>
      )}

      {!isAsking && !answer && (
        <p className="empty">Your answer will appear here, with the page and passage it came from.</p>
      )}

      {!isAsking && answer && (
        <>
          {askedQuestion && <p className="asked">{askedQuestion}</p>}
          <div className="markdown"><ReactMarkdown>{answer}</ReactMarkdown></div>

          {citations.length > 0 && (
            <div className="sources">
              <h3>Sources</h3>
              <ul>
                {citations.map((citation, index) => (
                  <li key={index} className="source">
                    <div className="source-head">
                      <FileIcon size={16} />
                      <span className="source-name">{citation.source}</span>
                      <span className="page-pill">Page {citation.page}</span>
                    </div>
                    <blockquote>&ldquo;{citation.quote}&rdquo;</blockquote>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
}
