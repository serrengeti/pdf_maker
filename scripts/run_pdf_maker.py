"""
One-shot PDF merger.

Usage examples:
  # From a local zip file
  python run_pdf_maker.py --subject cardiology --zip-path "C:/path/to/cardiology.zip"

  # From a download link
  python run_pdf_maker.py --subject cardiology --zip-link "https://..."

  # Dry run (show what would happen without writing anything)
  python run_pdf_maker.py --subject cardiology --zip-path "C:/path/to/cardiology.zip" --dry-run
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

# Allow running from any working directory
sys.path.insert(0, str(Path(__file__).parent))

from input_zip import extract_zip, resolve_zip
from merge_utils import is_candidate_pdf, merge_pdfs, sorted_pdfs

OUTPUT_ROOT = Path(__file__).parent.parent / "output"


def find_topic_folders(subject_root: Path) -> list[Path]:
    """
    Return all leaf directories that contain at least one PDF.
    Walks the full tree so nesting depth doesn't matter.
    """
    topics = []
    for folder in sorted(subject_root.rglob("*")):
        if folder.is_dir():
            pdfs = [f for f in folder.iterdir() if is_candidate_pdf(f)]
            if pdfs:
                topics.append(folder)
    return topics


def run(subject: str, zip_path: str | None, zip_link: str | None, dry_run: bool) -> None:
    created: list[str] = []
    skipped: list[str] = []
    empty: list[str] = []
    invalid_skipped_total = 0

    with tempfile.TemporaryDirectory(prefix="pdf_maker_") as tmp:
        tmp_path = Path(tmp)

        # --- Resolve & extract zip ---
        zip_file = resolve_zip(zip_path, zip_link, tmp_path)
        subject_root = extract_zip(zip_file, tmp_path / "extracted")
        print(f"Extracted to: {subject_root}")

        # --- Discover topic folders ---
        topics = find_topic_folders(subject_root)
        if not topics:
            print("No topic folders with PDFs found. Exiting.")
            return

        output_dir = OUTPUT_ROOT / f"{subject}_processed"

        print(f"\nFound {len(topics)} topic folder(s).\n")

        for topic_folder in topics:
            topic_name = topic_folder.name
            out_pdf = output_dir / f"{topic_name}_merged.pdf"

            pdfs = sorted_pdfs(topic_folder)
            if not pdfs:
                empty.append(topic_name)
                print(f"  [EMPTY]   {topic_name}  — no valid PDFs found, skipping.")
                continue

            if out_pdf.exists():
                skipped.append(topic_name)
                print(f"  [SKIP]    {topic_name}  — merged PDF already exists.")
                continue

            order = " -> ".join(p.name for p in pdfs)
            if dry_run:
                print(f"  [DRY-RUN] {topic_name}  ({len(pdfs)} PDFs) | order: {order}")
                created.append(topic_name)
                continue

            print(f"  [MERGE]   {topic_name}  ({len(pdfs)} PDFs) | order: {order}")
            merged_pages, invalid_skipped = merge_pdfs(pdfs, out_pdf)
            invalid_skipped_total += len(invalid_skipped)
            if invalid_skipped:
                print(f"            -> skipped invalid: {', '.join(invalid_skipped)}")
            if merged_pages == 0:
                empty.append(topic_name)
                print("            -> no readable source PDFs, skipping output.")
                continue
            created.append(topic_name)
            print(f"            -> saved: {out_pdf}")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if dry_run:
        print(f"  Would create : {len(created)} merged PDF(s)")
    else:
        print(f"  Created      : {len(created)} merged PDF(s)")
    print(f"  Skipped      : {len(skipped)} (already existed)")
    print(f"  Empty/invalid: {len(empty)} folder(s) with no PDFs")
    if not dry_run:
        print(f"  Bad PDFs skip: {invalid_skipped_total} file(s)")
    if not dry_run:
        print(f"\nOutput folder: {output_dir.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge topic PDFs from a subject zip.")
    parser.add_argument("--subject", required=True, help="Subject name, e.g. cardiology")

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--zip-path", help="Local path to the subject zip file.")
    source.add_argument("--zip-link", help="Download URL for the subject zip file.")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be merged without writing any files.",
    )

    args = parser.parse_args()
    run(
        subject=args.subject,
        zip_path=args.zip_path,
        zip_link=args.zip_link,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
