import { useEffect, useRef, useState } from "react";
import { CloseIcon, FileIcon, UploadIcon } from "./icons.jsx";
import { LIMITS, formatSize } from "./limits.js";

const STEPS = [
  { title: "Add a PDF", text: "A report, an article or a contract you know well." },
  { title: "Ask a question", text: "Use questions you can check yourself." },
  { title: "Check the sources", text: "Found answers show the pages they came from." },
];

/* Drifting outlines, drawn from triangles like the landing page. Each is [points, colour, size class]. */
const SHAPES = [
  ["28,6 52,48 4,48", "var(--iris)", "a"],
  ["20,4 38,36 2,36", "var(--saffron)", "b"],
  ["34,6 62,56 6,56", "var(--line-strong)", "c"],
  ["18,3 34,32 2,32", "var(--iris)", "d"],
  ["26,5 48,44 4,44", "var(--line-strong)", "e"],
  ["16,3 30,28 2,28", "var(--saffron)", "f"],
];

function Drift() {
  return (
    <div className="drift" aria-hidden="true">
      {SHAPES.map(([points, colour, name]) => (
        <svg key={name} className={`drift-${name}`} viewBox="0 0 64 60" fill="none" stroke={colour} strokeWidth="2" strokeLinejoin="round">
          <polygon points={points} />
        </svg>
      ))}
    </div>
  );
}

/* The conversation pane before any document exists: one clear place to add a PDF, then the three steps.
   The drop zone is a real button, so it works by mouse, drag and drop, keyboard and touch. */
export default function FirstRun({ selectedFiles, chooseFiles, uploadDocument, isUploading }) {
  const [dragging, setDragging] = useState(false);
  const zoneRef = useRef(null);
  const uploadRef = useRef(null);
  const inputRef = useRef(null);
  const ready = selectedFiles.length > 0 || isUploading;
  const wasReady = useRef(false);

  /* the zone is swapped for the ready card (and back): keep focus from falling to the page */
  useEffect(() => {
    const was = wasReady.current;
    wasReady.current = ready;
    if (was === ready) return;
    const active = document.activeElement;
    const lost = !active || active === document.body || active.tagName === "DIALOG";
    if (!lost) return;
    (ready ? uploadRef : zoneRef).current?.focus();
  }, [ready]);

  /* this screen has its own file input, so on a phone the chooser opens straight away (no drawer first) */
  function choose(files) {
    chooseFiles(files);
    if (inputRef.current) inputRef.current.value = "";
  }

  function onDrop(event) {
    event.preventDefault();
    setDragging(false);
    if (isUploading) return;
    const dropped = Array.from(event.dataTransfer.files);
    if (dropped.length > 0) choose(dropped);
  }

  function onDragLeave(event) {
    if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false);
  }

  return (
    <div className="firstrun">
      <header className="firstrun-head">
        <h2>Start with a document you know.</h2>
        <p>Test Tessel with questions you can check yourself.</p>
      </header>

      <div
        className={`drop${dragging ? " is-dragging" : ""}${ready ? " is-ready" : ""}`}
        onDragOver={(e) => { e.preventDefault(); if (!isUploading) setDragging(true); }}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          className="visually-hidden"
          type="file"
          accept="application/pdf"
          multiple
          tabIndex={-1}
          aria-hidden="true"
          disabled={isUploading}
          onChange={(event) => choose(Array.from(event.target.files))}
        />
        {!ready && <Drift />}
        {ready ? (
          <div className="drop-ready">
            <ul className="drop-files" aria-label="Files ready to upload">
              {selectedFiles.map((file) => (
                <li key={`${file.name}-${file.size}-${file.lastModified}`}>
                  <FileIcon size={18} />
                  <span className="name" title={file.name}>{file.name}</span>
                  <span className="size">{formatSize(file.size)}</span>
                </li>
              ))}
            </ul>
            {isUploading && (
              <div className="progress" role="status">
                <div className="bar" aria-hidden="true"><span /></div>
                <p>Uploading and reading your documents. Larger files can take a moment.</p>
              </div>
            )}
            <div className="drop-actions">
              <button ref={uploadRef} className="btn btn-primary" type="button" onClick={uploadDocument} disabled={isUploading}>
                {isUploading ? "Uploading..." : selectedFiles.length > 1 ? `Upload ${selectedFiles.length} PDFs` : "Upload PDF"}
              </button>
              {!isUploading && (
                <button className="btn btn-ghost btn-small" type="button" onClick={() => choose([])}>
                  <CloseIcon size={14} /> Clear
                </button>
              )}
            </div>
          </div>
        ) : (
          <button ref={zoneRef} className="drop-target" type="button" onClick={() => inputRef.current?.click()}>
            <span className="drop-icon" aria-hidden="true"><UploadIcon size={26} /></span>
            <span className="drop-main">{dragging ? "Drop your PDF to add it" : <><span className="when-pointer">Drop a PDF here</span><span className="when-touch">Tap to add a PDF</span></>}</span>
            <span className="btn btn-primary"><UploadIcon size={16} /> Add a PDF</span>
            <span className="drop-hint">
              PDF, up to {LIMITS.fileMb} MB and {LIMITS.pages} pages each. Up to {LIMITS.files} files, removed after {LIMITS.minutes} minutes.
            </span>
          </button>
        )}
      </div>

      <ol className="steps" aria-label="How it works">
        {STEPS.map((step, index) => (
          <li key={step.title}>
            <span className="step-no" aria-hidden="true">{index + 1}</span>
            <span className="step-body">
              <strong>{step.title}</strong>
              <span>{step.text}</span>
            </span>
          </li>
        ))}
      </ol>

      <p className="demo-note">This is a demo. Tessel as a product would keep your knowledge base, built from your own documents.</p>
    </div>
  );
}
