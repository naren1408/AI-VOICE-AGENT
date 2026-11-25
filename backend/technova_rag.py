"""
TechNova Solutions — RAG (Retrieval-Augmented Generation)
Uses TF-IDF similarity for lightweight, zero-download knowledge retrieval.
No external API or model download required.
"""
import os
import re
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Path to the TechNova knowledge base document
KB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "knowledge_base", "technova_info.txt"
)

# Chunk size in characters (~500 chars ≈ 1 paragraph)
CHUNK_SIZE = 600


def load_and_chunk(file_path: str = KB_PATH) -> List[str]:
    """Load knowledge base text and split into overlapping chunks."""
    if not os.path.exists(file_path):
        return ["TechNova Solutions provides CRM, ERP, and Analytics software starting at $99/month."]
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Split by double newline (paragraphs), then merge small ones
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) < CHUNK_SIZE:
            current += " " + para
        else:
            if current:
                chunks.append(current.strip())
            current = para
    if current:
        chunks.append(current.strip())
    return chunks


class TechNovaRAG:
    """
    Lightweight TF-IDF RAG pipeline.
    Fits on the knowledge base at startup — no model downloads, no API calls.
    """

    def __init__(self):
        self.chunks = load_and_chunk()
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        # Fit the vectorizer on all knowledge base chunks
        self.chunk_vectors = self.vectorizer.fit_transform(self.chunks)

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Return the top-k most relevant chunks for a query."""
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.chunk_vectors).flatten()
        # Sort by similarity descending
        ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)
        return [(self.chunks[i], round(float(s), 3)) for i, s in ranked[:top_k] if s > 0.01]

    def get_context(self, query: str, top_k: int = 3) -> str:
        """Return retrieved chunks as a single context string for the AI agent."""
        results = self.retrieve(query, top_k)
        if not results:
            return "No specific information found in the TechNova knowledge base for that query."
        return "\n\n---\n\n".join([chunk for chunk, _ in results])

    def add_text(self, new_text: str):
        """Add new content to the knowledge base and re-fit the vectorizer."""
        # Split new text into paragraphs and add directly (load_and_chunk is a module-level function)
        new_chunks = []
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", new_text) if p.strip()]
        current = ""
        for para in paragraphs:
            if len(current) + len(para) < CHUNK_SIZE:
                current += " " + para
            else:
                if current:
                    new_chunks.append(current.strip())
                current = para
        if current:
            new_chunks.append(current.strip())
        self.chunks.extend(new_chunks)
        self.chunk_vectors = self.vectorizer.fit_transform(self.chunks)


# Global singleton — initialized once at app startup
tn_rag = TechNovaRAG()
