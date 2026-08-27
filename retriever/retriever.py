# class Retriever:
#     def __init__(self,embedder,vector_store,top_k:int =4,score_threshold : float = None):
#         self.embedder = embedder
#         self.vector_store = vector_store
#         self.top_k = top_k
#         self.score_threshold = score_threshold
#     def retrieve(self, query:str):
#         query_vector = self.embedder.embed_query(query)
#         results = self.vector_store.search(query_vector,top_k=self.top_k)
        
#         if self.score_threshold is not None:
#             results = [
#                 r for r in results
#                 if r["score"]>=self.score_threshold
#             ]

#         return 

# retriever/retriever.py

import numpy as np

class Retriever:
    def __init__(
        self,
        embedder,
        vector_store,
        top_k: int = 2,  #4
        fetch_k: int = 6,  #10
        lambda_param: float = 0.5
    ):
        """
        lambda_param:
        - 1.0 → only relevance
        - 0.0 → only diversity
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.top_k = top_k
        self.fetch_k = fetch_k
        self.lambda_param = lambda_param

    def _cosine_similarity(self, a, b):
        return np.dot(a, b) / (
            np.linalg.norm(a) * np.linalg.norm(b)
        )

    def retrieve(self, query: str):
        query_vector = self.embedder.embed_query(query)

        # Step 1: Get more candidates than needed
        candidates = self.vector_store.search(
            query_vector, top_k=self.fetch_k
        )

        if len(candidates) <= self.top_k:
            return candidates

        # Extract vectors for MMR
        candidate_vectors = [
            self.embedder.embed_query(c["chunk_text"])
            for c in candidates
        ]

        selected = []
        selected_indices = []

        # Step 2: Select the most relevant first
        scores = [c["score"] for c in candidates]
        first_idx = int(np.argmax(scores))
        selected.append(candidates[first_idx])
        selected_indices.append(first_idx)

        # Step 3: MMR selection
        while len(selected) < self.top_k:
            mmr_scores = []

            for i, candidate in enumerate(candidates):
                if i in selected_indices:
                    continue

                relevance = candidate["score"]

                diversity = max(
                    self._cosine_similarity(
                        candidate_vectors[i],
                        candidate_vectors[j]
                    )
                    for j in selected_indices
                )

                mmr_score = (
                    self.lambda_param * relevance
                    - (1 - self.lambda_param) * diversity
                )

                mmr_scores.append((mmr_score, i))

            _, selected_idx = max(mmr_scores, key=lambda x: x[0])
            selected.append(candidates[selected_idx])
            selected_indices.append(selected_idx)

        return selected

