import { useState } from "react";
import { CloseIcon, FileIcon, UploadIcon } from "./icons.jsx";
import { LIMITS } from "./limits.js";

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/* Compact on purpose: the list below it is what needs the room. The Upload button only appears once
   files are picked, so the dropzone is the single action until then. */
export default function UploadPanel({ inputRef, selectedFiles, chooseFiles, uploadDocument, isUploading, full }) {
  const [dragging, setDragging] = useState(false);

  /* the file input is cleared after each choice so the same file can be picked again */
  function choose(files) {
    chooseFiles(files);
    if (inputRef.current) inputRef.current.value = "";
  }

  function onDrop(event) {
    event.preventDefault();
    setDragging(false);
    if (isUploading || full) return;
    const dropped = Array.from(event.dataTransfer.files);
    if (dropped.length > 0) choose(dropped);
  }

  return (
    <section className="upload" aria-label="Add documents">
      <label
        className={`dropzone${dragging ? " is-dragging" : ""}${isUploading ? " is-busy" : ""}${full ? " is-full" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          className="visually-hidden"
          type="file"
          accept="application/pdf"
          multiple
          disabled={isUploading || full}
          onChange={(event) => choose(Array.from(event.target.files))}
        />
        <UploadIcon size={22} />
        <span className="dropzone-text">
          <span className="dropzone-main">{full ? "File limit reached" : <>Drop PDFs or <span className="link-like">browse</span></>}</span>
          <span className="dropzone-hint">
            {full
              ? `You have ${LIMITS.files} files. Delete one to add another.`
              : `PDF, up to ${LIMITS.fileMb} MB and ${LIMITS.pages} pages each. Up to ${LIMITS.files} files.`}
          </span>
        </span>
      </label>

      {selectedFiles.length > 0 && (
        <ul className="picked" aria-label="Files ready to upload">
          {selectedFiles.map((file) => (
            <li key={`${file.name}-${file.size}-${file.lastModified}`}>
              <FileIcon size={16} />
              <span className="name" title={file.name}>{file.name}</span>
              <span className="size">{formatSize(file.size)}</span>
            </li>
          ))}
        </ul>
      )}

      {isUploading && (
        <div className="progress" role="status">
          <div className="bar" aria-hidden="true"><span /></div>
          <p>Uploading and reading your documents. Larger files can take a moment.</p>
        </div>
      )}

      {(selectedFiles.length > 0 || isUploading) && (
        <div className="upload-actions">
          <button className="btn btn-primary" type="button" onClick={uploadDocument} disabled={isUploading}>
            {isUploading ? "Uploading..." : selectedFiles.length > 1 ? `Upload ${selectedFiles.length} PDFs` : "Upload PDF"}
          </button>
          {!isUploading && (
            <button className="btn btn-ghost btn-small" type="button" onClick={() => choose([])}>
              <CloseIcon size={14} /> Clear
            </button>
          )}
        </div>
      )}
    </section>
  );
}
