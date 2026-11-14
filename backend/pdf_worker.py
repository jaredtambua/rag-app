"""Reads one PDF in a separate process so a hostile file cannot freeze or exhaust the server.

Usage: python pdf_worker.py <path> <max pages> <max characters> <max content bytes> <max address space>
Prints one line of JSON: {"pages": [...]} on success, or {"error": "<code>"}.
The parent also watches this process's memory and time and kills it if needed.
Nothing here imports the app.
"""

import json
import sys
import zlib

import fitz


def limit_memory(max_bytes):
    """Hard memory ceiling for this process (Linux only; does nothing on Windows)."""
    try:
        import resource
    except ImportError:
        return

    try:
        resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
    except (ValueError, OSError):
        pass


def stream_size_capped(doc, xref, cap):
    """Decompressed size of a stream, counted without ever holding more than a
    megabyte of it. Stops counting once the size passes cap."""
    raw = doc.xref_stream_raw(xref)
    kind, value = doc.xref_get_key(xref, "Filter")
    value = value.replace(" ", "")

    if kind == "null":
        return len(raw)

    if value in ("/FlateDecode", "[/FlateDecode]", "/Fl", "[/Fl]"):
        inflater = zlib.decompressobj()
        total = 0
        data = raw

        try:
            while data and total <= cap and not inflater.eof:
                chunk = inflater.decompress(data, 1 << 20)
                total += len(chunk)
                data = inflater.unconsumed_tail

                if not chunk:
                    break
        except zlib.error:
            return len(raw)

        return total

    # Other filters cannot be sized cheaply; the parent's memory and time limits cover them.
    return len(raw)


def main(path, max_pages, max_chars, max_content_bytes):
    try:
        doc = fitz.open(path)
    except Exception:
        return {"error": "invalid"}

    with doc:
        if doc.needs_pass:
            return {"error": "invalid"}

        if doc.page_count > max_pages:
            return {"error": "pages"}

        total_content = 0

        try:
            # Form objects (reusable page fragments) hold drawing instructions
            # too, so they count toward the same cap as the pages themselves.
            for xref in range(1, doc.xref_length()):
                if doc.xref_is_stream(xref) and doc.xref_get_key(xref, "Subtype")[1] == "/Form":
                    total_content += stream_size_capped(doc, xref, max_content_bytes)

                    if total_content > max_content_bytes:
                        return {"error": "content"}

            for number in range(doc.page_count):
                for xref in doc[number].get_contents():
                    total_content += stream_size_capped(doc, xref, max_content_bytes)

                    if total_content > max_content_bytes:
                        return {"error": "content"}
        except Exception:
            return {"error": "invalid"}

        pages = []
        total_chars = 0

        for number in range(doc.page_count):
            try:
                text = doc[number].get_text()
            except Exception:
                return {"error": "invalid"}

            total_chars += len(text)

            if total_chars > max_chars:
                return {"error": "text"}

            if text.strip():
                pages.append({"page": number + 1, "text": text})

    return {"pages": pages}


if __name__ == "__main__":
    limit_memory(int(sys.argv[5]))
    result = main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    sys.stdout.write(json.dumps(result))
