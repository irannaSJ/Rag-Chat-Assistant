import hashlib
import re
import numpy as np
from fastembed import TextEmbedding


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.dimension = 384

        try:
            self.model = TextEmbedding(model_name=model_name)
        except Exception:
            self.model = None

    def _fallback_embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype="float32")
        tokens = re.findall(r"\w+", text.lower())

        for token in tokens:
            index = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % self.dimension
            vector[index] += 1.0

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def embed_chunks(self, chunks: list[dict]) -> list[dict]:
        if not chunks:
            return []

        texts = [chunk["chunk_text"] for chunk in chunks]

        if self.model is not None:
            embeddings = np.array(list(self.model.embed(texts)), dtype="float32")
        else:
            embeddings = np.array(
                [self._fallback_embed(text) for text in texts],
                dtype="float32",
            )

        embedded_chunks = []
        for i, chunk in enumerate(chunks):
            embedded_chunks.append({
                "vector": embeddings[i],
                "chunk_text": chunk["chunk_text"],
                "metadata": chunk["metadata"],
            })

        return embedded_chunks

    def embed_query(self, query: str) -> np.ndarray:
        if self.model is not None:
            return np.array(next(self.model.embed([query])), dtype="float32")
        return self._fallback_embed(query)