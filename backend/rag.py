"""
ElectroMart India — RAG (Retrieval-Augmented Generation)
Loads all 8 documents from knowledge_base/, chunks them, and retrieves top relevant context
using scikit-learn TF-IDF and NumPy cosine similarity. Zero model downloads, zero API key required.
"""
import os
import re
from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")
CHUNK_SIZE_CHARS = 500


def load_all_chunks(kb_dir: str = KB_DIR) -> List[str]:
    """Read all knowledge base text files and split into coherent chunks."""
    chunks = []
    if not os.path.exists(kb_dir):
        return ["ElectroMart India is a leading electronics retailer offering laptops, smartphones, tablets, and accessories."]

    for fname in sorted(os.listdir(kb_dir)):
        if fname.endswith(".txt"):
            fpath = os.path.join(kb_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                # Split by double newlines into paragraphs
                paras = [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]
                current = ""
                for p in paras:
                    if len(current) + len(p) < CHUNK_SIZE_CHARS:
                        current += "\n" + p if current else p
                    else:
                        if current:
                            chunks.append(f"[{fname}] {current.strip()}")
                        current = p
                if current:
                    chunks.append(f"[{fname}] {current.strip()}")
            except Exception as e:
                print(f"Error reading {fname}: {e}")

    return chunks or ["ElectroMart India product catalog and policy information."]


class ElectroMartRAG:
    """Lightweight in-memory RAG pipeline using TF-IDF and NumPy cosine similarity."""

    def __init__(self):
        self.chunks = load_all_chunks()
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.chunk_vectors = self.vectorizer.fit_transform(self.chunks)

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Retrieve top_k chunks relevant to query using cosine similarity."""
        if not self.chunks or not query.strip():
            return []

        q_vec = self.vectorizer.transform([query])
        # Compute cosine similarity with NumPy
        sims = (q_vec * self.chunk_vectors.T).toarray().flatten()

        ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in ranked[:top_k]:
            if score > 0.01:
                results.append((self.chunks[idx], round(float(score), 3)))

        return results

    def get_context(self, query: str, top_k: int = 3) -> str:
        """Return retrieved chunks combined as context string for the AI agent."""
        res = self.retrieve(query, top_k)
        if not res:
            return "No specific information found in ElectroMart knowledge base for that query."
        return "\n\n---\n\n".join([chunk for chunk, _ in res])


# Global RAG singleton
rag_engine = ElectroMartRAG()
