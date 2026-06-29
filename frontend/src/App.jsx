import { useEffect, useState } from "react";
import ErrorAlert from "./components/ErrorAlert";
import UploadCard from "./components/UploadCard";
import DocumentsCard from "./components/DocumentsCard";
import AskCard from "./components/AskCard";
import AnswerCard from "./components/AnswerCard";

const API_URL = "http://127.0.0.1:8000";

function App() {
    const [documents, setDocuments] = useState([]);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [sources, setSources] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [isAsking, setIsAsking] = useState(false);
    const [error, setError] = useState("");
	const [justUploaded, setJustUploaded] = useState(false);

    useEffect(() => {
        loadDocuments();
    }, []);

    // console.log("hi");

    async function loadDocuments() {
        try {
            const response = await fetch(`${API_URL}/documents`);
            const data = await response.json();

            console.log("Loaded documents:", data);

            setDocuments(data.documents || []);
        } catch (error) {
            console.error("Load documents error:", error);
            setError("Could not load documents.");
        }
    }


	async function uploadDocument() {
		if (selectedFiles.length === 0) {
			if (justUploaded) {
				setError("Upload complete. Please select a new file.");
			} else {
				setError("Please choose at least one PDF first.");
			}

			return;
		}

		setError("");
		setIsUploading(true);

		try {
			const formData = new FormData();

			selectedFiles.forEach((file) => {
				formData.append("files", file);
			});

			const response = await fetch(`${API_URL}/upload`, {
				method: "POST",
				body: formData,
			});

			const data = await response.json();

			if (!response.ok) {
				setError(data.detail || "Upload failed.");
				return;
			}

			if (data.skipped?.length > 0) {
				setError(
					data.skipped
						.map((item) => `${item.filename}: ${item.reason}`)
						.join("\n")
				);
			}

			setSelectedFiles([]);
			setJustUploaded(true);
			await loadDocuments();

		} catch (error) {
			console.error("Upload error:", error);
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
        setAnswer("");
        setSources([]);
        setIsAsking(true);

        const response = await fetch(`${API_URL}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ question }),
        });

        const data = await response.json();

        setAnswer(data.answer);
        setSources(data.sources || []);
        setIsAsking(false);

    }

    async function deleteDocument(filename) {
      
        setError("");

        const response = await fetch(
            `${API_URL}/documents/${filename}`,
            {
                method: "DELETE",
            }
        );

        if (!response.ok) {
            setError("Failed to delete document.");
            return;
        }

        await loadDocuments();
    }

    return (
        <main className="container py-5">
            <section className="mb-5">
                <span className="badge text-bg-primary mb-3">
                    AI document search
                </span>

                <h1 className="display-5 fw-bold">
                    RAG Document Assistant
                </h1>

                <p className="lead text-secondary">
                    Upload PDFs, search across your knowledge base, and receive cited answers.
                </p>
            </section>


            <ErrorAlert error={error} />
            {/* {error && (
                <div className="alert alert-danger" role="alert">
                    {error}
                </div>
            )} */}

            <section className="row g-4 mb-4">
                <div className="col-md-6">
					<UploadCard
						setSelectedFiles={setSelectedFiles}
						setJustUploaded={setJustUploaded}
						uploadDocument={uploadDocument}
						isUploading={isUploading}
					/>
                </div>
  
                <div className="col-md-6">
                    <DocumentsCard
                        documents={documents}
                        deleteDocument={deleteDocument}
                    />
                </div>
            </section>

            <AskCard
                question={question}
                setQuestion={setQuestion}
                askQuestion={askQuestion}
                isAsking={isAsking}
            />
            {/* <section className="card shadow-sm mb-4">
                <div className="card-body">
                    <h2 className="h4 card-title">Ask a question</h2>

                    <textarea
                        className="form-control mb-3"
                        rows="5"
                        value={question}
                        onChange={(event) => setQuestion(event.target.value)}
                        placeholder="Example: What accuracy did the classifier achieve?"
                    />

                    <button
                        className="btn btn-success"
                        onClick={askQuestion}
                        disabled={isAsking}
                    >
                        {isAsking ? "Thinking..." : "Ask"}
                    </button>
                </div>
            </section> */}


            <AnswerCard
                answer={answer}
                sources={sources}
            />
        </main>
    );
}

export default App;