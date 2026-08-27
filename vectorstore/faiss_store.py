import faiss
import numpy as np
import pickle
import os

class FAISSVectorStore:
    def __init__(self,vector_dim: int , index_path:str = "faiss.index"):
        self.vector_dim = vector_dim
        self.index_path = index_path
        self.index = faiss.IndexFlatIP(vector_dim)
        self.metadata_store = []
    
    def _normalize(self,vectors):
        faiss.normalize_L2(vectors)
        return vectors
    
    def add_embeddings(self,embedded_chunks:list):
        vectors = np.array([item["vector"] for item in embedded_chunks]).astype("float32")
        vectors = self._normalize(vectors)

        self.index.add(vectors)

        for item in embedded_chunks:
            self.metadata_store.append({
                "chunk_text":item["chunk_text"],
                "metadata":item["metadata"]
            })

    def save(self):
        faiss.write_index(self.index,self.index_path)
        with open(self.index_path + ".meta", "wb") as f:
            pickle.dump(self.metadata_store,f)
    def load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.index_path + ".meta","rb") as f:
                self.metadata_store = pickle.load(f)
        
    def search(self, query_vector, top_k : int = 4):
        query_vector = np.array([query_vector]).astype("float32")
        query_vector = self._normalize(query_vector)

        scores, indices = self.index.search(query_vector,top_k)
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:
                continue

            results.append({
                "chunk_text": self.metadata_store[idx]["chunk_text"],
                "metadata": self.metadata_store[idx]["metadata"],
                "score": float(score)
            })

        return results
