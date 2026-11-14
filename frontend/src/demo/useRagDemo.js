/* All the demo's state and API calls. Every request carries the visitor ID; the screens only read what this hook returns. */
import { useEffect, useMemo, useRef, useState } from "react";
import { getVisitorId } from "./visitor.js";
import { LIMITS, MAX_FILE_BYTES, MESSAGES } from "./limits.js";

const API_URL = import.meta.env.VITE_API_URL;

/* the time-left labels refresh this often */
const TICK_MS = 60_000;

/* The demo server sleeps when idle and can take a minute to wake. These are the waiting rules. */
const WAKING_AFTER_MS = 4_000;
const RETRY_EVERY_MS = 5_000;
const GIVE_UP_AFTER_MS = 90_000;

const isPdf = (file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

function request(path, options = {}) {
  const headers = { ...options.headers, "X-Visitor-Id": getVisitorId() };
  return fetch(`${API_URL}${path}`, { ...options, headers });
}

/* One quiet check that the server answers. Never throws, and never needs a visitor ID. */
async function pingHealth(timeoutMs = RETRY_EVERY_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_URL}/health`, { signal: controller.signal });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

/* Called when the landing page opens so the server is already awake when someone clicks "Try the demo". Failures are silent. */
export function warmUpServer() {
  pingHealth(60_000);
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/* The backend's own message is shown for any refusal. A rate limit without a time in its message gets the retry time added. */
async function problemFrom(response, fallback) {
  let detail = "";
  try {
    const data = await response.json();
    if (typeof data.detail === "string") detail = data.detail;
  } catch {
    /* the body was not JSON: use the fallback */
  }

  if (!detail) return response.status === 413 ? MESSAGES.tooBig : fallback;

  const wait = Number(response.headers.get("Retry-After"));
  if (response.status === 429 && wait > 0 && !/minute/i.test(detail)) {
    detail += ` Try again in about ${Math.max(1, Math.ceil(wait / 60))} minute${wait > 60 ? "s" : ""}.`;
  }
  return detail;
}

export function useRagDemo() {
  /* the list as the server last sent it, and when it arrived; time left is worked out from these */
  const [listing, setListing] = useState({ items: [], receivedAt: 0 });
  const [now, setNow] = useState(() => Date.now());
  const [documentsStatus, setDocumentsStatus] = useState("loading"); // loading | ready | failed
  const [waking, setWaking] = useState(false); // true once the server has been slow for a few seconds
  const connectRun = useRef(0);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [question, setQuestion] = useState("");
  /* the latest question and what came of it: { question, answer, citations, failedMessage } */
  const [turn, setTurn] = useState(null);
  const [pendingQuestion, setPendingQuestion] = useState("");
  const seenIds = useRef(new Set());
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [justUploaded, setJustUploaded] = useState(false);

  /* files that have run out of time drop off the list without any error */
  const documents = useMemo(
    () =>
      listing.items
        .map((item) => ({ ...item, secondsLeft: item.seconds_left - (now - listing.receivedAt) / 1000 }))
        .filter((item) => item.secondsLeft > 0),
    [listing, now],
  );

  /* `quiet` refreshes (after an expiry) never show an error */
  async function loadDocuments({ quiet = false } = {}) {
    try {
      const response = await request("/documents");
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      setListing({ items: data.documents || [], receivedAt: Date.now() });
      setNow(Date.now());
      setDocumentsStatus("ready");
    } catch (err) {
      console.error("Load documents error:", err);
      if (quiet) return;
      /* the screen explains this itself, with a Try again button, so no separate banner */
      setDocumentsStatus("failed");
    }
  }

  /* Wait for the server to answer /health (showing a waking message if it is slow, retrying quietly), then load the list. */
  async function connect() {
    const run = ++connectRun.current;
    const current = () => run === connectRun.current;
    const started = Date.now();
    const wakingTimer = setTimeout(() => current() && setWaking(true), WAKING_AFTER_MS);

    setDocumentsStatus("loading");
    setWaking(false);
    setError("");

    try {
      while (current()) {
        const attemptStarted = Date.now();
        const up = await pingHealth();
        if (!current()) return;

        if (up) {
          setWaking(false);
          await loadDocuments();
          return;
        }

        if (Date.now() - started >= GIVE_UP_AFTER_MS) {
          setWaking(false);
          setDocumentsStatus("failed");
          return;
        }

        await wait(Math.max(0, RETRY_EVERY_MS - (Date.now() - attemptStarted)));
      }
    } finally {
      clearTimeout(wakingTimer);
    }
  }

  /* connect when the workspace opens; leaving the page stops any waiting */
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    connect();
    return () => { connectRun.current += 1; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* An answer that cites a document is dropped when any document is deleted or runs out of time. */
  useEffect(() => {
    const ids = new Set(documents.map((doc) => doc.id));
    const removed = [...seenIds.current].some((id) => !ids.has(id));
    seenIds.current = ids;
    if (removed) setTurn(null);
  }, [documents]);

  /* once a minute, refresh the time-left labels */
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(timer);
  }, []);

  /* when the soonest file runs out, drop it from view and ask the server for the true list */
  useEffect(() => {
    if (listing.items.length === 0) return undefined;
    const soonest = Math.min(...listing.items.map((item) => item.seconds_left));
    const wait = soonest * 1000 - (Date.now() - listing.receivedAt) + 400;
    const timer = setTimeout(() => {
      setNow(Date.now());
      loadDocuments({ quiet: true });
    }, Math.max(wait, 400));
    return () => clearTimeout(timer);
  }, [listing]);

  /* choosing files checks the limits in the browser first; the server still decides */
  function chooseFiles(files) {
    setJustUploaded(false);
    setNotice("");
    setError(""); /* an old refusal must not outlive the choice that caused it */

    const problems = [];
    let accepted = files.filter((file) => {
      if (!isPdf(file)) {
        problems.push(`${file.name}: ${MESSAGES.notPdf}`);
        return false;
      }
      if (file.size > MAX_FILE_BYTES) {
        problems.push(`${file.name}: ${MESSAGES.tooBig}`);
        return false;
      }
      return true;
    });

    const room = Math.max(0, LIMITS.files - documents.length);
    if (accepted.length > room) {
      problems.push(MESSAGES.tooManyFiles);
      accepted = accepted.slice(0, room);
    }

    setSelectedFiles(accepted);
    if (problems.length > 0) setError(problems.join("\n"));
  }

  async function uploadDocument() {
    if (selectedFiles.length === 0) {
      setError(justUploaded ? "Upload complete. Please select a new file." : "Please choose at least one PDF first.");
      return;
    }

    setError("");
    setNotice("");
    setIsUploading(true);

    try {
      const formData = new FormData();
      selectedFiles.forEach((file) => formData.append("files", file));

      const response = await request("/upload", { method: "POST", body: formData });

      if (!response.ok) {
        setError(await problemFrom(response, "Upload failed."));
        return;
      }

      const data = await response.json();

      if (data.skipped?.length > 0) {
        setError(data.skipped.map((item) => `${item.filename}: ${item.reason}`).join("\n"));
      }
      if (data.uploaded?.length > 0) {
        const what = data.uploaded.length === 1 ? data.uploaded[0] : `${data.uploaded.length} documents`;
        setNotice(`Added ${what}. ${data.uploaded.length === 1 ? "It" : "They"} will be removed after ${LIMITS.minutes} minutes.`);
      }

      setSelectedFiles([]);
      setJustUploaded(true);
      await loadDocuments();
    } catch (err) {
      console.error("Upload error:", err);
      setError("Could not upload documents.");
    } finally {
      setIsUploading(false);
    }
  }

  async function askQuestion() {
    const trimmed = question.trim();

    if (!trimmed) {
      setError("Please enter a question.");
      return;
    }
    if (trimmed.length > LIMITS.questionChars) {
      setError(MESSAGES.questionTooLong);
      return;
    }

    setError("");
    setNotice("");
    setPendingQuestion(question);
    setIsAsking(true);

    try {
      const response = await request("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        const message = await problemFrom(response, "Could not answer question.");
        if (response.status >= 500) {
          /* a fault on our side: the answer area says so and invites a retry */
          setTurn({ question, answer: "", citations: [], failedMessage: message });
        } else {
          /* a refusal (such as the hourly limit): the banner explains and the previous answer stays */
          setError(message);
        }
        return;
      }

      const data = await response.json();
      setTurn({ question, answer: data.answer, citations: data.citations || [], failedMessage: "" });
    } catch (err) {
      console.error("Ask question error:", err);
      setTurn({ question, answer: "", citations: [], failedMessage: "Could not reach the demo server." });
    } finally {
      setIsAsking(false);
    }
  }

  async function deleteDocument(id) {
    setError("");
    setNotice("");

    try {
      const response = await request(`/documents/${encodeURIComponent(id)}`, { method: "DELETE" });
      /* a 404 means it already expired: the refresh below makes the list right, with no error */
      if (!response.ok && response.status !== 404) {
        setError(await problemFrom(response, "Failed to delete document."));
        return;
      }
    } catch (err) {
      console.error("Delete document error:", err);
      setError("Failed to delete document.");
      return;
    }

    await loadDocuments();
  }

  return {
    documents, documentsStatus, waking, retryConnect: connect,
    selectedFiles, chooseFiles, uploadDocument, isUploading,
    question, setQuestion, askQuestion, isAsking,
    hasTurn: Boolean(turn) || isAsking,
    askedQuestion: isAsking ? pendingQuestion : turn?.question || "",
    answer: turn?.answer || "",
    citations: turn?.citations || [],
    failedMessage: turn?.failedMessage || "",
    error, setError, notice, setNotice,
    deleteDocument,
  };
}
