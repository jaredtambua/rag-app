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

# Rate limits, all per rolling hour. The totals are the cost ceiling,
# because visitor IDs are made by the browser and can be rotated.
RATE_WINDOW_SECONDS = 3600
ASK_LIMIT_PER_VISITOR = 20
ASK_LIMIT_PER_IP = 60
ASK_LIMIT_TOTAL = 300
UPLOAD_LIMIT_PER_VISITOR = 10
UPLOAD_LIMIT_PER_IP = 20
UPLOAD_LIMIT_TOTAL = 40

# Texts are embedded in groups of this size.
EMBEDDING_BATCH_SIZE = 64


def fake_openai() -> bool:
    """Test and QA switch: replace OpenAI calls with deterministic fakes."""
    return os.environ.get("FAKE_OPENAI") == "1"


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
