import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import config
import storage
from models import QuestionRequest
from rag import generate_answer
from uploads import UploadRejected, clean_display_name, read_limited
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
    first_status = None

    for file in files:
        try:
            name = clean_display_name(file.filename)
            data = read_limited(file.file)
            document = storage.add_document(visitor, name, data)
        except UploadRejected as rejection:
            first_status = first_status or rejection.status
            skipped.append({"filename": file.filename or "", "reason": rejection.message})
            continue

        uploaded.append(document["name"])

    if not uploaded and first_status:
        raise HTTPException(status_code=first_status, detail=skipped[0]["reason"])

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
