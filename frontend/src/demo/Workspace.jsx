import { useRef, useState, useSyncExternalStore } from "react";
import Logo from "../components/Logo.jsx";
import { BackIcon, FileIcon } from "./icons.jsx";
import { useRagDemo } from "./useRagDemo.js";
import Sidebar from "./Sidebar.jsx";
import Sheet from "./Sheet.jsx";
import Toasts, { ErrorAlert } from "./Toasts.jsx";
import EmptyState from "./EmptyState.jsx";
import AskPanel from "./AskPanel.jsx";
import AnswerPanel from "./AnswerPanel.jsx";
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
  const firstRun = demo.documentsStatus === "ready" && count === 0;
  const hasTurn = Boolean(demo.askedQuestion);

  /* on a wide screen the file picker is already on the page; on a phone it lives in the sheet */
  function pickFile() {
    if (compact) setSheetOpen(true);
    else inputRef.current?.click();
  }

  function fillExample(text) {
    demo.setQuestion(text);
    questionRef.current?.focus();
  }

  const sheetShown = compact && sheetOpen;
  const clearError = () => demo.setError("");

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
        <a className="btn btn-ghost btn-small back" href="#/" onClick={goHome}>
          <BackIcon size={14} /> Back to site
        </a>
      </header>

      <Toasts
        notice={demo.notice}
        onDismissNotice={() => demo.setNotice("")}
      />

      <div className="layout">
        {!compact && (
          <aside className="side-col" aria-label="Documents">
            <Sidebar demo={demo} inputRef={inputRef} />
          </aside>
        )}

        <main className="pane" id="main">
          <h1 className="visually-hidden">Tessel demo workspace</h1>
          {!sheetShown && <ErrorAlert message={demo.error} onDone={clearError} />}
          <div className="thread">
            <div className="thread-inner">
              {hasTurn
                ? <AnswerPanel answer={demo.answer} citations={demo.citations} isAsking={demo.isAsking} askedQuestion={demo.askedQuestion} />
                : <EmptyState loading={loading} firstRun={firstRun} compact={compact} count={count} onPick={pickFile} onExample={fillExample} />}
            </div>
          </div>
          <div className="dock">
            <div className="dock-inner">
              <AskPanel
                question={demo.question}
                setQuestion={demo.setQuestion}
                askQuestion={demo.askQuestion}
                isAsking={demo.isAsking}
                locked={firstRun}
                textareaRef={questionRef}
              />
            </div>
          </div>
        </main>
      </div>

      {compact && (
        <Sheet open={sheetOpen} onClose={() => setSheetOpen(false)} title="Documents">
          <ErrorAlert message={demo.error} onDone={clearError} />
          <Sidebar demo={demo} inputRef={inputRef} />
        </Sheet>
      )}
    </div>
  );
}
