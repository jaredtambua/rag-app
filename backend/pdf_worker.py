"""Reads one PDF in a separate process so a hostile file cannot freeze or exhaust the server.

Usage: python pdf_worker.py <path> <max pages> <max characters> <max content bytes>
Prints one line of JSON: {"pages": [...]} on success, or {"error": "<code>"}.
The parent kills this process if it runs too long. Nothing here imports the app.
"""

import json
import sys

import fitz


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

        pages = []
        total_chars = 0
        total_content = 0

        for number in range(doc.page_count):
            try:
                page = doc[number]
                # Page drawing instructions, decompressed. A tiny file can expand
                # to hundreds of megabytes, so the total is capped before any
                # text is extracted.
                total_content += len(page.read_contents())

                if total_content > max_content_bytes:
                    return {"error": "content"}

                text = page.get_text()
            except Exception:
                return {"error": "invalid"}

            total_chars += len(text)

            if total_chars > max_chars:
                return {"error": "text"}

            if text.strip():
                pages.append({"page": number + 1, "text": text})

    return {"pages": pages}


if __name__ == "__main__":
    result = main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    sys.stdout.write(json.dumps(result))
