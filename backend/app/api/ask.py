# app/api/ask.py
from fastapi import APIRouter
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer
from app.rag.repository import nearest_chunks_by_cosine, log_query
from app.llm.compose import compose_answer

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

    # Build the LLM response
    snippets = [row["content"] for _, row in hits]
    body = compose_answer(q, snippets)

    log_query(q, "llm-edu", 50, False, [r["id"] for _, r in hits])
    return {"answer": f"{DISCLAIMER}\n\n{body}", "citations": [r["id"] for _, r in hits]}