from clients import collection

from config import DOCUMENTS_DIR

from document_processing import (
    build_chunk_records,
    calculate_file_hash,
)

from embeddings import embed_text


# store chunks in chroma
def add_chunks_to_chroma(chunk_records, file_hash):
    for index, record in enumerate(chunk_records, start=1):
        print(f"Storing chunk {index}/{len(chunk_records)} in Chroma...")

        embedding = embed_text(record["text"])

        collection.add(
            ids=[record["id"]],
            embeddings=[embedding],
            documents=[record["text"]],
            metadatas=[
                {
                    "source": record["source"],
                    "page": record["page"],
                    "chunk_number": record["chunk_number"],
                    "chunk_index": record["chunk_index"],
                    "file_hash": file_hash,
                }
            ],
        )


# check whether a document needs reindexing
def document_needs_reindexing(source_name, file_hash):
    existing = collection.get(where={"source": source_name}, limit=1)

    if not existing["ids"]:
        return True

    existing_hash = existing["metadatas"][0].get("file_hash")

    return existing_hash != file_hash


# index one document
def index_document(pdf_path):
    source_name = pdf_path.name
    file_hash = calculate_file_hash(pdf_path)

    if not document_needs_reindexing(source_name, file_hash):
        print(f"{source_name} is already indexed and unchanged. Skipping.")
        return

    print(f"\nIndexing {source_name}...")

    collection.delete(where={"source": source_name})

    chunk_records = build_chunk_records(pdf_path)

    if not chunk_records:
        print(f"No text chunks found in {source_name}.")
        return

    add_chunks_to_chroma(chunk_records, file_hash)

    print(f"Finished indexing {source_name}.")


# remove deleted documents from chroma
def remove_deleted_documents_from_chroma():
    existing = collection.get()

    sources_in_chroma = {metadata["source"] for metadata in existing["metadatas"]}

    sources_in_folder = {pdf_path.name for pdf_path in DOCUMENTS_DIR.glob("*.pdf")}

    deleted_sources = sources_in_chroma - sources_in_folder

    for source in deleted_sources:
        print(f"Removing deleted document from Chroma: {source}")

        collection.delete(where={"source": source})


# retrieve relevant chunks
def retrieve_chunks(question, limit=20):
    question_embedding = embed_text(question)

    chroma_results = collection.query(
        query_embeddings=[question_embedding],
        n_results=limit,
    )

    retrieved = []

    for i in range(len(chroma_results["ids"][0])):
        record = {
            "id": chroma_results["ids"][0][i],
            "text": chroma_results["documents"][0][i],
            "source": chroma_results["metadatas"][0][i]["source"],
            "page": chroma_results["metadatas"][0][i]["page"],
            "chunk_number": chroma_results["metadatas"][0][i]["chunk_number"],
            "chunk_index": chroma_results["metadatas"][0][i]["chunk_index"],
        }

        distance = chroma_results["distances"][0][i]

        retrieved.append((distance, record))

    return retrieved


# retrieve one chunk by source + chunk number
def get_chunk_by_source_and_index(source, chunk_index):
    results = collection.get(
        where={
            "$and": [
                {"source": {"$eq": source}},
                {"chunk_index": {"$eq": chunk_index}},
            ]
        }
    )

    if not results["ids"]:
        return None

    return {
        "id": results["ids"][0],
        "text": results["documents"][0],
        "source": results["metadatas"][0]["source"],
        "page": results["metadatas"][0]["page"],
        "chunk_number": results["metadatas"][0]["chunk_number"],
        "chunk_index": results["metadatas"][0]["chunk_index"],
    }
