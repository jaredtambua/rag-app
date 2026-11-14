import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import Logo from "../components/Logo.jsx";
import { BackIcon, FileIcon } from "./icons.jsx";
import { useRagDemo } from "./useRagDemo.js";
import Sidebar from "./Sidebar.jsx";
import Sheet from "./Sheet.jsx";
import Toasts, { ErrorAlert } from "./Toasts.jsx";
import EmptyState from "./EmptyState.jsx";
import AskPanel from "./AskPanel.jsx";
import Thread, { ThreadBar } from "./Thread.jsx";
import { LIMITS } from "./limits.js";
import "./demo.css";

/* below this width the documents column becomes a sheet opened from the top bar */
const COMPACT = "(max-width: 860px)";

function useMediaQuery(query) {
  return useSyncExternalStore(
    (notify) => {
      const list = window.matchMedia(query);
      list.addEventListener("change", notify);
      return () => list.removeEventListener("change", notify);
    },
    () => window.matchMedia(query).matches,
    () => false,
  );
}

export default function Workspace({ onNavigate }) {
  const demo = useRagDemo();
  const compact = useMediaQuery(COMPACT);
  const [sheetOpen, setSheetOpen] = useState(false);
  const inputRef = useRef(null);
  const questionRef = useRef(null);

  const count = demo.documents.length;
  const loading = demo.documentsStatus === "loading";
  const failed = demo.documentsStatus === "failed";
  const firstRun = demo.documentsStatus === "ready" && count === 0;
  /* the ask box opens once the server is up and there is a document to ask about */
  const askLocked = loading || failed || firstRun;
  const turnCount = demo.thread.filter((item) => item.kind === "turn").length;
  const hasTurn = turnCount > 0;

  /* on a wide screen the file picker is already on the page; on a phone it lives in the sheet */
  function pickFile() {
    if (compact) setSheetOpen(true);
    else inputRef.current?.click();
  }

  /* Try again and Clear history remove the button that had focus: put it back in the question box */
  function retry(id) {
    demo.retryTurn(id);
    questionRef.current?.focus();
  }

  function clearHistory() {
    demo.clearHistory();
    questionRef.current?.focus();
  }

  function fillExample(text) {
    demo.setQuestion(text);
    questionRef.current?.focus();
  }

  const sheetShown = compact && sheetOpen;
  const { error, setError, isUploading } = demo;
  const clearError = () => setError("");

  /* Escape dismisses the red banner (a drawer that is open keeps Escape for itself) */
  useEffect(() => {
    if (!error || sheetShown) return undefined;
    const onKey = (event) => { if (event.key === "Escape") setError(""); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [error, sheetShown, setError]);

  /* After an upload, or after the last file is deleted, the button that had focus is gone: put focus somewhere useful */
  const wasUploading = useRef(false);
  const lastCount = useRef(0);
  useEffect(() => {
    const finishedUpload = wasUploading.current && !isUploading;
    const deletedLast = lastCount.current > 0 && count === 0;
    wasUploading.current = isUploading;
    lastCount.current = count;
    if (!finishedUpload && !deletedLast) return;
    const active = document.activeElement;
    const lost = !active || active === document.body || active.tagName === "DIALOG";
    if (!lost) return;
    if (count < LIMITS.files) inputRef.current?.focus();
    else if (!sheetShown) questionRef.current?.focus();
  }, [isUploading, count, sheetShown]);

  const goHome = (event) => { event.preventDefault(); onNavigate("#/"); };

  return (
    <div className="demo">
      <header className="demo-top">
        <a className="logo-link" href="#/" aria-label="Tessel home" onClick={goHome}><Logo /></a>
        <span className="demo-label">Demo workspace</span>
        {compact && (
          <button className="btn btn-ghost btn-small docs-btn" type="button" aria-haspopup="dialog" aria-label={`Documents, ${count}`} onClick={() => setSheetOpen(true)}>
            <FileIcon size={14} /> <span className="label">Documents</span> <span className="count">{count}</span>
          </button>
        )}
        <a className="btn btn-ghost btn-small back" href="#/" aria-label="Back to site" onClick={goHome}>
          <BackIcon size={14} /> <span className="label">Back to site</span>
        </a>
      </header>

      {/* on a wide screen the message floats; on a phone it sits above the ask box (or in the drawer) so it never covers an answer */}
      {!compact && <Toasts notice={demo.notice} onDismissNotice={() => demo.setNotice("")} />}

      <div className="layout">
        {!compact && (
          <aside className="side-col" aria-label="Documents">
            <Sidebar demo={demo} inputRef={inputRef} />
          </aside>
        )}

        <main className="pane" id="main">
          <h1 className="visually-hidden">Tessel demo workspace</h1>
          {!sheetShown && <ErrorAlert message={error} onDone={clearError} />}
          {hasTurn && <ThreadBar count={turnCount} disabled={demo.isAsking} onClear={clearHistory} />}
          <div className="thread">
            <div className="thread-inner">
              {hasTurn
                ? <Thread items={demo.thread} isAsking={demo.isAsking} onRetry={retry} onAddPdf={pickFile} noDocuments={firstRun} />
                : <EmptyState loading={loading} waking={demo.waking} failed={failed} onRetry={demo.retryConnect} firstRun={firstRun} count={count} onPick={pickFile} onExample={fillExample} />}
            </div>
          </div>
          <div className="dock">
            <div className="dock-inner">
              {compact && !sheetShown && <Toasts inline notice={demo.notice} onDismissNotice={() => demo.setNotice("")} />}
              <AskPanel
                question={demo.question}
                setQuestion={demo.setQuestion}
                askQuestion={demo.askQuestion}
                isAsking={demo.isAsking}
                locked={askLocked}
                lockedHint={loading ? "Questions open up once the demo server is ready." : failed ? "Questions open up once the demo server answers." : undefined}
                textareaRef={questionRef}
              />
            </div>
          </div>
        </main>
      </div>

      {compact && (
        <Sheet open={sheetOpen} onClose={() => setSheetOpen(false)} title="Documents">
          <Toasts inline notice={demo.notice} onDismissNotice={() => demo.setNotice("")} />
          <ErrorAlert message={demo.error} onDone={clearError} />
          <Sidebar demo={demo} inputRef={inputRef} />
        </Sheet>
      )}
    </div>
  );
}
