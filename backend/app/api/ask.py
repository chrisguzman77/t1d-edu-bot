# app/api/ask.py
from fastapi import APIRouter
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer
from app.rag.repository import nearest_chunks_by_cosine, log_query
from app.safety.rules import safety_check, DISCLAIMER
from app.llm.compose import compose_answer



router = APIRouter()
EMB = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

class Ask(BaseModel):
    question: str

@router.post("/ask")
def ask(payload: Ask):
    q = payload.question.strip()

    #1) SAFETY CHECK - early if blocked
    s = safety_check(q)
    if s.blocked:
        log_query(q, "none", 0, True, [])
        return {"answer": s.message, "citations": []}
    
    #2) Embed and retrieve from SQLite store
    qvec = EMB.encode([q], convert_to_numpy=True)[0]
    hits = nearest_chunks_by_cosine(qvec, k=4)

    #3) Compose with LLM (or stitch prefer)
    snippets = [row["content"] for _, row in hits]
    body = compose_answer(q, snippets)

    #4) Log + respond
    ids = [r["id"] for _, r in hits]
    log_query(q, "llm-edu", 50, False, ids)
    return {"answer": f"{DISCLAIMER}\n\n{body}", "citations": ids}
