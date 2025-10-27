# t1d-edu-bot
# 🩸 Type 1 Diabetes Educational Chatbot (T1D-Edu-Bot)

An open-source AI chatbot that provides **general, evidence-based information** about **Type 1 Diabetes (T1D)** using trusted public sources such as the **ADA, JDRF, NIDDK, and CDC**.  
It does *not* provide medical advice or personalized treatment recommendations.

---

## 🚀 Features
- ⚡ **FastAPI backend** with REST API (`/ask`)
- 🔍 **Retrieval-Augmented Generation (RAG)** using vector embeddings (pgvector / FAISS)
- 🧠 **Local knowledge base** built from ADA, JDRF, NIDDK, and CDC documents
- 🛡️ **Safety guardrails** (no dosing, diagnosis, or emergency advice)
- 🧾 **Citation tracking** for every answer
- 💬 Optional **Streamlit / React front-end**

---

## 🏗️ Project Structure

