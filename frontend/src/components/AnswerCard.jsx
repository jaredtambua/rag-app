import ReactMarkdown from "react-markdown";

function AnswerCard({ answer, citations }) {
    if (!answer) {
        return null;
    }

    return (
        <section className="card shadow-sm border-0 rounded-4 mb-4 answer-card">
            <div className="card-body">
                <h2 className="h4 card-title">
                    <i className="bi bi-stars text-info me-2"></i>
                    Answer
                </h2>

                <div className="text-start answer-markdown">
                    <ReactMarkdown>
                        {answer}
                    </ReactMarkdown>
                </div>

                {citations.length > 0 && (
                    <>
                        <h3 className="h5 mt-4">
                            <i className="bi bi-link-45deg me-2"></i>
                            Sources
                        </h3>

                        <div className="d-flex flex-column gap-3">
                            {citations.map((citation, index) => (
                                <div
                                    key={index}
                                    className="border rounded-3 p-3 bg-light"
                                >
                                    <div className="fw-semibold mb-2">
                                        <i className="bi bi-file-earmark-text text-primary me-2"></i>
                                        {citation.source} · Page {citation.page}
                                    </div>

                                    <blockquote className="mb-0 fst-italic">
                                        "{citation.quote}"
                                    </blockquote>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </section>
    );
}

export default AnswerCard;