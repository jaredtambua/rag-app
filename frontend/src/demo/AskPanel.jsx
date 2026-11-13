import { SendIcon } from "./icons.jsx";

const EXAMPLES = ["Summarise this document", "What are the key points?", "What does it say about risks?"];

export default function AskPanel({ question, setQuestion, askQuestion, isAsking, hasDocuments }) {
  function onKeyDown(event) {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && !isAsking) {
      event.preventDefault();
      askQuestion();
    }
  }

  return (
    <section className="panel" aria-labelledby="ask-title">
      <h2 id="ask-title" className="panel-title">2. Ask a question</h2>

      <label className="visually-hidden" htmlFor="question">Your question</label>
      <textarea
        id="question"
        rows="4"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Example: What accuracy did the classifier achieve?"
      />

      <div className="chips" aria-label="Example questions">
        {EXAMPLES.map((text) => (
          <button key={text} className="chip" type="button" onClick={() => setQuestion(text)}>{text}</button>
        ))}
      </div>

      <div className="row">
        <button className="btn btn-primary" type="button" onClick={askQuestion} disabled={isAsking}>
          {isAsking ? "Thinking..." : "Ask"} {!isAsking && <SendIcon size={16} />}
        </button>
        <span className="hint">
          {hasDocuments ? "Press Ctrl+Enter to send." : "Add a PDF first, then ask about it."}
        </span>
      </div>
    </section>
  );
}
