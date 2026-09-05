"""
Milestone 1: prove the core loop works end to end for ONE paper.

Given an arXiv ID:
  1. Fetch the PDF into memory (never written to disk).
  2. Parse it with Docling into structured markdown.
  3. Save the markdown to backend/data/markdown/{arxiv_id}.md
  4. Insert a row into the `papers` table in Supabase.

Run:
    python -m app.ingest 1706.03762
"""

import sys
import hashlib
import tempfile
from pathlib import Path

import httpx
import pymupdf4llm
from supabase import create_client

from app.config import settings

MARKDOWN_DIR = Path(__file__).parent.parent / "data" / "markdown"
MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)

supabase = create_client(settings.supabase_url, settings.supabase_service_key)


def fetch_pdf_bytes(arxiv_id: str) -> bytes:
    """Fetch a PDF from arXiv straight into memory. Nothing touches disk here."""
    url = f"https://arxiv.org/pdf/{arxiv_id}"
    response = httpx.get(url, follow_redirects=True, timeout=60)
    response.raise_for_status()
    return response.content


def parse_to_markdown(pdf_bytes: bytes) -> str:
    """Run PyMuPDF4LLM on in-memory PDF bytes, return structured markdown text.

    PyMuPDF4LLM needs a file path (not bytes directly), so we use a
    temp file that's deleted immediately after parsing -- this is NOT
    the same as the permanent PDF storage we decided to skip. It exists
    only for the moment PyMuPDF4LLM needs to read it.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        return pymupdf4llm.to_markdown(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def already_ingested(arxiv_id: str) -> bool:
    res = (
        supabase.table("papers")
        .select("id")
        .eq("arxiv_id", arxiv_id)
        .execute()
    )
    return len(res.data) > 0


def already_ingested_by_hash(content_hash: str) -> dict | None:
    res = (
        supabase.table("papers")
        .select("id, arxiv_id, markdown_path")
        .eq("content_hash", content_hash)
        .execute()
    )
    return res.data[0] if res.data else None


def ingest_paper(arxiv_id: str) -> None:
    if already_ingested(arxiv_id):
        print(f"[skip] {arxiv_id} already in papers table")
        return

    print(f"[fetch] downloading {arxiv_id} into memory...")
    pdf_bytes = fetch_pdf_bytes(arxiv_id)
    content_hash = hashlib.sha256(pdf_bytes).hexdigest()

    print(f"[parse] running PyMuPDF4LLM ({len(pdf_bytes) // 1024} KB)...")
    markdown_text = parse_to_markdown(pdf_bytes)

    markdown_path = MARKDOWN_DIR / f"{arxiv_id}.md"
    markdown_path.write_text(markdown_text, encoding="utf-8")
    print(f"[save] wrote {markdown_path}")

    print("[db] inserting row into Supabase...")
    supabase.table("papers").insert(
        {
            "arxiv_id": arxiv_id,
            "content_hash": content_hash,
            "markdown_path": str(markdown_path),
            "status": "processed",
        }
    ).execute()

    print(f"[done] {arxiv_id} ingested successfully.")


def ingest_uploaded_pdf(pdf_bytes: bytes, filename: str) -> dict:
    """
    Ingest a user-uploaded PDF that has no arXiv ID. Deduped by content
    hash instead -- uploading the exact same file twice reuses the
    existing row rather than reprocessing.

    Returns the paper row (dict with at least "id").
    """
    content_hash = hashlib.sha256(pdf_bytes).hexdigest()

    existing = already_ingested_by_hash(content_hash)
    if existing:
        print(f"[skip] {filename} already ingested (content hash match)")
        return existing

    print(f"[parse] running PyMuPDF4LLM on {filename} ({len(pdf_bytes) // 1024} KB)...")
    markdown_text = parse_to_markdown(pdf_bytes)

    markdown_path = MARKDOWN_DIR / f"{content_hash}.md"
    markdown_path.write_text(markdown_text, encoding="utf-8")
    print(f"[save] wrote {markdown_path}")

    print("[db] inserting row into Supabase...")
    result = (
        supabase.table("papers")
        .insert(
            {
                "arxiv_id": None,
                "content_hash": content_hash,
                "title": filename,
                "markdown_path": str(markdown_path),
                "status": "processed",
            }
        )
        .execute()
    )

    print(f"[done] {filename} ingested successfully.")
    return result.data[0]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.ingest <arxiv_id>")
        print("Example: python -m app.ingest 1706.03762")
        sys.exit(1)

    ingest_paper(sys.argv[1])