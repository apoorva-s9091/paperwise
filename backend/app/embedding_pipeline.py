"""
Phase 2c: for every section of a paper, chunk its content and embed
each chunk, writing rows into `chunks`.

Run after sectioning.py has populated `sections` for the paper.
"""

from supabase import create_client
from app.config import settings
from app.chunking import chunk_section
from app.embeddings import embed_documents

supabase = create_client(settings.supabase_url, settings.supabase_service_key)


def chunk_and_embed_paper(paper_id: str) -> int:
    sections_res = (
        supabase.table("sections")
        .select("id, content")
        .eq("paper_id", paper_id)
        .execute()
    )
    sections = sections_res.data
    if not sections:
        print(f"[warn] no sections found for paper {paper_id} -- run sectioning first")
        return 0

    # Build the full list of chunk texts across ALL sections first,
    # remembering which section + order each one belongs to. This lets
    # us embed everything in one API call instead of one call per
    # section, which matters a lot on rate-limited free tiers.
    all_texts: list[str] = []
    all_meta: list[dict] = []  # {section_id, order}

    for section in sections:
        texts = chunk_section(section["content"])
        for i, text in enumerate(texts):
            all_texts.append(text)
            all_meta.append({"section_id": section["id"], "order": i})

    if not all_texts:
        print(f"[warn] no chunk text produced for paper {paper_id}")
        return 0

    embeddings = embed_documents(all_texts)

    rows = [
        {
            "section_id": meta["section_id"],
            "order": meta["order"],
            "text": text,
            "embedding": embedding,
        }
        for meta, text, embedding in zip(all_meta, all_texts, embeddings)
    ]
    supabase.table("chunks").insert(rows).execute()

    print(f"[chunks] inserted {len(rows)} chunks across {len(sections)} sections")
    return len(rows)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m app.embedding_pipeline <arxiv_id>")
        sys.exit(1)

    arxiv_id = sys.argv[1]
    res = supabase.table("papers").select("id").eq("arxiv_id", arxiv_id).execute()
    if not res.data:
        print(f"[error] no paper found with arxiv_id={arxiv_id}")
        sys.exit(1)

    chunk_and_embed_paper(res.data[0]["id"])