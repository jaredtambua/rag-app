function DocumentsCard({ documents, deleteDocument }) {
    return (
        <div className="card shadow-sm h-100">
            <div className="card-body">
                <h2 className="h4 card-title">Documents</h2>

                {documents.length === 0 ? (
                    <p className="text-secondary mb-0">
                        No documents uploaded yet.
                    </p>
                ) : (
                    <ul className="list-group list-group-flush">
                        {documents.map((document) => (
                            <li
                                key={document}
                                className="list-group-item d-flex justify-content-between align-items-center"
                            >
                                <span>{document}</span>

                                <button
                                    className="btn btn-sm btn-outline-danger"
                                    onClick={() => deleteDocument(document)}
                                >
                                    Delete
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

export default DocumentsCard;