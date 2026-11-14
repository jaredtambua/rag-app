import { useEffect, useRef } from "react";
import { SendIcon } from "./icons.jsx";
import { LIMITS } from "./limits.js";

/* The ask box, docked at the bottom of the conversation pane. */
export default function AskPanel({ question, setQuestion, askQuestion, isAsking, locked, textareaRef }) {
  const fallbackRef = useRef(null);
  const ref = textareaRef || fallbackRef;

  /* grow with the text up to a limit, and shrink again when it is replaced or cleared */
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 164)}px`;
  }, [question, ref]);

  function onKeyDown(event) {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && !isAsking) {
      event.preventDefault();
      askQuestion();
    }
  }

  return (
    <form className="composer-wrap" onSubmit={(event) => { event.preventDefault(); if (!isAsking) askQuestion(); }}>
      <div className="composer">
        <label className="visually-hidden" htmlFor="question">Your question</label>
        <textarea
          id="question"
          ref={ref}
          rows="1"
          maxLength={LIMITS.questionChars}
          value={question}
          disabled={locked}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder={locked ? "Add a PDF to start asking" : "Ask about your documents"}
        />
        <button className="btn btn-primary" type="submit" disabled={isAsking || locked}>
          {isAsking ? "Thinking..." : "Ask"} {!isAsking && <SendIcon size={16} />}
        </button>
      </div>
      <p className="hint">{locked ? "Questions open up once a document is added." : "Ctrl+Enter to send. Enter adds a new line."}</p>
    </form>
  );
}
