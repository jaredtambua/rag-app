import { UploadIcon } from "./icons.jsx";

const EXAMPLES = ["Summarise this document", "What are the key points?", "What does it say about risks?"];

/* What the conversation pane shows before the first question: first run guides to an upload, later it offers a start. */
export default function EmptyState({ loading, firstRun, compact, count, onPick, onExample }) {
  if (loading) return <div className="empty-state" />;

  if (firstRun) {
    return (
      <div className="empty-state">
        <h2>Start with a document.</h2>
        <p>Add a PDF, ask a question about it, and Tessel answers with the pages it used.{compact && " This demo shares one document store, so don’t upload anything sensitive."}</p>
        <ol className="how">
          <li><span>1</span>Add a PDF</li>
          <li><span>2</span>Ask a question</li>
          <li><span>3</span>Check the sources</li>
        </ol>
        <button className="btn btn-primary" type="button" onClick={onPick}><UploadIcon size={16} /> Add a PDF</button>
      </div>
    );
  }

  return (
    <div className="empty-state">
      <h2>{count === 1 ? "Ask your document anything." : count > 1 ? `Ask your ${count} documents anything.` : "Ask your documents anything."}</h2>
      <p>Ask in plain words. Answers cite the pages and passages they used.</p>
      <div className="chips" role="group" aria-label="Example questions">
        {EXAMPLES.map((text) => (
          <button key={text} className="chip" type="button" onClick={() => onExample(text)}>{text}</button>
        ))}
      </div>
    </div>
  );
}
