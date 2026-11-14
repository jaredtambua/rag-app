import { useRef, useState } from "react";
import { FileIcon, SearchIcon, TrashIcon } from "./icons.jsx";
import { formatTimeLeft } from "./limits.js";

const SEARCH_FROM = 8; // below this many files a search box is just clutter

export default function DocumentList({ documents, status, deleteDocument, retryConnect }) {
  const [query, setQuery] = useState("");
  const listRef = useRef(null);
  const showSearch = documents.length >= SEARCH_FROM;
  const needle = showSearch ? query.trim().toLowerCase() : "";
  const shown = needle ? documents.filter((doc) => doc.name.toLowerCase().includes(needle)) : documents;

  /* the focused delete button disappears with its row, so keep keyboard focus on the list */
  async function remove(id) {
    listRef.current?.focus();
    await deleteDocument(id);
  }

  return (
    <div className="docs-wrap">
      {status === "failed" && documents.length === 0 && (
        <div className="empty">
          <p>Documents could not be loaded.</p>
          <button className="btn btn-ghost btn-small retry" type="button" onClick={retryConnect}>Try again</button>
        </div>
      )}

      {status === "ready" && documents.length === 0 && (
        <p className="empty">Nothing here yet. Added PDFs will be listed here, each with the time it has left.</p>
      )}

      {showSearch && (
        <div className="search">
          <SearchIcon size={16} />
          <label className="visually-hidden" htmlFor="doc-search">Search documents</label>
          <input id="doc-search" type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search documents" autoComplete="off" />
        </div>
      )}

      {documents.length > 0 && (
        <ul className="docs" ref={listRef} tabIndex={-1} aria-label="Your documents">
          {shown.map((doc) => (
            <li key={doc.id}>
              <FileIcon size={18} />
              <span className="doc-text">
                <span className="name" title={doc.name}>{doc.name}</span>
                <span className={`time-left${doc.secondsLeft < 300 ? " is-soon" : ""}`}>{formatTimeLeft(doc.secondsLeft)}</span>
              </span>
              <button className="icon-btn" type="button" aria-label={`Delete ${doc.name}`} onClick={() => remove(doc.id)}>
                <TrashIcon size={16} />
              </button>
            </li>
          ))}
          {shown.length === 0 && <li className="empty no-match">No document matches &ldquo;{query.trim()}&rdquo;.</li>}
        </ul>
      )}
    </div>
  );
}
