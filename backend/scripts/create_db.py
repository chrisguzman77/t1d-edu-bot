# scripts/create_db.py
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "t1d.db"

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;                 -- better concurrency & crash safety
PRAGMA foreign_keys = ON;                  -- must enable in SQLite per-connection

-- Documents you ingest (one row per source page/section)
CREATE TABLE IF NOT EXISTS documents (
  id            TEXT PRIMARY KEY,          -- use your own UUID string
  source_url    TEXT,
  title         TEXT,
  section       TEXT,
  raw_text      TEXT NOT NULL,
  created_at    TEXT DEFAULT (datetime('now'))
);

-- Chunked text ready for retrieval
CREATE TABLE IF NOT EXISTS doc_chunks (
  id            TEXT PRIMARY KEY,          -- UUID string
  document_id   TEXT NOT NULL,
  chunk_index   INTEGER NOT NULL,
  content       TEXT NOT NULL,
  -- For SQLite we don't have a VECTOR type. We'll store a normalized embedding as BLOB bytes.
  embedding     BLOB,
  FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
  UNIQUE (document_id, chunk_index)
);

-- Query log (observability)
CREATE TABLE IF NOT EXISTS queries (
  id            TEXT PRIMARY KEY,          -- UUID string
  asked_at      TEXT DEFAULT (datetime('now')),
  question      TEXT NOT NULL,
  top_chunk_ids TEXT,                      -- comma-separated chunk IDs or JSON
  model_name    TEXT,
  latency_ms    INTEGER,
  refused       INTEGER DEFAULT 0          -- 0/1 boolean
);

CREATE TABLE IF NOT EXISTS feedback (
  id            TEXT PRIMARY KEY,
  query_id      TEXT NOT NULL,
  rating        INTEGER,                   -- -1, 0, +1
  comment       TEXT,
  FOREIGN KEY (query_id) REFERENCES queries(id) ON DELETE CASCADE
);

-- Helpful indexes (speed up searches/joins)
CREATE INDEX IF NOT EXISTS idx_doc_chunks_docid ON doc_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_chunks_chunk_index ON doc_chunks(chunk_index);
CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
CREATE INDEX IF NOT EXISTS idx_queries_asked_at ON queries(asked_at);
"""
def main():
    print("START: create_db.py", flush=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Creating DB at: {DB_PATH}", flush=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        # executescript can run multiple SQL statements in one call
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        print("Schema created successfully.", flush=True)
    except sqlite3.Error as e:
        print(f"SQLite error: {e}", flush=True)
        raise
    finally:
        conn.close()
        print("Closed connection.", flush=True)

if __name__ == "__main__":
    main()