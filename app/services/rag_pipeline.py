from app.services.embeddings import VectorStore
from app.services.llm import generate_answer

# 🔥 SINGLE shared instance (used everywhere)
vector_store = VectorStore()

# simple cache (optional but useful)
cache = {}


def ingest_chunks(chunks):
    vector_store.add_texts(chunks)


def query_rag(query, k=5, history =[]):
    # ✅ handle empty index
    if vector_store.index is None or len(vector_store.texts) == 0:
        return "Repository not indexed yet. Call /index_repo first.", []

    # ✅ cache for speed
    if query in cache:
        return cache[query]

    results = vector_store.search(query, k=k)

    print("\n===== RETRIEVED CHUNKS =====")
    for i, r in enumerate(results):
        print(f"\n--- Chunk {i} ---")
        print(r["text"][:300])
    print("============================\n")

    answer = generate_answer(query, results, history)

    cache[query] = (answer, results)

    return answer, results