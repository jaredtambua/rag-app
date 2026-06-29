import ReactMarkdown from "react-markdown";


function AnswerCard({ answer, sources }) {
    if (!answer) {
        return null;
    }

    return (
        <section className="card shadow-sm">
            <div className="card-body">
                <h2 className="h4 card-title">Answer</h2>


                <div className="text-start">
                    <ReactMarkdown>
                        {answer}
                    </ReactMarkdown>
                </div>
                {/* <p>{answer}</p> */}

                {sources.length > 0 && (
                    <>
                        <h3 className="h5 mt-4">Sources</h3>

                        <ul className="list-group">
                            {sources.map((source, index) => (
                                <li className="list-group-item" key={index}>
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