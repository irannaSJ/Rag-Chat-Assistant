import hashlib
import re

import numpy as np
from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self, model_name : str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.fallback_dim = 384

        try:
            self.model = SentenceTransformer(model_name)
        except Exception:
            self.model = None

    def _fallback_embed(self, text: str):
        vector = np.zeros(self.fallback_dim, dtype="float32")
        tokens = re.findall(r"\w+", text.lower())

        for token in tokens:
            index = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % self.fallback_dim
            vector[index] += 1.0

        norm = np.linalg.norm(vector)
        if norm:
            vector = vector / norm

        return vector

    def embed_chunks(self, chunks:list):
        texts = [chunk["chunk_text"] for chunk in chunks]

        if self.model is not None:
            embeddings = self.model.encode(
                texts,
                show_progress_bar = True,
                convert_to_numpy = True
            )
        else:
            embeddings = np.array([self._fallback_embed(text) for text in texts], dtype="float32")

        embedded_chunks = []

        for i, chunk in enumerate(chunks):
            embedded_chunks.append({
                "vector":embeddings[i],
                "chunk_text":chunk["chunk_text"],
                "metadata":chunk["metadata"]
            })

        return embedded_chunks
    def embed_query(self,query:str):
        if self.model is not None:
            return self.model.encode(query, convert_to_numpy = True)
        return self._fallback_embed(query)
