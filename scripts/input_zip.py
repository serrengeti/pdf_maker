"""
Zip retrieval and extraction utilities.
Supports a local file path or an HTTP/HTTPS download URL.
"""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path


def resolve_zip(zip_path: str | None, zip_link: str | None, work_dir: Path) -> Path:
    """
    Return a local Path to the zip file, downloading it first if a link was supplied.
    """
    if zip_path:
        local = Path(zip_path)
        if not local.exists():
            raise FileNotFoundError(f"Zip path not found: {local}")
        return local

    if zip_link:
        import requests  # optional dependency
        print(f"Downloading zip from {zip_link} ...")
        response = requests.get(zip_link, stream=True, timeout=120)
        response.raise_for_status()
        dest = work_dir / "download.zip"
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        print(f"Downloaded to {dest}")
        return dest

    raise ValueError("Provide either --zip-path or --zip-link.")


def extract_zip(zip_file: Path, extract_to: Path) -> Path:
    """Extract zip into extract_to and return the root folder inside it."""
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_file, "r") as zf:
        zf.extractall(extract_to)
    # If the zip has a single top-level folder, return it; otherwise return extract_to
    children = [c for c in extract_to.iterdir()]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return extract_to
