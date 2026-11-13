import { FileIcon, TrashIcon } from "./icons.jsx";

export default function DocumentList({ documents, status, deleteDocument }) {
  return (
    <section className="panel" aria-labelledby="docs-title">
      <div className="panel-head">
        <h2 id="docs-title" className="panel-title">Your documents</h2>
        <span className="count" aria-label={`${documents.length} documents`}>{documents.length}</span>
      </div>

      {status === "loading" && <WakeNotice />}

      {status === "failed" && documents.length === 0 && (
        <p className="empty">Documents could not be loaded. Check your connection and refresh the page.</p>
      )}

      {status === "ready" && documents.length === 0 && (
        <p className="empty">Nothing here yet. Add a PDF above and it will appear in this list.</p>
      )}

      {documents.length > 0 && (
        <ul className="docs">
          {documents.map((name) => (
            <li key={name}>
              <FileIcon size={18} />
              <span className="name">{name}</span>
              <button className="icon-btn" type="button" aria-label={`Delete ${name}`} onClick={() => deleteDocument(name)}>
                <TrashIcon size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/* shown while the first request is out; the demo server can be slow to wake up */
function WakeNotice() {
  return (
    <div className="progress" role="status">
      <div className="bar" aria-hidden="true"><span /></div>
      <p>Connecting to the demo server. If it has been idle it may take a minute to wake up.</p>
    </div>
  );
}
