import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi.middleware.cors import CORSMiddleware

import config
import rate_limit
import storage
from models import QuestionRequest
from rag import AnswerError, generate_answer
from uploads import UploadRejected, clean_display_name, read_limited
from retrieval import retrieve_context
from visitor import visitor_id

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.check_environment()

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


class BodyTooLarge(Exception):
    pass


class BodyLimitMiddleware:
    """Refuse oversized request bodies while they stream in.

    Checks the declared Content-Length first, then counts the bytes actually
    received, so a body sent without a length cannot get past the limit.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if scope["path"] == "/upload":
            limit = config.MAX_UPLOAD_REQUEST_BYTES
            message = "This file is larger than 5 MB."
        else:
            limit = config.MAX_OTHER_REQUEST_BYTES
            message = "The request is too large."

        declared = dict(scope["headers"]).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > limit:
            await self._refuse(scope, receive, send, message)
            return

        received = 0
        exceeded = False
        responded = False

        async def refuse_once():
            nonlocal responded
            if not responded:
                responded = True
                await self._refuse(scope, receive, send, message)

        async def limited_receive():
            nonlocal received, exceeded
            event = await receive()
            if event["type"] == "http.request":
                received += len(event.get("body", b""))
                if received > limit:
                    exceeded = True
                    raise BodyTooLarge()
            return event

        async def guarded_send(event):
            nonlocal responded
            if exceeded:
                # The framework may turn the failed read into its own error
                # response; replace it with a clear 413.
                await refuse_once()
                return
            if event["type"] == "http.response.start":
                responded = True
            await send(event)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except BodyTooLarge:
            await refuse_once()

    @staticmethod
    async def _refuse(scope, receive, send, message):
        response = JSONResponse(status_code=413, content={"detail": message})
        await response(scope, receive, send)


app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if config.docs_enabled() else None,
    redoc_url="/redoc" if config.docs_enabled() else None,
    openapi_url="/openapi.json" if config.docs_enabled() else None,
)

app.add_middleware(BodyLimitMiddleware)

# Added last so it is outermost: even refusals carry the CORS headers.
# No cookies are used, so credentials are not allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins(),
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Visitor-Id"],
    # Lets the page read how long to wait after a 429.
    expose_headers=["Retry-After"],
)


@app.exception_handler(AnswerError)
def answer_error_handler(request: Request, error: AnswerError):
    return JSONResponse(status_code=502, content={"detail": error.message})


@app.exception_handler(RecursionError)
def too_deep_handler(request: Request, error: RecursionError):
    return JSONResponse(status_code=400, content={"detail": "The request could not be read."})


@app.exception_handler(rate_limit.RateLimited)
def rate_limited_handler(request: Request, error: rate_limit.RateLimited):
    return JSONResponse(
        status_code=429,
        content={"detail": error.message},
        headers={"Retry-After": str(error.retry_after)},
    )


@app.get("/health")
async def health_check():
    # async and lock-free: it answers even while uploads are being read
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

    # Every attempt counts, even ones that will be rejected: reading a file costs CPU.
    rate_limit.check_upload_attempt(ip)

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
    refunded = False

    for file in files:
        try:
            name = clean_display_name(file.filename)
            data = read_limited(file.file)
            document = storage.add_document(visitor, name, data, use_quota, owner=ip)
        except UploadRejected as rejection:
            if rejection.status == 503 and not refunded:
                # 'Busy' refusals are not the visitor's fault: they do not use up attempts.
                refunded = True
                rate_limit.refund_upload_attempt(ip)

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
