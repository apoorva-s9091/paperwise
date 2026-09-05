"""
Phase 2 (GUI wrapper): expose the existing CLI pipeline as an HTTP API.

No pipeline logic changes here -- this just wraps pipeline.py and ask.py
behind two endpoints so a frontend can call them instead of the CLI.

Run:
    uvicorn app.api:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.pipeline import run_full_pipeline
from app.ask import ask, resolve_paper_id
from app.ingest import supabase

app = FastAPI(title="Paperwise API")

# Allow the frontend (running on a different port/origin) to call this API.
# Wide open for local dev -- tighten this before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    arxiv_id: str


class AskRequest(BaseModel):
    question: str
    arxiv_id: str | None = None


@app.post("/papers")
def ingest_endpoint(req: IngestRequest):
    """Ingest, section, chunk, and embed a paper by arXiv ID."""
    try:
        run_full_pipeline(req.arxiv_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "processed", "arxiv_id": req.arxiv_id}


@app.get("/papers")
def list_papers():
    """List all papers currently ingested, for the frontend's paper picker."""
    res = supabase.table("papers").select("arxiv_id, title, status").execute()
    return res.data


@app.post("/ask")
def ask_endpoint(req: AskRequest):
    """Ask a question against the corpus, or one paper if arxiv_id is given."""
    if req.arxiv_id:
        paper_id = resolve_paper_id(req.arxiv_id)
        if not paper_id:
            raise HTTPException(status_code=404, detail=f"No paper found for {req.arxiv_id}")

    try:
        answer = ask(req.question, req.arxiv_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"answer": answer}