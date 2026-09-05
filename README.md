# paperwise

Tree-structured RAG for research papers — parses PDFs into section-aware
markdown for citation-grounded Q&A, no chunk-boundary context loss.

Paperwise lets you query a corpus of research papers directly and get
citation-grounded answers pulled from the actual text — not a ranked
list of links, not a chatbot that hallucinates references. Instead of
naive fixed-size chunking, papers are parsed into structured,
section-aware markdown so retrieval respects the paper's actual
structure (Abstract, Methods, Results) instead of cutting through it
arbitrarily.

## Status

**Phase 1 (core pipeline) — complete.** PDF → markdown → sections →
chunks → embeddings → retrieval → cited answer, working end to end.

**Phase 2 (GUI) — in progress.** FastAPI backend exposes the pipeline
over HTTP; a Next.js frontend (with Clerk auth) lets you upload a
paper directly and ask questions scoped to just that paper.

```
> What is the main idea of R2-ROUTER, and how does it differ from a
  traditional reactive LLM router?

The main idea of R2-ROUTER is to treat the output length budget as a
controllable variable, jointly selecting the optimal LLM and output
token budget while enforcing that budget using length-constrained
instructions [Abstract] [1. Introduction].

R2-ROUTER differs from traditional reactive routers in the following
key ways: Traditional reactive routers profile each LLM as a single
static operating point ("routing on points")... R2-ROUTER models each
LLM as a quality-cost curve ("routing on curves")...
```

Next up: async job queue for ingestion, Library/Discover sections,
deployment.

## How it works

1. **Ingest** — fetch a paper's PDF (by arXiv ID, or accept a direct
   upload) straight into memory, parse it into structured markdown
   with PyMuPDF4LLM. No PDF ever touches disk permanently.
2. **Section** — split the markdown into sections along its actual
   header structure (Abstract, Introduction, Methods, ...) instead of
   guessing.
3. **Chunk** — sections that fit under a token threshold stay whole.
   Longer sections split on paragraph boundaries with ~15% overlap.
   Tables and code blocks are never split.
4. **Embed** — each chunk is embedded via Gemini's embedding API and
   stored in Postgres (Supabase) with pgvector.
5. **Retrieve** — a question is embedded and matched against chunks via
   cosine similarity, returning the most relevant sections. Questions
   can be scoped to one uploaded paper or run across the whole corpus.
6. **Generate** — retrieved sections are fed to Gemini with a prompt
   that forces citation of the source section for every claim, and
   refuses to guess if the corpus doesn't contain the answer.

## Stack

- **Backend**: Python, FastAPI
- **Database**: Supabase (Postgres + pgvector)
- **Auth**: Clerk
- **Parsing**: PyMuPDF4LLM
- **Embeddings**: Gemini Embedding API
- **Generation**: Gemini 3.6 Flash
- **Frontend**: Next.js

Everything runs on free tiers — no paid infrastructure required.

## Why not just chunk everything?

Standard RAG splits documents into arbitrary fixed-size chunks, which
frequently cuts a relevant idea in half across a chunk boundary.
Paperwise chunks along section structure first — most sections in a
paper (Methods, Results) fit whole in one chunk. Only sections long
enough to exceed the token threshold get split, and only along
paragraph breaks, with overlap so nothing is fully lost at the seam.
