"""
Phase 2 (GUI wrapper): expose the existing CLI pipeline as an HTTP API.

No pipeline logic changes here -- this just wraps pipeline.py and ask.py
behind two endpoints so a frontend can call them instead of the CLI.

Run:
    uvicorn app.api:app --reload
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.pipeline import run_full_pipeline, run_full_pipeline_from_bytes
from app.ask import ask, ask_by_paper_id, resolve_paper_id
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
    paper_id: str | None = None  # for uploaded papers, which have no arxiv_id


@app.post("/papers")
def ingest_endpoint(req: IngestRequest):
    """Ingest, section, chunk, and embed a paper by arXiv ID."""
    try:
        run_full_pipeline(req.arxiv_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "processed", "arxiv_id": req.arxiv_id}


@app.post("/papers/upload")
async def upload_endpoint(file: UploadFile = File(...)):
    """Ingest a user-uploaded PDF. Returns the paper's id so the
    frontend can scope subsequent questions to just this paper."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()

    try:
        paper_id = run_full_pipeline_from_bytes(pdf_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "processed", "paper_id": paper_id, "filename": file.filename}


@app.get("/papers")
def list_papers():
    """List all papers currently ingested, for the frontend's paper picker."""
    res = supabase.table("papers").select("id, arxiv_id, title, status").execute()
    return res.data


@app.post("/ask")
def ask_endpoint(req: AskRequest):
    """
    Ask a question. Scoping priority: explicit paper_id > arxiv_id > all papers.
    paper_id is what the frontend uses for uploaded papers (no arxiv_id exists).
    """
    try:
        if req.paper_id:
            answer = ask_by_paper_id(req.question, req.paper_id)
        elif req.arxiv_id:
            paper_id = resolve_paper_id(req.arxiv_id)
            if not paper_id:
                raise HTTPException(status_code=404, detail=f"No paper found for {req.arxiv_id}")
            answer = ask(req.question, req.arxiv_id)
        else:
            answer = ask(req.question)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"answer": answer}