from pathlib import Path

# Paths
DOCUMENTS_DIR = Path("documents")
VECTORSTORE_PATH = "vectorstore"


# Chroma
COLLECTION_NAME = "documents"


# Models
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"


# Chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


# Retrieval
TOP_K = 3
