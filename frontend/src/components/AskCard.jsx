function AskCard({
    question,
    setQuestion,
    askQuestion,
    isAsking,
}) {
    return (
        <section className="card shadow-sm mb-4">
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
        </section>
    );
}

export default AskCard;