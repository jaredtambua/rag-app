/* Small line icons drawn to match the Tessel look (2px strokes, rounded joins). */
function Icon({ children, size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {children}
    </svg>
  );
}

export const FileIcon = (p) => <Icon {...p}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5" /></Icon>;
export const UploadIcon = (p) => <Icon {...p}><path d="M12 16V4" /><path d="m7 9 5-5 5 5" /><path d="M5 20h14" /></Icon>;
export const TrashIcon = (p) => <Icon {...p}><path d="M4 7h16" /><path d="M9 7V4h6v3" /><path d="m6 7 1 13h10l1-13" /></Icon>;
export const SendIcon = (p) => <Icon {...p}><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></Icon>;
export const BackIcon = (p) => <Icon {...p}><path d="M19 12H5" /><path d="m11 6-6 6 6 6" /></Icon>;
export const AlertIcon = (p) => <Icon {...p}><path d="M12 3 2.5 20h19z" /><path d="M12 10v4" /><path d="M12 17.5v.01" /></Icon>;
export const CheckIcon = (p) => <Icon {...p}><path d="m5 12 5 5 9-10" /></Icon>;
export const CloseIcon = (p) => <Icon {...p}><path d="M6 6l12 12" /><path d="M18 6 6 18" /></Icon>;

export const SearchIcon = (p) => <Icon {...p}><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></Icon>;
