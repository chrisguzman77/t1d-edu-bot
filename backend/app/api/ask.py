# app/api/ask.py
from fastapi import APIRouter
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer
from app.rag.repository import nearest_chunks_by_cosine, log_query

router = APIRouter()
EMB = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

DISCLAIMER = (
    "Disclaimer: Educational info only. No medical advice/dosing."
    "Contect your clincian for personal care. Emergencies: call local services."
)

class Ask(BaseModel):
    question: str

def safety_refusal(q: str) -> str | None:
    red = ["units of insulin", "dose", "boslus", "change my basal", "seizure", "unconscious", "dka", "trouble breathing"]
    if any(w in q.lower() for w in red):
        return ("I can't help with dosing or urgent issues. "
                "Please contact your diabetes care team or emergency services.")
    return None

@router.post("/ask")
def ask(payload: Ask):
    q = payload.question.strip()
    refusal = safety_refusal(q)
    if refusal:
        log_query(q, "none", 0, True, [])
        return {"answer": f"{DISCLAIMER}\n\n{refusal}", "citations": []}
    
    qvec = EMB.encode([q], convert_to_numpy=True)[0]
    hits = nearest_chunks_by_cosine(qvec, k=4)

    # Compose a simple sitched answer with tiny citations
    lines, ids = [], []
    for i, (score, row) in enumerate(hits, start=1):
        src = row["document_id"]
        lines.append(f"[[{i}]] {row['content'][:300]}…")
        ids.append(row["id"])
    body = "\n\n".join(lines) if lines else "I couldn't find anything relevant yet."

    log_query(q, "stitcher-edu", 25, False, ids)
    return {"answer": f"{DISCLAIMER}\n\nQ: {q}\n\n{body}", "citations": ids}