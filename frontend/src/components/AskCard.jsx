function AskCard({
    question,
    setQuestion,
    askQuestion,
    isAsking,
}) {
    return (
        <section className="card shadow-sm border-0 rounded-4 mb-4">
            <div className="card-body">
                <h2 className="h4 card-title">
                    <i className="text-success me-2"></i>
                    Ask a question
                </h2>

                <textarea
                    className="form-control mb-3"
                    rows="5"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Example: What accuracy did the classifier achieve?"
                />

                <button
                    className="btn btn-success rounded-pill px-4"
                    onClick={askQuestion}
                    disabled={isAsking}
                >
                    <i className="bi bi-send-fill me-2"></i>
                    {isAsking ? "Thinking..." : "Ask"}
                </button>
            </div>
        </section>
    );
}

export default AskCard;