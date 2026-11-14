import UploadPanel from "./UploadPanel.jsx";
import DocumentList from "./DocumentList.jsx";
import { LIMITS } from "./limits.js";

/* The documents column: add on top, the list in the middle (the only part that scrolls), the honest warning at the foot. */
export default function Sidebar({ demo, inputRef }) {
  const count = demo.documents.length;
  return (
    <div className="side">
      <div className="side-head">
        <h2>Documents</h2>
        <span className="count" aria-live="polite" aria-label={`${count} documents`}>{count}</span>
      </div>
      <UploadPanel
        inputRef={inputRef}
        selectedFiles={demo.selectedFiles}
        chooseFiles={demo.chooseFiles}
        uploadDocument={demo.uploadDocument}
        isUploading={demo.isUploading}
        full={count >= LIMITS.files}
      />
      <DocumentList documents={demo.documents} status={demo.documentsStatus} deleteDocument={demo.deleteDocument} retryConnect={demo.retryConnect} />
      <p className="side-warn">Uploads are private to this browser, read by an AI service to answer you, and removed {LIMITS.minutes} minutes after you add them.</p>
    </div>
  );
}
