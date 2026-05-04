from fastapi import FastAPI
from pydantic import BaseModel
import logging
import os

from app.services.github_loader import clone_repo
from app.services.file_parser import get_code_files, read_file
from app.services.chunker import chunk_code
from app.services.rag_pipeline import ingest_chunks, query_rag, vector_store

logging.basicConfig(level=logging.INFO)
app = FastAPI()


class RepoRequest(BaseModel):
    repo_url: str


@app.get("/")
def root():
    return {"message": "AI Codebase Assistant Running"}


@app.post("/index_repo")
def index_repo(request: RepoRequest):
    # ✅ avoid re-index if already loaded from disk
    if vector_store.index is not None and len(vector_store.texts) > 0:
        return {
            "status": "already indexed",
            "chunks": len(vector_store.texts)
        }

    repo_path = clone_repo(request.repo_url)
    files = get_code_files(repo_path)

    all_chunks = []

    print(f"Total files found: {len(files)}")

    for file in files:
        content = read_file(file)

        if not content or not content.strip():
            continue

        if len(content) < 50:
            continue

        chunks = chunk_code(content, chunk_size=50)
        chunks = [c for c in chunks if c.strip()]

        for chunk in chunks:
            all_chunks.append({
                "text": chunk,
                "source": file
            })

    print(f"Total chunks created: {len(all_chunks)}")

    ingest_chunks(all_chunks)

    logging.info(f"Files found: {len(files)}")
    logging.info(f"Chunks created: {len(all_chunks)}")

    return {
        "status": "indexed",
        "chunks": len(all_chunks)
    }


@app.get("/query")
def query(q: str, k: int = 5):
    try:
        answer, sources = query_rag(q, k)
        return {
            "answer": answer,
            "sources": sources[:3]
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/reset_index")
def reset_index():
    if os.path.exists("faiss.index"):
        os.remove("faiss.index")
    if os.path.exists("texts.pkl"):
        os.remove("texts.pkl")

    vector_store.index = None
    vector_store.texts = []

    return {"status": "reset complete"}


@app.get("/health")
def health():
    return {"status": "ok"}