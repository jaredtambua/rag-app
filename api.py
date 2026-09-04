from fastapi import FastAPI, UploadFile, HTTPException, File
from typing import List

from rag import generate_answer
from vector_store import (
    retrieve_chunks,
    index_document,
    remove_deleted_documents_from_chroma,
    expand_with_neighbor_chunks,
)
from models import QuestionRequest

from pathlib import Path

from config import DOCUMENTS_DIR

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def select_relevant_chunks(
    results,
    max_chunks=8,
    max_distance=0.8,
    fallback_chunks=3,
):
    selected = []

    for distance, record in results:
        if distance <= max_distance:
            selected.append((distance, record))

        if len(selected) >= max_chunks:
            break

    if selected:
        return selected

    return results[:fallback_chunks]


# Add this helper function in api.py, near select_relevant_chunks


def limit_context_size(results, max_characters=12000):
    limited = []
    total_characters = 0

    for distance, record in results:
        text_length = len(record["text"])

        if total_characters + text_length > max_characters:
            break

        limited.append((distance, record))
        total_characters += text_length

    return limited


def deduplicate_citations(citations):
    seen = set()
    unique = []

    for citation in citations:
        key = (
            citation["source"],
            citation["page"],
            citation["quote"],
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(citation)

    return unique


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask")
def ask_question(request: QuestionRequest):
    candidates = retrieve_chunks(request.question, limit=20)

    selected_results = select_relevant_chunks(candidates)

    expanded_results = expand_with_neighbor_chunks(selected_results, window=1)

    limited_results = limit_context_size(expanded_results)

    response = generate_answer(request.question, limited_results)

    citations = deduplicate_citations(response.get("citations", []))

    return {
        "question": request.question,
        "answer": response.get("answer", ""),
        "sources": citations,
    }


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
