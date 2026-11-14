import { useEffect, useRef, useState } from "react";
import { CloseIcon } from "./icons.jsx";

/* A bottom sheet on the browser's own modal dialog: it traps focus, closes on Escape, locks the page behind it
   and hands focus back to the button that opened it. Dragging the grip down (or flicking it) closes it. */
export default function Sheet({ open, onClose, title, children }) {
  const ref = useRef(null);
  const start = useRef(null);
  const [offset, setOffset] = useState(0);
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  function onPointerDown(event) {
    event.currentTarget.setPointerCapture(event.pointerId);
    start.current = { y: event.clientY, t: event.timeStamp };
    setDragging(true);
  }
  function onPointerMove(event) {
    if (!start.current) return;
    setOffset(Math.max(0, event.clientY - start.current.y));
  }
  function onPointerUp(event) {
    if (!start.current) return;
    const distance = event.clientY - start.current.y;
    const speed = distance / Math.max(1, event.timeStamp - start.current.t);
    start.current = null;
    setDragging(false);
    setOffset(0);
    if (distance > 110 || speed > 0.6) onClose();
  }

  return (
    <dialog
      ref={ref}
      className="sheet"
      aria-label={title}
      data-dragging={dragging}
      style={offset ? { transform: `translateY(${offset}px)` } : undefined}
      onClose={onClose}
      onClick={(event) => { if (event.target === ref.current) onClose(); }}
    >
      <div className="sheet-top">
        <div
          className="sheet-grip"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
          aria-hidden="true"
        ><span /></div>
        <button className="icon-btn" type="button" aria-label="Close documents" onClick={onClose}><CloseIcon size={18} /></button>
      </div>
      {open && children}
    </dialog>
  );
}
