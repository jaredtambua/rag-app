from pathlib import Path

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

DOCUMENTS_DIR = Path("documents")
VECTORSTORE_PATH = "vectorstore"


# ---------------------------------------------------------
# Chroma
# ---------------------------------------------------------

COLLECTION_NAME = "documents"


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
