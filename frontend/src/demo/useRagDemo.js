/* All the demo's state and API calls. The requests, payloads and error messages are unchanged from the
   original app; the screens only read what this hook returns. */
import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL;

export function useRagDemo() {
  const [documents, setDocuments] = useState([]);
  const [documentsStatus, setDocumentsStatus] = useState("loading"); // loading | ready | failed
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [question, setQuestion] = useState("");
  const [askedQuestion, setAskedQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [justUploaded, setJustUploaded] = useState(false);

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_URL}/documents`);
      const data = await response.json();
      setDocuments(data.documents || []);
      setDocumentsStatus("ready");
    } catch (err) {
      console.error("Load documents error:", err);
      setError("Could not load documents.");
      setDocumentsStatus("failed");
    }
  }

  /* load the document list once when the workspace opens */
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDocuments();
  }, []);

  /* choosing new files clears the "already uploaded" state, exactly as before */
  function chooseFiles(files) {
    setSelectedFiles(files);
    setJustUploaded(false);
    setNotice("");
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

      const response = await fetch(`${API_URL}/upload`, { method: "POST", body: formData });
      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Upload failed.");
        return;
      }

      if (data.skipped?.length > 0) {
        setError(data.skipped.map((item) => `${item.filename}: ${item.reason}`).join("\n"));
      }
      if (data.uploaded?.length > 0) {
        setNotice(data.uploaded.length === 1 ? `Added ${data.uploaded[0]}.` : `Added ${data.uploaded.length} documents.`);
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
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    setError("");
    setNotice("");
    setAnswer("");
    setCitations([]);
    setAskedQuestion(question);
    setIsAsking(true);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Could not answer question.");
        return;
      }

      setAnswer(data.answer);
      setCitations(data.citations || []);
    } catch (err) {
      console.error("Ask question error:", err);
      setError("Could not answer question.");
    } finally {
      setIsAsking(false);
    }
  }

  async function deleteDocument(filename) {
    setError("");
    setNotice("");

    try {
      const response = await fetch(`${API_URL}/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });
      if (!response.ok) {
        setError("Failed to delete document.");
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
    documents, documentsStatus,
    selectedFiles, chooseFiles, uploadDocument, isUploading,
    question, setQuestion, askQuestion, isAsking, askedQuestion,
    answer, citations,
    error, setError, notice, setNotice,
    deleteDocument,
  };
}
