"""Creates a small synthetic test zip for validation."""
import zipfile
import pathlib

def tiny_pdf(label: str) -> bytes:
    """Build a proper minimal PDF with correct xref byte offsets."""
    objects = []
    objects.append(b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n")
    objects.append(b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n")
    objects.append(
        b"3 0 obj\n<</Type /Page /Parent 2 0 R /MediaBox [0 0 200 200]"
        b" /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>>\nendobj\n"
    )
    stream_data = b"BT /F1 12 Tf 50 150 Td (" + label.encode() + b") Tj ET"
    objects.append(
        b"4 0 obj\n<</Length " + str(len(stream_data)).encode() + b">>\nstream\n"
        + stream_data + b"\nendstream\nendobj\n"
    )
    objects.append(
        b"5 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>\nendobj\n"
    )

    header = b"%PDF-1.4\n"
    body = b""
    offsets = []
    for obj in objects:
        offsets.append(len(header) + len(body))
        body += obj

    xref_pos = len(header) + len(body)
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = (
        b"trailer\n<</Size 6 /Root 1 0 R>>\nstartxref\n"
        + str(xref_pos).encode() + b"\n%%EOF\n"
    )
    return header + body + xref + trailer

out = pathlib.Path(__file__).parent.parent / "test_input.zip"
with zipfile.ZipFile(out, "w") as z:
    for topic in ["embryo", "anatomy"]:
        for i in ["1", "2", "3.1", "3.2"]:
            z.writestr(f"cardiology/{topic}/{i}.pdf", tiny_pdf(f"{topic}-{i}"))

print("Created test zip:", out)
