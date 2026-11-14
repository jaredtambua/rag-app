"""Small hostile PDFs for regression tests: tiny on disk, huge once decompressed."""

import zlib

TEXT_UNIT = b"BT /F1 12 Tf 10 10 Td (word word word word word word word word) Tj ET\n"
DRAWING_UNIT = b"0 0 m 500 700 l 20 30 l S\n"


def make_stream_bomb(decompressed_mb: int, unit: bytes = TEXT_UNIT, pages: int = 1) -> bytes:
    """A PDF whose single content stream is a flate bomb of repeated operators."""
    reps = (decompressed_mb * 1024 * 1024) // len(unit)
    comp = zlib.compressobj(9)
    block = unit * 1000
    chunks = [comp.compress(block) for _ in range(reps // 1000)]
    chunks.append(comp.flush())
    data = b"".join(chunks)

    kids = b" ".join(b"%d 0 R" % (5 + i) for i in range(pages))
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [" + kids + b"] /Count %d >>" % pages,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(data) + data + b"\nendstream",
    ]
    for _ in range(pages):
        objs.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] "
            b"/Resources << /Font << /F1 3 0 R >> >> /Contents 4 0 R >>"
        )

    parts = [b"%PDF-1.4\n"]
    pos = len(parts[0])
    offsets = []
    for number, body in enumerate(objs, 1):
        offsets.append(pos)
        chunk = b"%d 0 obj\n" % number + body + b"\nendobj\n"
        parts.append(chunk)
        pos += len(chunk)
    parts.append(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
    parts.extend(b"%010d 00000 n \n" % offset for offset in offsets)
    parts.append(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, pos)
    )
    return b"".join(parts)
