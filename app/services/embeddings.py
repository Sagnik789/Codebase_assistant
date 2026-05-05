import faiss
import numpy as np
import os
import pickle
import requests


class VectorStore:
    def __init__(self):
        self.index = None
        self.texts = []
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.embedding_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

        if os.path.exists("faiss.index"):
            self.load()

    def _embed_texts(self, texts):
        vectors = []
        for text in texts:
            payload = {
                "model": self.embedding_model,
                "input": text,
            }
            response = requests.post(f"{self.ollama_base_url}/api/embed", json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            emb = data.get("embeddings", [[]])[0]
            if not emb:
                raise ValueError("Empty embedding received from Ollama")
            vectors.append(emb)
        return np.array(vectors, dtype=np.float32)

    def add_texts(self, chunks):
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        embeddings = self._embed_texts(texts)

        if self.index is None:
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)

        self.index.add(embeddings)
        self.texts.extend(chunks)
        self.save()

    def search(self, query, k=5):
        if self.index is None or not self.texts:
            return []

        query_embedding = self._embed_texts([query])
        _distances, indices = self.index.search(query_embedding, k)

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.texts):
                results.append(self.texts[idx])

        return results

    def save(self):
        if self.index is None:
            return
        faiss.write_index(self.index, "faiss.index")
        with open("texts.pkl", "wb") as f:
            pickle.dump(self.texts, f)

    def load(self):
        self.index = faiss.read_index("faiss.index")
        with open("texts.pkl", "rb") as f:
            self.texts = pickle.load(f)