# app/rag/repository.py
from typing import List, Dict, Any, Tuple
import numpy as np
from app.core.db import get_conn

def _from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)

def log_query(question: str, model_name: str, latency_ms: int, refused: bool, top_chunk_ids: List[str]) -> str:
    import uuid
    q_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute("""
                     INSERT INTO queries (id, question, model_name, latency_ms, refused, top_chunk_ids)
                     VALUES (?, ?, ?, ?, ?, ?)
                     """, (q_id, question, model_name, latency_ms, int(refused), ",".join(top_chunk_ids)))
        conn.commit()
    return q_id

def fetch_chunks(limit: int = 10) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.execute("SELECT id, document_id, chunk_index, embedding FROM doc_chunks LIMIT ?", (limit,))
        rows =  cur.fetchall()
        return [dict(r) for r in rows]
    
def nearest_chunks_by_cosine(query_vec: np.ndarray, k: int = 4) -> List[Tuple[float, Dict[str, Any]]]:
    """
    Simple in-Python cosine similarity over embeddings stored in SQLite as BLOB.
    """
    with get_conn() as conn:
        cur = conn.execute("SELECT id, document_id, chunk_index, content, embedding FROM doc_chunks")
        rows = cur.fetchall()

    scored = []
    q = query_vec / (np.linalg.norm(query_vec) + 1e12)
    for r in rows:
        emb = _from_blob(r["embedding"])
        if emb.shape != q.shape:
            continue
        emb = emb / (np.linalg.norm(emb) + 1e-12)
        score = float(np.dot(q, emb)) # cosine since both normalized
        scored.append((score, dict(r)))

    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[:k]