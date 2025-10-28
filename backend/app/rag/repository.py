# app/rag/repository.py
from typing import List, Dict, Any, Tuple
import numpy as np
from app.core.db import get_conn

def _from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)

def log_query(question: str, model_name: str, latency_ms: int, refused: bool, top_chunk_ids: List[str]) -> str:
    import uuid, json_id 
    q_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute("""
                     INSERT INTO queries (id, question, model_name, latency_ms, refused, top_chunk_ids)
                     VALUES (?, ?, ?, ?, ?, ?)
                     """, (q_id, question, model_name, latency_ms, int(refused), ",".join(top_chunk_ids)))
        conn.commit()
    return q_id

