function UploadCard({
    setSelectedFiles,
    setJustUploaded,
    uploadDocument,
    isUploading,
}) {
    return (
        <div className="card shadow-sm border-0 rounded-4 h-100">
            <div className="card-body">
                <h2 className="h4 card-title mb-3">
                    <i className="bi bi-cloud-arrow-up-fill text-primary me-2"></i>
                    Upload document
                </h2>

                <p className="text-secondary">
                    Add a PDF to your searchable knowledge base.
                </p>

                <input
                    className="form-control mb-3"
                    type="file"
                    accept="application/pdf"
                    multiple
                    onChange={(event) => {
                        setSelectedFiles(Array.from(event.target.files));
                        setJustUploaded(false);
                    }}
                />

                <button
                    className="btn btn-primary rounded-pill px-4"
                    onClick={uploadDocument}
                    disabled={isUploading}
                >
                    <i className="bi bi-upload me-2"></i>
                    {isUploading ? "Uploading..." : "Upload PDF"}
                </button>
            </div>
        </div>
    );
}

export default UploadCard;

