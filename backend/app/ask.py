"""
Ask a question against the corpus (or one paper, if you pass an arxiv_id).

Run:
    python -m app.ask "What optimizer did they use?"
    python -m app.ask "What optimizer did they use?" --paper 1706.03762
"""

import sys

from supabase import create_client
from app.config import settings
from app.retrieve import retrieve
from app.generate import generate_answer

supabase = create_client(settings.supabase_url, settings.supabase_service_key)


def resolve_paper_id(arxiv_id: str) -> str | None:
    res = supabase.table("papers").select("id").eq("arxiv_id", arxiv_id).execute()
    return res.data[0]["id"] if res.data else None


def ask(question: str, arxiv_id: str | None = None) -> str:
    paper_id = resolve_paper_id(arxiv_id) if arxiv_id else None
    return ask_by_paper_id(question, paper_id)


def ask_by_paper_id(question: str, paper_id: str | None = None) -> str:
    """Same as ask(), but takes the paper's actual id directly -- needed
    for uploaded papers, which have no arxiv_id to resolve from."""
    chunks = retrieve(question, paper_id=paper_id)

    print(f"[retrieved] {len(chunks)} chunks:")
    for c in chunks:
        print(f'  - "{c["section_title"]}" (similarity: {c["similarity"]:.3f})')

    return generate_answer(question, chunks)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python -m app.ask "your question" [--paper <arxiv_id>]')
        sys.exit(1)

    question = sys.argv[1]
    paper_arg = None
    if "--paper" in sys.argv:
        paper_arg = sys.argv[sys.argv.index("--paper") + 1]

    print(f"\n[answer]\n{ask(question, paper_arg)}")