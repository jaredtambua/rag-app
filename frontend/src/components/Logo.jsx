import { useId } from "react";

/* The Tessel mark: one outlined triangle with an iris-to-teal stroke, plus the wordmark. */
export default function Logo({ as: Tag = "span", ...rest }) {
  const gradient = useId();
  return (
    <Tag className="logo" {...rest}>
      <svg width="22" height="20" viewBox="0 0 22 20" aria-hidden="true">
        <defs>
          <linearGradient id={gradient} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#8052ff" />
            <stop offset="1" stopColor="#15846e" />
          </linearGradient>
        </defs>
        <path d="M11 1.5 20.5 18.5H1.5Z" fill="none" stroke={`url(#${gradient})`} strokeWidth="2" strokeLinejoin="round" />
      </svg>
      Tessel
    </Tag>
  );
}
