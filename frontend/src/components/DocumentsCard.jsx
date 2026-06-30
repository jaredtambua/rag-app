function DocumentsCard({ documents, deleteDocument }) {
    return (
        <div className="card shadow-sm border-0 rounded-4 h-100">
            <div className="card-body">
                <div className="d-flex justify-content-between align-items-center mb-3">
                    <h2 className="h4 card-title mb-0">
                        <i className="bi bi-folder2-open text-warning me-2"></i>
                        Documents
                    </h2>

                    <span className="badge bg-primary rounded-pill">
                        {documents.length}
                    </span>
                </div>

                {documents.length === 0 ? (
                    <p className="text-secondary mb-0">
                        <i className="bi bi-inbox me-2"></i>
                        No documents uploaded yet.
                    </p>
                ) : (
                    <ul className="list-group list-group-flush">
                        {documents.map((document) => (
                            <li
                                key={document}
                                className="list-group-item d-flex align-items-center gap-3 px-0"
                            >
                                <div className="d-flex align-items-start flex-grow-1 min-w-0">
                                    <i className="bi bi-file-earmark-pdf-fill text-danger me-2 mt-1"></i>

                                    <span className="text-start text-break">
                                        {document}
                                    </span>
                                </div>

                                <button
                                    className="btn btn-sm btn-outline-danger rounded-pill flex-shrink-0"
                                    onClick={() => deleteDocument(document)}
                                >
                                    <i className="bi bi-trash me-1"></i>
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