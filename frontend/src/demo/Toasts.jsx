import { useEffect, useState } from "react";
import { AlertIcon, CheckIcon, CloseIcon } from "./icons.jsx";

const NOTICE_MS = 5000;

/* A confirmation that clears itself. Hovering or focusing it holds it on screen, as Sonner does. */
function NoticeToast({ message, onDone }) {
  const [held, setHeld] = useState(false);

  useEffect(() => {
    if (held) return undefined;
    const timer = setTimeout(onDone, NOTICE_MS);
    return () => clearTimeout(timer);
  }, [held, message, onDone]);

  return (
    <div
      className="toast toast-ok"
      role="status"
      onMouseEnter={() => setHeld(true)}
      onMouseLeave={() => setHeld(false)}
      onFocus={() => setHeld(true)}
      onBlur={() => setHeld(false)}
    >
      <CheckIcon size={18} />
      <p>{message}</p>
      <button className="icon-btn" type="button" aria-label="Dismiss message" onClick={onDone}><CloseIcon size={16} /></button>
    </div>
  );
}

/* Errors stay until dismissed, because the visitor has to read them and act. */
export function ErrorAlert({ message, onDone }) {
  if (!message) return null;
  return (
    <div className="alert-wrap">
      <div className="alert" role="alert">
        <AlertIcon size={18} />
        <p>{message}</p>
        <button className="icon-btn" type="button" aria-label="Dismiss message" onClick={onDone}><CloseIcon size={16} /></button>
      </div>
    </div>
  );
}

export default function Toasts({ notice, onDismissNotice }) {
  return (
    <div className="toasts">
      {notice && <NoticeToast message={notice} onDone={onDismissNotice} />}
    </div>
  );
}
