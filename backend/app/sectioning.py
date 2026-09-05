"""
Phase 2a: turn one paper's flat markdown file into rows in `sections`.

Docling outputs proper markdown headers (#, ##, ###) for detected
sections -- we split on those directly rather than guessing structure
ourselves.
"""

import re
from pathlib import Path

from supabase import create_client
from app.config import settings

supabase = create_client(settings.supabase_url, settings.supabase_service_key)

# Matches a markdown header line: captures (#'s, header text)
HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def split_into_sections(markdown_text: str) -> list[dict]:
    """
    Returns a list of {title, level, content, order} dicts, one per
    header-delimited block. Content before the first header (if any)
    is dropped -- it's usually just the title/authors line Docling
    emits before the Abstract heading.
    """
    matches = list(HEADER_RE.finditer(markdown_text))
    sections = []

    for i, match in enumerate(matches):
        level = len(match.group(1))          # number of '#' chars
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
        content = markdown_text[start:end].strip()

        if not content:
            # Header with no body (rare, but skip rather than store empty)
            continue

        sections.append(
            {
                "title": title,
                "level": level,
                "content": content,
                "order": i,
            }
        )

    return sections


def section_paper(paper_id: str, markdown_path: str) -> int:
    """Reads the markdown file for a paper and inserts its sections. Returns count."""
    text = Path(markdown_path).read_text(encoding="utf-8")
    sections = split_into_sections(text)

    if not sections:
        print(f"[warn] no headers found in {markdown_path} -- nothing to insert")
        return 0

    rows = [
        {
            "paper_id": paper_id,
            "title": s["title"],
            "order": s["order"],
            "level": s["level"],
            "content": s["content"],
        }
        for s in sections
    ]

    supabase.table("sections").insert(rows).execute()
    print(f"[sections] inserted {len(rows)} sections for paper {paper_id}")
    return len(rows)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m app.sectioning <arxiv_id>")
        sys.exit(1)

    arxiv_id = sys.argv[1]
    res = supabase.table("papers").select("id, markdown_path").eq("arxiv_id", arxiv_id).execute()
    if not res.data:
        print(f"[error] no paper found with arxiv_id={arxiv_id}. Run ingest first.")
        sys.exit(1)

    paper = res.data[0]
    section_paper(paper["id"], paper["markdown_path"])