import ReactMarkdown from "react-markdown";

function AnswerCard({ answer, sources }) {
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

                {sources.length > 0 && (
                    <>
                        <h3 className="h5 mt-4">
                            <i className="bi bi-link-45deg me-2"></i>
                            Sources
                        </h3>

                        <ul className="list-group list-group-flush">
                            {sources.map((source, index) => (
                                <li className="list-group-item px-0" key={index}>
                                    <i className="bi bi-file-earmark-text text-primary me-2"></i>
                                    {source.source}, page {source.page}, chunk {source.chunk}
                                </li>
                            ))}
                        </ul>
                    </>
                )}
            </div>
        </section>
    );
}

export default AnswerCard;