import { useEffect, useRef } from "react";
import { SendIcon } from "./icons.jsx";
import { LIMITS, MESSAGES } from "./limits.js";

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

  /* Enter sends (so does Ctrl or Cmd+Enter); Shift+Enter is a new line. Enter that confirms an IME choice (Japanese, Chinese, Korean) must not send. */
  function onKeyDown(event) {
    if (event.key !== "Enter" || event.shiftKey) return;
    if (event.nativeEvent.isComposing || event.keyCode === 229) return;
    event.preventDefault();
    if (!isAsking && !locked && !over) askQuestion();
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
              : `Enter to send, Shift+Enter for a new line. Up to ${LIMITS.questionsPerHour} questions an hour. Follow-up questions work: the last ${LIMITS.sentHistoryTurns} questions are remembered until you refresh or clear history.`}
        </span>
        {!locked && nearLimit && <span className={`counter${over ? " is-over" : ""}`}>{length} / {LIMITS.questionChars}</span>}
      </p>
    </form>
  );
}
