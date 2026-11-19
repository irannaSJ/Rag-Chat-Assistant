import numpy as np


class Retriever:
    def __init__(
        self,
        embedder,
        vector_store,
        top_k: int = 4,
        fetch_k: int = 12,
        lambda_param: float = 0.65,
        min_score: float = 0.25,
    ):
        """
        lambda_param:
        - 1.0 -> only relevance
        - 0.0 -> only diversity
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.top_k = top_k
        self.fetch_k = fetch_k
        self.lambda_param = lambda_param
        self.min_score = min_score

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def retrieve(self, query: str) -> list[dict]:
        query_vector = self.embedder.embed_query(query)
        candidates = self.vector_store.search(query_vector, top_k=self.fetch_k)

        # Filter out low-similarity noise
        candidates = [c for c in candidates if c["score"] >= self.min_score]
        if not candidates:
            return []

        if len(candidates) <= self.top_k:
            return candidates

        # Reuse stored normalized vectors; fall back to encoding only if missing
        candidate_vectors = [
            c["vector"] if c.get("vector") is not None else self.embedder.embed_query(c["chunk_text"])
            for c in candidates
        ]

        selected = []
        selected_indices = []

        # Step 1: Pick the highest-scoring chunk first
        scores = [c["score"] for c in candidates]
        first_idx = int(np.argmax(scores))
        selected.append(candidates[first_idx])
        selected_indices.append(first_idx)

        # Step 2: Maximal Marginal Relevance (MMR) selection
        while len(selected) < self.top_k:
            mmr_scores = []

            for i, candidate in enumerate(candidates):
                if i in selected_indices:
                    continue

                relevance = candidate["score"]
                diversity = max(
                    self._cosine_similarity(candidate_vectors[i], candidate_vectors[j])
                    for j in selected_indices
                )

                mmr_score = (
                    self.lambda_param * relevance
                    - (1.0 - self.lambda_param) * diversity
                )
                mmr_scores.append((mmr_score, i))

            _, selected_idx = max(mmr_scores, key=lambda x: x[0])
            selected.append(candidates[selected_idx])
            selected_indices.append(selected_idx)

        return selected