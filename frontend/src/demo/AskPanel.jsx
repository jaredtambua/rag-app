import { useEffect, useRef } from "react";
import { SendIcon } from "./icons.jsx";
import { LIMITS, MESSAGES } from "./limits.js";

/* the send shortcut works with Ctrl or Cmd; the hint names the one this computer uses */
const IS_MAC = typeof navigator !== "undefined" && /Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent || "");
const SHORTCUT = IS_MAC ? "Cmd+Enter" : "Ctrl+Enter";

/* The ask box, docked at the bottom of the conversation pane. */
export default function AskPanel({ question, setQuestion, askQuestion, isAsking, locked, lockedHint, textareaRef }) {
  const fallbackRef = useRef(null);
  const ref = textareaRef || fallbackRef;

  /* grow with the text up to a limit, and shrink again when it is replaced or cleared */
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 164)}px`;
  }, [question, ref]);

  const length = Array.from(question.trim()).length; /* code points, like the server */
  const over = length > LIMITS.questionChars;
  const nearLimit = length >= LIMITS.questionChars - 100;

  function onKeyDown(event) {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && !isAsking && !over) {
      event.preventDefault();
      askQuestion();
    }
  }

  return (
    <form className="composer-wrap" onSubmit={(event) => { event.preventDefault(); if (!isAsking && !over) askQuestion(); }}>
      <div className="composer">
        <label className="visually-hidden" htmlFor="question">Your question</label>
        <textarea
          id="question"
          ref={ref}
          rows="1"
          aria-invalid={over}
          value={question}
          disabled={locked}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder={locked ? (lockedHint ? "Waiting for the demo server" : "Add a PDF to start asking") : "Ask about your documents"}
        />
        <button className="btn btn-primary" type="submit" disabled={isAsking || locked || over}>
          {isAsking ? "Thinking..." : "Ask"} {!isAsking && <SendIcon size={16} />}
        </button>
      </div>
      <p className={`hint${!locked && nearLimit ? " is-alert" : ""}`} aria-live="polite">
        <span>
          {locked
            ? (lockedHint || "Questions open up once a document is added.")
            : over
              ? MESSAGES.questionTooLong
              : `${SHORTCUT} to send. Up to ${LIMITS.questionsPerHour} questions an hour.`}
        </span>
        {!locked && nearLimit && <span className={`counter${over ? " is-over" : ""}`}>{length} / {LIMITS.questionChars}</span>}
      </p>
    </form>
  );
}
