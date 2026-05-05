from fastapi import FastAPI
from pydantic import BaseModel
import logging
import os

from app.services.github_loader import clone_repo
from app.services.file_parser import get_code_files, read_file
from app.services.chunker import chunk_code
from app.services.rag_pipeline import ingest_chunks, query_rag, vector_store
from app.services.database import engine
from app.services.models import Base
from app.services.database import SessionLocal
from app.services.llm import get_model_name
from app.services.models import QueryHistory
from app.services.llm import get_model_name

Base.metadata.create_all(bind=engine)
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

    logging.info("Total files found: %s", len(files))

    for file in files:
        if "test" in file.lower():
            continue
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

    logging.info("Total chunks created: %s", len(all_chunks))

    ingest_chunks(all_chunks)

    logging.info(f"Files found: {len(files)}")
    logging.info(f"Chunks created: {len(all_chunks)}")

    return {
        "status": "indexed",
        "chunks": len(all_chunks)
    }


@app.get("/query")
def query(q: str, k: int = 12):
    db = SessionLocal()
    try:
        # 🔥 Get last 3 queries for context
        history_data = db.query(QueryHistory).order_by(QueryHistory.id.desc()).limit(3).all()

        history = [
            {"question": h.question, "answer": h.answer}
            for h in reversed(history_data)
        ]

        answer, sources = query_rag(q, k, history)

        # Save new query
        entry = QueryHistory(question=q, answer=answer)
        db.add(entry)
        db.commit()

        return {
            "answer": answer,
            "sources": sources[:3]
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@app.post("/reset_index")
def reset_index():
    if os.path.exists("faiss.index"):
        os.remove("faiss.index")
    if os.path.exists("texts.pkl"):
        os.remove("texts.pkl")

    vector_store.index = None
    vector_store.texts = []

    return {"status": "reset complete"}

@app.get("/history")
def get_history():
    db = SessionLocal()
    data = db.query(QueryHistory).all()
    db.close()

    return [
        {"q": d.question, "a": d.answer}
        for d in data
    ]


@app.get("/health")
def health():
    return {"status": "ok", "llm_model": get_model_name()}