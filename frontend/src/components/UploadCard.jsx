function UploadCard({
    setSelectedFiles,
    setJustUploaded,
    uploadDocument,
    isUploading,
}) {
    return (
        <div className="card shadow-sm h-100">
            <div className="card-body">
                <h2 className="h4 card-title">Upload document</h2>

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
                    className="btn btn-primary"
                    onClick={uploadDocument}
                    disabled={isUploading}
                >
                    {isUploading ? "Uploading..." : "Upload PDF"}
                </button>
            </div>
        </div>
    );
}

export default UploadCard;