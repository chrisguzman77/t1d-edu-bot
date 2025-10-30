# scripts/seed_db.py
import sqlite3
import uuid
from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer

DB_PATH = Path(__file__).resolve().parent.parent / "t1d.db"
EMB_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def uid() -> str:
    return str(uuid.uuid4())

def to_blob(vec_np: np.ndarray) -> bytes:
    """
    Store a float32 vector as bytes.
    We'll read it back with np.frombuffer(..., dtype=np.float32)
    """
    return vec_np.astype("float32").tobytes()

def main():
    print("Starting seed_db.py")
    print(f"Database path: {DB_PATH}")
    if not DB_PATH.exists():
        print("t1d.db not found yet.")
    conn = None
    
    try:
        print(f"Loading embedder: {EMB_NAME}")
        model = SentenceTransformer(EMB_NAME)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()
        print("Connected to SQLite and enabled foreign keys")

        # 1) Insert one document (prented it's a short ADA summary you wrote)
        print("Inserting 1 document into documents ...")
        doc_id = uid()
        cur.execute("""
                INSERT INTO documents (id, source_url, title, section, raw_text)
                VALUES (?, ?, ?, ?, ?)
            """, (
                doc_id,
                "https://diabetes.org/hypoglycemia",
                "ADA: Hypoglycemia",
                "Basics",
                "Hypoglycemia (low blood glucose) can cause shakiness, sweating, confusion..."  
            ))
        
        # 2) Make 2 chunks (toy example)
        print("Inserting 2 chunks into doc_documents ... ")
        chunks = [
            "Hypoglycemia is typically <70 mg/dl and may present with systems like sweating, shakiness.",
            "Severe hypoglycemia can lead to confusion or unconciousnes; seek urgent medical attention "
        ]

        # We'll fake an embedding with a sma; rando normalized vector (dim=8 just for demo).
        # In the real pipeline, you'd compute embeddings with sentence-transformers and likely larger dims (e.g, 384).
        for i, text in enumerate(chunks):
            chunk_id = uid()
            vec = model.encode([text], convert_to_numpy=True)[0].astype("float32")
            vec = vec / np.linalg.norm(vec)
            cur.execute("""
                INSERT INTO doc_chunks (id, document_id, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, (chunk_id, doc_id, i, text, to_blob(vec)))
            
        # 3) Insert a sample query row
        print("Inserting 1 example query into queries ...")
        q_id = uid()
        cur.execute("""
            INSERT INTO queries (id, question, model_name, latency_ms, refused, top_chunk_ids)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            q_id,
            "What are common symptoms of hypoglycemia?",
            "baseline-stitcher",
            42,
            0,
            "" # we can fill later
        ))

        conn.commit()
        print("Seeded demo data.")
    except sqlite3.OperationalError as e:
        print(f"SQLite OperationalError (schema/tables/SQL): {e}")
        print("   → Tip: Ensure you ran scripts/create_db.py to create tables first.")
    except sqlite3.ProgrammingError as e:
        print(f"SQLite ProgrammingError (placeholders/bindings): {e}")
        print("   → Tip: Check number of VALUES placeholders matches number of items supplied.")
    except ModuleNotFoundError as e:
        print(f"Module error: {e}")
        print("   → Tip: Install missing packages, e.g., `pip install numpy`.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if conn is not None:
            conn.close()
            print("Closed Connection.")

if __name__ == "__main__":
    main()
        
