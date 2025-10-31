# backend/scripts/ingest.py

import argparse, os, glob, json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
try:
    import faiss
    HAVE_FAISS = True
except Exception:
    HAVE_FAISS = False
import numpy as np

def read_docs(input_dir):
    docs = []
    for p in glob.glob(os.path.join(input_dir, "*.md")):
        with open(p, "r", encoding="utf-8") as f:
            docs.append({"path": p, "text": f.read()})
    return docs

def chunk(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=150, length_function=len
    )
    return splitter.split_text(text)

def main(args):
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(args.index, exist_ok=True)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    all_chunks, meta = [], []
    for doc in read_docs(args.input):
        pieces = chunk(doc["text"])
        for i, piece in enumerate(pieces):
            all_chunks.append(piece)
            meta.append({"source": doc["path"], "chunk": i})

    # embeddings 
    vecs = model.encode(all_chunks, convert_to_numpy=True, normalize_embeddings=True)

    # save processed data
    with open(os.path.join(args.out, "chunks.json1"), "w", encoding="utf-8") as w:
        for m, t in zip(meta, all_chunks):
            w.write(json.dumps({"meta": m, "text": t}) + "\n")

    # build FAISS (inner product works with normalized vectors)
    if HAVE_FAISS:
        index = faiss.IndexFlatIP(vecs.shape[1])
        index.add(vecs.astype("float32"))
        faiss.write_index(index, os.path.join(args.index, "faiss.index"))
        print(f"Ingested {len(all_chunks)} chunks.")
        print(f"Saved FAISS index to {args.index}")
    else:
        print("FAISS not available; skipping FAISS index build. (Embeddings still saved.)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--index", required=True)
    main(ap.parse_args())