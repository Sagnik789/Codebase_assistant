import logging
import re
from app.services.embeddings import VectorStore
from app.services.llm import generate_answer

vector_store = VectorStore()
cache = {}


def ingest_chunks(chunks):
    vector_store.add_texts(chunks)


def _tokenize(text: str):
    return set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", text.lower()))


def _keyword_rerank(query: str, results: list, top_n: int = 6):
    """
    Lightweight reranker by token overlap.
    """
    q_tokens = _tokenize(query)
    if not q_tokens:
        return results[:top_n]

    scored = []
    for r in results:
        text = r.get("text", "")
        t_tokens = _tokenize(text)
        overlap = len(q_tokens & t_tokens)
        if "def " in text:
            overlap += 2
        if "class " in text:
            overlap += 2
        scored.append((overlap, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_n]]


def query_rag(query, k=12, history=None):
    if history is None:
        history = []

    if vector_store.index is None or len(vector_store.texts) == 0:
        return "Repository not indexed yet. Call /index_repo first.", []

    cache_key = (query, k)
    if cache_key in cache:
        return cache[cache_key]

    # wider recall
    raw_results = vector_store.search(query, k=k)

    # better precision
    results = _keyword_rerank(query, raw_results, top_n=6)

    logging.info("RAG retrieved=%s reranked=%s", len(raw_results), len(results))

    answer = generate_answer(query, results, history)

    cache[cache_key] = (answer, results)
    return answer, results