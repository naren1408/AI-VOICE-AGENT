import os
import re
import math
from typing import List, Dict, Any, Tuple

# --- CONFIGURATION (Single variable for live explanation) ---
RAG_CHUNK_SIZE_WORDS = 300
RAG_TOP_K = 3

COMPANY_INFO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base", "company_info.txt")


def load_knowledge_base(file_path: str = COMPANY_INFO_PATH) -> str:
    """Load text content from the knowledge base file."""
    if not os.path.exists(file_path):
        return "Company Information: CloudScale AI optimizes enterprise cloud compute."
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int = RAG_CHUNK_SIZE_WORDS) -> List[str]:
    """Split company document by sections or fixed word counts."""
    # Split by markdown headers if available, else by word count
    sections = re.split(r"\n(?=##\s+)", text)
    chunks = []
    for section in sections:
        section = section.strip()
        words = section.split()
        if len(words) <= chunk_size:
            if section:
                chunks.append(section)
        else:
            # Sub-chunk by word count
            for i in range(0, len(words), chunk_size):
                sub_chunk = " ".join(words[i:i + chunk_size])
                chunks.append(sub_chunk)
    return chunks if chunks else [text]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two numerical embedding vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def keyword_overlap_score(query: str, text: str) -> float:
    """Fallback keyword scoring for Demo Mode without Gemini embeddings."""
    q_words = set(re.findall(r"\w+", query.lower()))
    t_words = set(re.findall(r"\w+", text.lower()))
    if not q_words:
        return 0.0
    overlap = len(q_words.intersection(t_words))
    return overlap / len(q_words)


class SimpleRAG:
    """Lightweight in-memory RAG pipeline supporting both embeddings and keyword fallback."""

    def __init__(self, file_path: str = COMPANY_INFO_PATH):
        raw_text = load_knowledge_base(file_path)
        self.chunks = chunk_text(raw_text, RAG_CHUNK_SIZE_WORDS)
        self.embeddings: Dict[int, List[float]] = {}

    def retrieve(self, query: str, top_k: int = RAG_TOP_K, client=None, embed_model: str = "text-embedding-004") -> List[Tuple[str, float]]:
        """Retrieve most relevant chunks using Gemini embeddings when available, or keyword overlap."""
        # Check if Gemini client is active and embeddings can be computed
        if client and hasattr(client, "models"):
            try:
                # Compute query embedding
                q_res = client.models.embed_content(model=embed_model, contents=query)
                q_vec = q_res.embeddings[0].values

                # Ensure chunk embeddings are cached
                for idx, chunk in enumerate(self.chunks):
                    if idx not in self.embeddings:
                        c_res = client.models.embed_content(model=embed_model, contents=chunk)
                        self.embeddings[idx] = c_res.embeddings[0].values

                scores = []
                for idx, chunk in enumerate(self.chunks):
                    sim = cosine_similarity(q_vec, self.embeddings[idx])
                    scores.append((chunk, sim))

                scores.sort(key=lambda x: x[1], reverse=True)
                return scores[:top_k]
            except Exception:
                # Fall through to keyword fallback
                pass

        # Demo mode / rule-based keyword retrieval
        scores = [(chunk, keyword_overlap_score(query, chunk)) for chunk in self.chunks]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# Global RAG singleton
rag_pipeline = SimpleRAG()
