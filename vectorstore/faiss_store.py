import os
import pickle
import faiss
import numpy as np


class FAISSVectorStore:
    def __init__(self, vector_dim: int = 384, index_path: str = "data/vectorstore/faiss.index"):
        self.vector_dim = vector_dim
        self.index_path = index_path
        self.meta_path = f"{index_path}.meta"
        self.index = faiss.IndexFlatIP(vector_dim)
        self.metadata_store: list[dict] = []

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        vectors = np.array(vectors, dtype="float32", copy=True)
        faiss.normalize_L2(vectors)
        return vectors

    def add_embeddings(self, embedded_chunks: list[dict]) -> None:
        if not embedded_chunks:
            return

        raw_vectors = np.array([item["vector"] for item in embedded_chunks], dtype="float32")
        norm_vectors = self._normalize(raw_vectors)

        self.index.add(norm_vectors)

        for idx, item in enumerate(embedded_chunks):
            self.metadata_store.append({
                "chunk_text": item["chunk_text"],
                "metadata": item["metadata"],
                "vector": norm_vectors[idx],
            })

        self.save()

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata_store, f)

    def load(self) -> bool:
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.metadata_store = pickle.load(f)
            return True
        return False

    def list_sources(self) -> list[dict]:
        """Return unique ingested documents with their chunk counts."""
        sources: dict[str, dict] = {}
        for item in self.metadata_store:
            meta = item["metadata"]
            source_id = meta.get("source_id") or meta.get("source_name", "unknown")
            if source_id not in sources:
                sources[source_id] = {
                    "source_id": source_id,
                    "source_name": meta.get("source_name", "Untitled"),
                    "source_type": meta.get("source_type", "UNKNOWN"),
                    "url": meta.get("url"),
                    "chunk_count": 0,
                }
            sources[source_id]["chunk_count"] += 1
        return list(sources.values())

    def delete_source(self, source_id: str) -> bool:
        """Remove all chunks for a given source_id and rebuild the FAISS index."""
        remaining = [
            item for item in self.metadata_store
            if (item["metadata"].get("source_id") or item["metadata"].get("source_name")) != source_id
        ]

        if len(remaining) == len(self.metadata_store):
            return False

        self.metadata_store = remaining
        self.index = faiss.IndexFlatIP(self.vector_dim)

        if self.metadata_store:
            vectors = np.array([item["vector"] for item in self.metadata_store], dtype="float32")
            self.index.add(vectors)

        self.save()
        return True

    def clear(self) -> None:
        self.index = faiss.IndexFlatIP(self.vector_dim)
        self.metadata_store = []
        self.save()

    @property
    def total_chunks(self) -> int:
        return self.index.ntotal

    def search(self, query_vector: np.ndarray, top_k: int = 4) -> list[dict]:
        if self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        q_vec = self._normalize(np.array([query_vector], dtype="float32"))

        scores, indices = self.index.search(q_vec, k)
        results = []

        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:
                continue
            item = self.metadata_store[idx]
            results.append({
                "chunk_text": item["chunk_text"],
                "metadata": item["metadata"],
                "vector": item.get("vector"),
                "score": float(score),
            })

        return results