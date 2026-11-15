import FirstRun from "./FirstRun.jsx";

const EXAMPLES = ["Summarise this document", "What are the key points?", "What does it say about risks?"];

/* What the conversation pane shows before the first question: first run guides to an upload, later it offers a start. */
export default function EmptyState({ loading, waking, failed, onRetry, firstRun, count, onExample, upload }) {
  if (loading) {
    return (
      <div className="empty-state">
        <div className="progress" role="status">
          <div className="bar" aria-hidden="true"><span /></div>
          <p>{waking ? "The demo server is waking up, this can take up to a minute." : "Connecting to the demo server."}</p>
        </div>
      </div>
    );
  }

  if (failed) {
    return (
      <div className="empty-state">
        <h2>The demo server is not answering.</h2>
        <p>It may still be starting up. Give it a moment, then try again.</p>
        <button className="btn btn-primary" type="button" onClick={onRetry}>Try again</button>
      </div>
    );
  }

  if (firstRun) return <FirstRun {...upload} />;

  return (
    <div className="empty-state">
      <h2>{count === 1 ? "Ask your document anything." : count > 1 ? `Ask your ${count}\u00a0documents anything.` : "Ask your documents anything."}</h2>
      <p>Ask in plain words. Answers cite the pages and passages they used.</p>
      <div className="chips" role="group" aria-label="Example questions">
        {EXAMPLES.map((text) => (
          <button key={text} className="chip" type="button" onClick={() => onExample(text)}>{text}</button>
        ))}
      </div>
    </div>
  );
}
