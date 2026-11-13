import { useEffect, useRef } from "react";
import Logo from "../components/Logo.jsx";
import { BackIcon, AlertIcon, CloseIcon } from "./icons.jsx";
import { useRagDemo } from "./useRagDemo.js";
import UploadPanel from "./UploadPanel.jsx";
import DocumentList from "./DocumentList.jsx";
import AskPanel from "./AskPanel.jsx";
import AnswerPanel from "./AnswerPanel.jsx";
import "./demo.css";

const STEPS = ["Add a PDF", "Ask a question", "Check the source"];

/* which step the visitor is on, worked out from what exists so far */
function currentStep({ documents, answer, isAsking }) {
  if (documents.length === 0) return 0;
  return answer && !isAsking ? 2 : 1;
}

function Steps({ active }) {
  return (
    <ol className="steps" aria-label="How the demo works">
      {STEPS.map((label, i) => (
        <li key={label} aria-current={i === active ? "step" : undefined} data-done={i < active}>
          <span className="step-num">{i + 1}</span>
          {label}
        </li>
      ))}
    </ol>
  );
}

function ErrorBanner({ error, onDismiss }) {
  const ref = useRef(null);
  /* on a phone the message can be above the button that caused it, so bring it into view */
  useEffect(() => {
    ref.current?.scrollIntoView({ block: "nearest" });
  }, [error]);
  if (!error) return null;
  return (
    <div className="error-banner" role="alert" ref={ref}>
      <AlertIcon size={20} />
      <p>{error}</p>
      <button className="icon-btn" type="button" aria-label="Dismiss message" onClick={onDismiss}><CloseIcon size={16} /></button>
    </div>
  );
}

export default function Workspace({ onNavigate }) {
  const demo = useRagDemo();
  const hasDocuments = demo.documents.length > 0;
  const firstRun = demo.documentsStatus !== "loading" && !hasDocuments;

  return (
    <div className="demo">
      <header className="demo-top">
        <a className="logo-link" href="#/" aria-label="Tessel home" onClick={(e) => { e.preventDefault(); onNavigate("#/"); }}><Logo /></a>
        <span className="demo-label">Demo workspace</span>
        <a className="btn btn-ghost btn-small back" href="#/" onClick={(e) => { e.preventDefault(); onNavigate("#/"); }}>
          <BackIcon size={14} /> Back to site
        </a>
      </header>

      <main className="workspace" id="main">
        <div className="intro">
          <h1>{firstRun ? "Start with a document." : "Ask your documents anything."}</h1>
          <p>
            {firstRun
              ? "Add a PDF on the left. Once it is in, ask a question and Tessel will answer and cite the pages it used. This demo shares one document store, so don’t upload anything sensitive."
              : "Ask in plain words. Answers cite the pages and passages they used."}
          </p>
        </div>

        <Steps active={currentStep(demo)} />
        <ErrorBanner error={demo.error} onDismiss={() => demo.setError("")} />

        <div className="grid">
          <div className="col">
            <UploadPanel
              selectedFiles={demo.selectedFiles}
              chooseFiles={demo.chooseFiles}
              uploadDocument={demo.uploadDocument}
              isUploading={demo.isUploading}
              notice={demo.notice}
              setError={demo.setError}
            />
            <DocumentList documents={demo.documents} status={demo.documentsStatus} deleteDocument={demo.deleteDocument} />
          </div>
          <div className="col">
            <AskPanel
              question={demo.question}
              setQuestion={demo.setQuestion}
              askQuestion={demo.askQuestion}
              isAsking={demo.isAsking}
              hasDocuments={hasDocuments}
            />
            <AnswerPanel answer={demo.answer} citations={demo.citations} isAsking={demo.isAsking} askedQuestion={demo.askedQuestion} />
          </div>
        </div>
      </main>
    </div>
  );
}
