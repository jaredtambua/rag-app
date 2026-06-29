import hashlib

import fitz

from config import CHUNK_SIZE, CHUNK_OVERLAP


# extract text from a pdf
def extract_pdf_text(pdf_path):
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages = []

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text()

        if text.strip():
            pages.append({"page": page_number, "text": text})

    return pages


# recursively split text into semantic chunks
def split_text_recursive(text, chunk_size=CHUNK_SIZE):
    separators = ["\n\n", "\n", ". ", " ", ""]

    return recursive_split(text, separators, chunk_size)


# recursively split using progressively smaller separators
def recursive_split(text, separators, chunk_size):
    text = text.strip()

    if len(text) <= chunk_size:
        return [text] if text else []

    separator = separators[0]
    remaining = separators[1:]

    if separator == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    parts = text.split(separator)

    chunks = []
    current_chunk = ""

    for part in parts:
        part = part.strip()

        if not part:
            continue

        candidate = current_chunk + separator + part if current_chunk else part

        if len(candidate) <= chunk_size:
            current_chunk = candidate

        else:
            if current_chunk:
                chunks.append(current_chunk)

            if len(part) > chunk_size:
                chunks.extend(recursive_split(part, remaining, chunk_size))
                current_chunk = ""

            else:
                current_chunk = part

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# add overlap between neighbouring chunks
def add_overlap(chunks, overlap):
    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]

    for i in range(1, len(chunks)):
        previous_tail = chunks[i - 1][-overlap:]
        overlapped.append(previous_tail + "\n\n" + chunks[i])

    return overlapped


# split text into final chunks
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = split_text_recursive(text, chunk_size)

    return add_overlap(chunks, overlap)


# build chunk records from a pdf
def build_chunk_records(pdf_path):
    source_name = pdf_path.name
    pages = extract_pdf_text(pdf_path)

    chunk_records = []

    for page in pages:
        chunks = chunk_text(page["text"])

        for chunk_number, chunk in enumerate(chunks, start=1):
            chunk_records.append(
                {
                    "id": f"{source_name}-page-{page['page']}-chunk-{chunk_number}",
                    "source": source_name,
                    "page": page["page"],
                    "chunk_number": chunk_number,
                    "text": chunk,
                }
            )

    return chunk_records


# calculate a file hash
def calculate_file_hash(file_path):
    file_bytes = file_path.read_bytes()

    return hashlib.sha256(file_bytes).hexdigest()
