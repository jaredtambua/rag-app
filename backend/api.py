import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import config
import rate_limit
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
    rate_limit.limiter.reset()

    sweeper = storage.Sweeper(
        config.SWEEP_INTERVAL_SECONDS, [storage.sweep, rate_limit.limiter.prune]
    )
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


@app.exception_handler(rate_limit.RateLimited)
def rate_limited_handler(request: Request, error: rate_limit.RateLimited):
    return JSONResponse(
        status_code=429,
        content={"detail": error.message},
        headers={"Retry-After": str(error.retry_after)},
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask")
def ask(
    body: QuestionRequest, request: Request, visitor: str = Depends(visitor_id)
):
    question = body.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Please enter a question.")

    if len(question) > config.MAX_QUESTION_CHARACTERS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Questions can be up to {config.MAX_QUESTION_CHARACTERS} characters."
            ),
        )

    # Only questions that passed validation use up quota.
    rate_limit.check_ask(visitor, rate_limit.client_ip(request))

    context = retrieve_context(visitor, question)

    return generate_answer(question, context)


@app.post("/upload")
def upload_documents(
    request: Request,
    files: List[UploadFile] = File(...),
    visitor: str = Depends(visitor_id),
):
    ip = rate_limit.client_ip(request)
    quota_used = False

    def use_quota():
        # One upload unit per request, taken when the first file passes
        # validation (before any paid indexing). Rejected files cost nothing.
        nonlocal quota_used

        if not quota_used:
            rate_limit.check_upload(visitor, ip)
            quota_used = True

    uploaded = []
    skipped = []
    first_status = None

    for file in files:
        try:
            name = clean_display_name(file.filename)
            data = read_limited(file.file)
            document = storage.add_document(visitor, name, data, use_quota)
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
