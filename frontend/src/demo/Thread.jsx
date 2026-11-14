import { useEffect, useRef } from "react";
import AnswerPanel from "./AnswerPanel.jsx";
import { LIMITS } from "./limits.js";

/* the slim row above the thread: how many questions are kept, and the way to clear them */
export function ThreadBar({ count, disabled, onClear }) {
  return (
    <div className="thread-bar">
      <div className="thread-bar-inner">
        <span>{count >= LIMITS.historyTurns ? `Your last ${LIMITS.historyTurns} questions` : `${count} ${count === 1 ? "question" : "questions"}`}</span>
        <button className="link-btn" type="button" disabled={disabled} onClick={onClear}>Clear history</button>
      </div>
    </div>
  );
}

/* The conversation, oldest first. It is display only; the last few answered turns are also sent with each new question (see useRagDemo.js). */
export default function Thread({ items, isAsking, onRetry, onAddPdf, noDocuments }) {
  const latestRef = useRef(null);
  const turns = items.filter((item) => item.kind === "turn");
  const latestId = turns.length ? turns[turns.length - 1].id : null;

  /* a new question (typed or retried) is brought to the top of the thread so the start of its answer is what the visitor sees */
  useEffect(() => {
    if (latestId === null) return;
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    latestRef.current?.scrollIntoView({ block: "start", behavior: calm ? "auto" : "smooth" });
  }, [latestId]);

  return (
    <div className="thread-list" role="log" aria-label="Conversation">
      {items.map((item) => (item.kind === "note"
        ? <p className="thread-note" key={item.id}><span>A document was removed. Earlier answers may cite it.</span></p>
        : <AnswerPanel key={item.id} turn={item} innerRef={item.id === latestId ? latestRef : undefined} retryDisabled={isAsking} onRetry={() => onRetry(item.id)} />))}
      {noDocuments && (
        <div className="thread-empty">
          <p>No documents left. Add a PDF to keep asking.</p>
          <button className="btn btn-ghost btn-small" type="button" onClick={onAddPdf}>Add a PDF</button>
        </div>
      )}
    </div>
  );
}
