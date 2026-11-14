/* The visitor ID: a random UUID this browser makes once and sends on every request (X-Visitor-Id).
   It is not a login. It only keeps one visitor's uploads apart from everyone else's.
   If storage is blocked the ID lives in memory, so the demo still works for the page session. */
const KEY = "tessel-visitor-id";
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

let memoryId = null;

function makeId() {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  /* randomUUID needs a secure page; build a version 4 UUID by hand otherwise */
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function getVisitorId() {
  if (memoryId) return memoryId;

  try {
    const stored = localStorage.getItem(KEY);
    if (stored && UUID.test(stored)) {
      memoryId = stored;
      return stored;
    }
  } catch {
    /* storage blocked: fall through to a fresh in-memory ID */
  }

  memoryId = makeId();
  try {
    localStorage.setItem(KEY, memoryId);
  } catch {
    /* keep the in-memory ID */
  }
  return memoryId;
}
