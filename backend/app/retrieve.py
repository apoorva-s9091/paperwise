"""
Phase 2d (v1): retrieval via direct vector search.

Embeds the user's question and calls the `match_chunks` Postgres
function (see schema_functions.sql) to get the top-k most similar
chunks, each tagged with its paper and section for citation.

Note: this is the simple version. Later we can add an LLM-driven
tree-navigation step (Groq) before this to narrow to relevant
sections first -- see the earlier design discussion. Swapping that in
later won't change what generate.py expects to receive.
"""

from supabase import create_client
from app.config import settings
from app.embeddings import embed_query

supabase = create_client(settings.supabase_url, settings.supabase_service_key)


def retrieve(question: str, paper_id: str | None = None, top_k: int = 8) -> list[dict]:
    """
    Returns a list of dicts: {chunk_text, section_title, paper_id, similarity}
    ordered by relevance (most similar first).
    """
    query_embedding = embed_query(question)

    result = supabase.rpc(
        "match_chunks",
        {
            "query_embedding": query_embedding,
            "match_paper_id": paper_id,
            "match_count": top_k,
        },
    ).execute()

    return result.data