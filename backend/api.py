from fastapi import FastAPI, UploadFile, HTTPException, File
from typing import List

from rag import generate_answer
from vector_store import (
    index_document,
    remove_deleted_documents_from_chroma,
)

from retrieval import retrieve_context
from rag import generate_answer

from models import QuestionRequest

from pathlib import Path

from config import DOCUMENTS_DIR

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://rag-app-1-8mtr.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask")
def ask(request: QuestionRequest):
    context = retrieve_context(request.question)

    response = generate_answer(
        request.question,
        context,
    )

    return response


@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    uploaded = []
    skipped = []

    for file in files:
        if not file.filename.endswith(".pdf"):
            skipped.append(
                {"filename": file.filename, "reason": "Only PDF files are supported."}
            )
            continue

        file_path = DOCUMENTS_DIR / file.filename

        if file_path.exists():
            skipped.append(
                {
                    "filename": file.filename,
                    "reason": "This document has already been uploaded.",
                }
            )
            continue

        contents = await file.read()

        with open(file_path, "wb") as f:
            f.write(contents)

        index_document(file_path)

        uploaded.append(file.filename)

    return {"uploaded": uploaded, "skipped": skipped}


@app.get("/documents")
def list_documents():
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    pdf_files = sorted(file.name for file in DOCUMENTS_DIR.glob("*.pdf"))

    return {"documents": pdf_files}


@app.delete("/documents/{filename}")
def delete_document(filename: str):
    file_path = DOCUMENTS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path.unlink()

    remove_deleted_documents_from_chroma()

    return {"message": "Document deleted successfully.", "filename": filename}
