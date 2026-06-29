from config import DOCUMENTS_DIR

from display import print_results
from rag import generate_answer
from vector_store import (
    index_document,
    remove_deleted_documents_from_chroma,
    retrieve_chunks,
)


# run the application
def main():
    remove_deleted_documents_from_chroma()

    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {DOCUMENTS_DIR}.")
        return

    print(f"Found {len(pdf_files)} PDF file(s).")

    for pdf_path in pdf_files:
        index_document(pdf_path)

    print("\nReady to search!")

    while True:
        question = input("\nAsk a question, or type 'exit': ").strip()

        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not question:
            print("Please enter a question.")
            continue

        results = retrieve_chunks(question)

        print_results(results)

        answer = generate_answer(question, results)

        print("\nAnswer:")
        print(answer)


if __name__ == "__main__":
    main()
