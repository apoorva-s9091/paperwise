"""
Phase 2b: turn each section's content into one or more chunks.

Rules (decided earlier in the design discussion):
  - Section fits under CHUNK_TOKEN_LIMIT -> one chunk, no splitting.
  - Section too long -> split on paragraph boundaries, ~15% overlap
    between consecutive chunks so an idea spanning a paragraph break
    isn't fully lost from either side.
  - Tables and code blocks are atomic -- never split internally, even
    if that makes one chunk larger than the limit.
"""

import re
import tiktoken

ENCODER = tiktoken.get_encoding("cl100k_base")

CHUNK_TOKEN_LIMIT = 500
OVERLAP_TOKENS = 70  # ~15% of 500

# A markdown table block: consecutive lines starting with '|'
TABLE_BLOCK_RE = re.compile(r"(?:^\|.*\|$\n?)+", re.MULTILINE)
# A fenced code block: ```...```
CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)


def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text))


def _protect_atomic_blocks(text: str) -> tuple[str, dict]:
    """
    Replace tables/code blocks with placeholders so paragraph-splitting
    doesn't cut through them. Returns (modified_text, placeholder_map).
    """
    placeholders = {}
    counter = 0

    def _stash(match: re.Match) -> str:
        nonlocal counter
        key = f"\x00ATOMIC_{counter}\x00"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    text = CODE_BLOCK_RE.sub(_stash, text)
    text = TABLE_BLOCK_RE.sub(_stash, text)
    return text, placeholders


def _restore_atomic_blocks(text: str, placeholders: dict) -> str:
    for key, original in placeholders.items():
        text = text.replace(key, original)
    return text


def chunk_section(content: str) -> list[str]:
    """Returns a list of chunk texts for one section's content."""
    total_tokens = count_tokens(content)
    if total_tokens <= CHUNK_TOKEN_LIMIT:
        return [content]

    protected_text, placeholders = _protect_atomic_blocks(content)
    paragraphs = [p for p in protected_text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current_paras: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if current_tokens + para_tokens > CHUNK_TOKEN_LIMIT and current_paras:
            # Close out the current chunk
            chunk_text = "\n\n".join(current_paras)
            chunks.append(_restore_atomic_blocks(chunk_text, placeholders))

            # Start next chunk with overlap: carry the tail of the
            # previous chunk forward (last paragraph, or a token-based
            # tail if that single paragraph is itself large)
            overlap_para = current_paras[-1]
            if count_tokens(overlap_para) > OVERLAP_TOKENS:
                # trim to roughly the last OVERLAP_TOKENS worth of text
                words = overlap_para.split()
                overlap_para = " ".join(words[-(OVERLAP_TOKENS * 3 // 4):])
            current_paras = [overlap_para]
            current_tokens = count_tokens(overlap_para)

        current_paras.append(para)
        current_tokens += para_tokens

    if current_paras:
        chunk_text = "\n\n".join(current_paras)
        chunks.append(_restore_atomic_blocks(chunk_text, placeholders))

    return chunks