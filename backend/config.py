import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent

# Read backend/.env if present (values already in the environment win).
load_dotenv(BACKEND_DIR / ".env")


# ---------------------------------------------------------
# Paths (always anchored on this file, never the working directory)
# ---------------------------------------------------------

DEFAULT_DATA_DIR = BACKEND_DIR / "data"


def data_dir() -> Path:
    """Root folder for temporary visitor data. Override with DATA_DIR."""
    override = os.environ.get("DATA_DIR")
    return Path(override).resolve() if override else DEFAULT_DATA_DIR


def documents_root() -> Path:
    return data_dir() / "documents"


def vectorstore_path() -> Path:
    return data_dir() / "vectorstore"


def data_dir_is_safe_to_wipe(path: Path) -> bool:
    """Only a dedicated folder may be wiped at startup."""
    path = Path(path).resolve()
    if path.name == "data":
        return True
    temp_root = Path(tempfile.gettempdir()).resolve()
    return temp_root in path.parents


# ---------------------------------------------------------
# Demo limits (one place to change them)
# ---------------------------------------------------------

# Uploads (file and search index) are removed this long after upload.
DEFAULT_UPLOAD_TTL_SECONDS = 1800


def upload_ttl() -> float:
    """Lifetime of an upload in seconds. Override with UPLOAD_TTL_SECONDS."""
    raw = os.environ.get("UPLOAD_TTL_SECONDS")
    try:
        value = float(raw) if raw else DEFAULT_UPLOAD_TTL_SECONDS
    except ValueError:
        return DEFAULT_UPLOAD_TTL_SECONDS
    return value if value > 0 else DEFAULT_UPLOAD_TTL_SECONDS


# How often the cleanup sweeper runs.
SWEEP_INTERVAL_SECONDS = 60

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_PAGES = 30
MAX_FILES_PER_VISITOR = 3
MAX_QUESTION_CHARACTERS = 500
MAX_DISPLAY_NAME_CHARACTERS = 100

# Conversation memory: earlier question-and-answer pairs sent with a question.
MAX_HISTORY_TURNS = 5
MAX_HISTORY_QUESTION_CHARS = MAX_QUESTION_CHARACTERS
MAX_HISTORY_ANSWER_CHARS = 1000
# Each earlier answer is cut to this many characters when it goes into a prompt.
HISTORY_ANSWER_PROMPT_CHARS = 600

# Rate limits, all per rolling hour. The totals are the cost ceiling,
# because visitor IDs are made by the browser and can be rotated.
RATE_WINDOW_SECONDS = 3600
ASK_LIMIT_PER_VISITOR = 20
ASK_LIMIT_PER_IP = 60
ASK_LIMIT_TOTAL = 300
UPLOAD_LIMIT_PER_VISITOR = 10
UPLOAD_LIMIT_PER_IP = 20
UPLOAD_LIMIT_TOTAL = 40

# Upload attempts (accepted OR rejected) before any parsing, per address and in total.
# Separate from the accepted-upload quotas above, so rejected files cannot be sent for free.
UPLOAD_ATTEMPT_LIMIT_PER_IP = 30
UPLOAD_ATTEMPT_LIMIT_TOTAL = 120

# Reading an uploaded PDF (done in a separate process).
PARSE_TIMEOUT_SECONDS = 5
# The reader and its child processes are killed above this much memory (checked every 20 ms).
MAX_PARSE_MEMORY_BYTES = 350 * 1024 * 1024
MAX_CONCURRENT_PARSES = 2
# Total text taken from one document, and the chunks made from it.
MAX_EXTRACTED_CHARACTERS = 200_000
MAX_CHUNKS = 500
# Total decompressed page-drawing data. A tiny file can expand to hundreds of MB.
MAX_CONTENT_BYTES = 8 * 1024 * 1024

# Texts are embedded in groups of this size.
EMBEDDING_BATCH_SIZE = 64


DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://rag-app-1-8mtr.onrender.com",
]

# Largest request body accepted: three 5 MB files plus form overhead for
# uploads, and a small cap for everything else (questions are tiny).
MAX_UPLOAD_REQUEST_BYTES = 20 * 1024 * 1024
MAX_OTHER_REQUEST_BYTES = 64 * 1024


def allowed_origins() -> list[str]:
    """Browser origins allowed to call the API. Override with ALLOWED_ORIGINS."""
    raw = os.environ.get("ALLOWED_ORIGINS")
    if raw is None:
        return list(DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def docs_enabled() -> bool:
    """The interactive API docs are off unless ENABLE_API_DOCS=1."""
    return os.environ.get("ENABLE_API_DOCS") == "1"


def check_environment() -> None:
    """Refuse to run the OpenAI fakes in the hosted environment."""
    fake_openai()


def fake_openai() -> bool:
    """Test and QA switch: replace OpenAI calls with deterministic fakes.

    Refuses to answer True on Render (any non-empty RENDER value), so the fakes
    can never run in the hosted app even if the startup check was skipped.
    """
    enabled = os.environ.get("FAKE_OPENAI") == "1"
    if enabled and os.environ.get("RENDER"):
        raise RuntimeError("FAKE_OPENAI must never be set on Render.")
    return enabled


# ---------------------------------------------------------
# Chroma
# ---------------------------------------------------------

COLLECTION_NAME = "visitor_documents"


# ---------------------------------------------------------
# Models
# ---------------------------------------------------------

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"


# ---------------------------------------------------------
# Chunking
# ---------------------------------------------------------

# Maximum number of characters in each chunk.
CHUNK_SIZE = 800

# Number of characters shared between consecutive chunks.
# This helps avoid losing context at chunk boundaries.
CHUNK_OVERLAP = 150


# ---------------------------------------------------------
# Retrieval
# ---------------------------------------------------------

# Number of candidate chunks to initially retrieve from Chroma.
#
# Previously we retrieved only TOP_K = 3. We now deliberately
# retrieve a larger candidate set because later stages of the
# retrieval pipeline will filter and process these results.
RETRIEVAL_CANDIDATES = 20


# Maximum Chroma distance normally considered relevant.
#
# Lower distance = greater similarity.
#
# NOTE:
# This is an initial heuristic rather than a universally correct
# value. We should inspect real retrieval results and tune it later.
MAX_DISTANCE = 1.0


# If fewer than this many chunks pass MAX_DISTANCE,
# retain at least this many of the best candidates.
MIN_RESULTS = 3


# Never keep more than this many of the best chunks before neighbours are
# added. On a small document nearly every chunk is "close", and without a cap
# the whole document would be sent (and then dropped for being too big).
MAX_SELECTED = 6


# Number of chunks immediately before and after a selected
# chunk that we retrieve to restore surrounding context.
#
# Example with window=1:
#
#       chunk 36
#       chunk 37  <-- retrieved match
#       chunk 38
#
NEIGHBOR_WINDOW = 1


# Approximate maximum number of characters of retrieved
# evidence that we will provide to the generation layer.
#
# Context blocks are considered in relevance order until
# this budget is reached.
MAX_CONTEXT_CHARACTERS = 12_000
