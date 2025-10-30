# app/api/main.py
from fastapi import FastAPI
from app.api.ask import router as ask_router

app = FastAPI(title="T1D Educational Bot (SQLite)")

app.include_router(ask_router, prefix="")