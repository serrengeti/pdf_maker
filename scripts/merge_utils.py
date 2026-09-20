"""
Numeric filename sorting and PDF merge utilities.
"""
from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader
from pypdf import PdfWriter


def _numeric_key(path: Path) -> tuple:
    """
    Parse a filename stem into a tuple of numeric parts for sorting.
    E.g. '4.2' -> (4, 2), '10' -> (10,), 'intro' -> (float('inf'), 'intro')
    """
    parts = path.stem.split(".")
    result = []
    for p in parts:
        if re.fullmatch(r"\d+", p):
            result.append(int(p))
        else:
            # Non-numeric part: sort after all numeric files
            result.append(float("inf"))
            result.append(p)
            break
    return tuple(result)


def is_candidate_pdf(path: Path) -> bool:
    """
    True when a file should be considered a source input PDF.
    Excludes macOS resource fork artifacts and previously merged outputs.
    """
    if not path.is_file() or path.suffix.lower() != ".pdf":
        return False
    name = path.name.lower()
    if name.startswith("._"):
        return False
    if name.endswith("_merged.pdf"):
        return False
    return True


def sorted_pdfs(folder: Path) -> list[Path]:
    """Return PDF files in folder sorted by numeric filename key."""
    pdfs = [f for f in folder.iterdir() if is_candidate_pdf(f)]
    return sorted(pdfs, key=_numeric_key)


def merge_pdfs(pdf_paths: list[Path], output_path: Path) -> tuple[int, list[str]]:
    """
    Merge PDFs into output_path.
    Returns (count_merged, skipped_filenames_for_invalid_pdfs).
    """
    writer = PdfWriter()
    skipped_invalid: list[str] = []
    for pdf in pdf_paths:
        try:
            # Validate readability first so a single bad PDF does not kill the whole run.
            PdfReader(str(pdf), strict=False)
            writer.append(str(pdf))
        except Exception:
            skipped_invalid.append(pdf.name)

    if len(writer.pages) == 0:
        return 0, skipped_invalid

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    return len(writer.pages), skipped_invalid
