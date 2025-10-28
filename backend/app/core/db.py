# app/core/db.py
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parents[2] / "t1d.db"

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    # return rows as dict-like objects
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()