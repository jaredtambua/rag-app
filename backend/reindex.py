from config import DOCUMENTS_DIR
from vector_store import index_document


def reindex_all_documents():
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDFs found in {DOCUMENTS_DIR}/")
        return

    print(f"Found {len(pdf_files)} PDF(s). Reindexing...\n")

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        try:
            index_document(pdf_path)
            print(f"✓ Finished {pdf_path.name}\n")

        except Exception as error:
            print(f"✗ Failed: {pdf_path.name}")
            print(f"  {type(error).__name__}: {error}\n")

    print("Reindex complete.")


if __name__ == "__main__":
    reindex_all_documents()
