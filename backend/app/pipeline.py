"""
Runs the complete Phase 1 pipeline for one paper:
  fetch PDF -> Docling parse -> markdown -> sections -> chunks + embeddings

Run:
    python -m app.pipeline 1706.03762
"""

import sys

from app.ingest import ingest_paper, supabase as ingest_client
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.pipeline <arxiv_id>")
        sys.exit(1)

    run_full_pipeline(sys.argv[1])