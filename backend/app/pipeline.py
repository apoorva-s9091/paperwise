"""
Runs the complete Phase 1 pipeline for one paper:
  fetch PDF -> Docling parse -> markdown -> sections -> chunks + embeddings

Run:
    python -m app.pipeline 1706.03762
"""

import sys

from app.ingest import ingest_paper, ingest_uploaded_pdf, supabase as ingest_client
from app.sectioning import section_paper
from app.embedding_pipeline import chunk_and_embed_paper


def run_full_pipeline(arxiv_id: str) -> None:
    ingest_paper(arxiv_id)

    res = (
        ingest_client.table("papers")
        .select("id, markdown_path")
        .eq("arxiv_id", arxiv_id)
        .execute()
    )
    if not res.data:
        print(f"[error] ingestion did not produce a paper row for {arxiv_id}")
        return

    paper = res.data[0]
    section_paper(paper["id"], paper["markdown_path"])
    chunk_and_embed_paper(paper["id"])

    print(f"\n[complete] {arxiv_id} is ready to query.")


def run_full_pipeline_from_bytes(pdf_bytes: bytes, filename: str) -> str:
    """
    Same pipeline as run_full_pipeline, but for a user-uploaded PDF
    with no arXiv ID. Returns the paper's id so the caller (the API
    endpoint) can hand it back to the frontend for scoped questions.
    """
    paper = ingest_uploaded_pdf(pdf_bytes, filename)
    paper_id = paper["id"]

    # If this was a dedup hit (already ingested before), sections/chunks
    # already exist -- skip re-processing.
    existing_sections = (
        ingest_client.table("sections").select("id").eq("paper_id", paper_id).limit(1).execute()
    )
    if not existing_sections.data:
        markdown_path = paper.get("markdown_path")
        section_paper(paper_id, markdown_path)
        chunk_and_embed_paper(paper_id)

    print(f"\n[complete] {filename} is ready to query.")
    return paper_id


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.pipeline <arxiv_id>")
        sys.exit(1)

    run_full_pipeline(sys.argv[1])