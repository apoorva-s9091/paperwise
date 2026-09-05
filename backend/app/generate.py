"""
Phase 2e: generate a citation-grounded answer from retrieved chunks.

Uses Gemini 2.5 Flash (free tier) as decided. The prompt explicitly
forces the model to cite [Section Title] for every claim and to say
so plainly if the retrieved chunks don't actually answer the
question -- this is the anti-hallucination piece.
"""

import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.gemini_api_key)
_model = genai.GenerativeModel("gemini-3.6-flash")

SYSTEM_PROMPT = """You are a research assistant. Answer the user's question using
ONLY the excerpts provided below.

Rules:
- Start directly with the answer. No preamble like "Based on the provided
  excerpts" -- just answer.
- Be concise. Give the direct answer first, with only as much supporting
  detail as the question actually needs.
- Never use LaTeX or $ notation for math. Write formulas in plain, readable
  text instead -- e.g. "d_k = d_model / h = 64" not "$d_k = d_{model}/h$".
- End every distinct claim with a compact citation tag in this exact format:
  [Section Title] -- e.g. "...8 attention heads [Model Architecture]."
  Do not use the word "Section" or parentheses around it.
- If the excerpts don't contain enough information to answer, say so plainly
  in one sentence instead of guessing or using outside knowledge."""


def generate_answer(question: str, retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        return "I couldn't find anything relevant in the corpus to answer that."

    context_blocks = "\n\n---\n\n".join(
        f'[Section: "{c["section_title"]}"]\n{c["chunk_text"]}' for c in retrieved_chunks
    )

    prompt = f"""{SYSTEM_PROMPT}

EXCERPTS:
{context_blocks}

QUESTION: {question}

ANSWER:"""

    response = _model.generate_content(prompt)
    return response.text