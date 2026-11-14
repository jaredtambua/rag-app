"""More hostile PDFs: huge form objects and nested forms (tiny on disk)."""

import zlib

from bombs import TEXT_UNIT


def _build(objs):
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


def _flate(unit: bytes, total: int) -> bytes:
    comp = zlib.compressobj(9)
    block = unit * 1000
    out = [comp.compress(block) for _ in range(total // len(block))]
    out.append(comp.flush())
    return b"".join(out)


def make_form_bomb(decompressed_mb: int, unit: bytes = TEXT_UNIT) -> bytes:
    """A tiny page that calls one form object (XObject) holding a huge stream."""
    data = _flate(unit, decompressed_mb * 1024 * 1024)
    page = b"q /X Do Q"
    return _build([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 5 0 R >> /XObject << /X 6 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(page) + page + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /XObject /Subtype /Form /BBox [0 0 600 800] /Resources << /Font << /F1 5 0 R >> >> /Length %d /Filter /FlateDecode >>\nstream\n" % len(data) + data + b"\nendstream",
    ])


def make_nested_forms(depth: int = 12, fan: int = 10) -> bytes:
    """Form i calls form i+1 `fan` times: fan**depth operations from a tiny file."""
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 5 0 R >> /XObject << /X 6 0 R >> >> /Contents 4 0 R >>",
    ]
    page = b"/X Do"
    objs.append(b"<< /Length %d >>\nstream\n" % len(page) + page + b"\nendstream")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for i in range(depth):
        number = 6 + i
        if i == depth - 1:
            body = b"BT /F1 12 Tf 10 10 Td (leaf text here) Tj ET"
        else:
            body = b" ".join([b"/X Do"] * fan)
        nxt = b"<< /X %d 0 R >>" % (number + 1)
        objs.append(
            b"<< /Type /XObject /Subtype /Form /BBox [0 0 600 800] /Resources << /Font << /F1 5 0 R >> /XObject "
            + nxt + b" >> /Length %d >>\nstream\n" % len(body) + body + b"\nendstream"
        )
    return _build(objs)
