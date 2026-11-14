import { useRef, useState } from "react";
import { FileIcon, SearchIcon, TrashIcon } from "./icons.jsx";

const SEARCH_FROM = 8; // below this many files a search box is just clutter

export default function DocumentList({ documents, status, deleteDocument }) {
  const [query, setQuery] = useState("");
  const listRef = useRef(null);
  const showSearch = documents.length >= SEARCH_FROM;
  const needle = showSearch ? query.trim().toLowerCase() : "";
  const shown = needle ? documents.filter((name) => name.toLowerCase().includes(needle)) : documents;

  /* the focused delete button disappears with its row, so keep keyboard focus on the list */
  async function remove(name) {
    listRef.current?.focus();
    await deleteDocument(name);
  }

  return (
    <div className="docs-wrap">
      {status === "loading" && <WakeNotice />}

      {status === "failed" && documents.length === 0 && (
        <p className="empty">Documents could not be loaded. Check your connection and refresh the page.</p>
      )}

      {status === "ready" && documents.length === 0 && (
        <p className="empty">Nothing here yet. Added PDFs will be listed here.</p>
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
          {shown.map((name) => (
            <li key={name}>
              <FileIcon size={18} />
              <span className="name" title={name}>{name}</span>
              <button className="icon-btn" type="button" aria-label={`Delete ${name}`} onClick={() => remove(name)}>
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

/* shown while the first request is out; the demo server can be slow to wake up */
function WakeNotice() {
  return (
    <div className="progress" role="status">
      <div className="bar" aria-hidden="true"><span /></div>
      <p>Connecting to the demo server. If it has been idle it may take a minute to wake up.</p>
    </div>
  );
}
