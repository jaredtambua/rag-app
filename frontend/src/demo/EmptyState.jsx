import { UploadIcon } from "./icons.jsx";

const EXAMPLES = ["Summarise this document", "What are the key points?", "What does it say about risks?"];

/* What the conversation pane shows before the first question: first run guides to an upload, later it offers a start. */
export default function EmptyState({ loading, waking, failed, onRetry, firstRun, count, onPick, onExample }) {
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

  if (firstRun) {
    return (
      <div className="empty-state">
        <h2>Start with a document you know.</h2>
        <p>Add a PDF you know well, such as a report, an article or a contract, then test Tessel with questions you can check yourself. Answers cite the pages they used.</p>
        <ol className="how">
          <li><span>1</span>Add a PDF</li>
          <li><span>2</span>Ask a question</li>
          <li><span>3</span>Check the sources</li>
        </ol>
        <button className="btn btn-primary" type="button" onClick={onPick}><UploadIcon size={16} /> Add a PDF</button>
        <p className="demo-note">This is a demo. Tessel as a product would keep your knowledge base, built from your own documents.</p>
      </div>
    );
  }

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
