import { DEMO_PATH } from "../routing.js";

/* A real link to the demo (so it can be opened in a new tab), that plays the page transition on a normal click. */
export default function DemoLink({ onNavigate, className = "btn btn-primary", children = "Try the Demo" }) {
  function handleClick(event) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    onNavigate(DEMO_PATH);
  }
  return (
    <a className={className} href={DEMO_PATH} onClick={handleClick}>
      {children}
    </a>
  );
}
