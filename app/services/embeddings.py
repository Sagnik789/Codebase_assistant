import faiss
import numpy as np
import os
from sentence_transformers import SentenceTransformer
import pickle

class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.texts = []

        # 🔥 auto-load if exists
        if os.path.exists("faiss.index"):
            self.load()

    def add_texts(self, chunks):
        texts = [c["text"] for c in chunks]

        embeddings = self.model.encode(texts)

        if self.index is None:
            dim = len(embeddings[0])
            self.index = faiss.IndexFlatL2(dim)

        self.index.add(np.array(embeddings))
        self.texts.extend(chunks)

        # 🔥 SAVE after adding
        self.save()

    def search(self, query, k=5):
        if self.index is None or not self.texts:
            return []

        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding), k)

        results = []
        for idx in indices[0]:
            if idx < len(self.texts):
                results.append(self.texts[idx])

        return results

    # 🔥 SAVE FUNCTION
    def save(self):
        faiss.write_index(self.index, "faiss.index")
        with open("texts.pkl", "wb") as f:
            pickle.dump(self.texts, f)

    # 🔥 LOAD FUNCTION
    def load(self):
        self.index = faiss.read_index("faiss.index")
        with open("texts.pkl", "rb") as f:
            self.texts = pickle.load(f)
