import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import config
import storage
from models import QuestionRequest
from rag import generate_answer
from retrieval import retrieve_context
from visitor import visitor_id

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uploads never survive a restart, matching the 30-minute promise.
    storage.reset_all()

    sweeper = storage.Sweeper(config.SWEEP_INTERVAL_SECONDS)
    sweeper.start()

    try:
        yield
    finally:
        sweeper.stop()


app = FastAPI(lifespan=lifespan)

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
def ask(request: QuestionRequest, visitor: str = Depends(visitor_id)):
    context = retrieve_context(visitor, request.question)

    return generate_answer(request.question, context)


@app.post("/upload")
def upload_documents(
    files: List[UploadFile] = File(...), visitor: str = Depends(visitor_id)
):
    uploaded = []
    skipped = []

    for file in files:
        name = file.filename or ""

        if not name.lower().endswith(".pdf"):
            skipped.append({"filename": name, "reason": "Only PDF files are supported."})
            continue

        document = storage.add_document(visitor, name, file.file.read())
        uploaded.append(document["name"])

    return {"uploaded": uploaded, "skipped": skipped}


@app.get("/documents")
def list_documents(visitor: str = Depends(visitor_id)):
    return {"documents": storage.list_documents(visitor)}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str, visitor: str = Depends(visitor_id)):
    try:
        document = storage.delete_document(visitor, doc_id)
    except storage.DocumentNotFound:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {"message": "Document deleted successfully.", "id": document["id"]}
