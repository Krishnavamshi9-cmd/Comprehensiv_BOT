from typing import List, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.index = None  # type: ignore
        self.texts: List[str] = []

    def _embed(self, texts: List[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return embeddings.astype('float32')

    def build_index(self, chunks: List[str]) -> None:
        if not chunks:
            raise ValueError("No chunks provided to build the index.")
        self.texts = chunks
        vectors = self._embed(chunks)
        dim = vectors.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(vectors)

    def query(self, q: str, k: int = 8) -> List[Tuple[str, float]]:
        if self.index is None or not self.texts:
            raise ValueError("Index not built. Call build_index() first.")
        qv = self._embed([q])
        scores, indices = self.index.search(qv, min(k, len(self.texts)))
        results: List[Tuple[str, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:
                continue
            results.append((self.texts[int(idx)], float(score)))
        return results
