"""RAG knowledge base - Note 5 & Note 6.

Pipeline: question -> embedding -> vector search -> top documents -> model answer.

Uses ChromaDB when installed, otherwise a built-in lightweight vector store
(Ollama embeddings + numpy cosine similarity). Both keep everything local.
"""
from __future__ import annotations

import json
import os
import re
from hashlib import blake2b
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from .config import settings
from .llm import OllamaClient, OllamaError

try:
    import chromadb  # optional, used when installed
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False


def _hash_embed(text: str, dim: int = 384) -> List[float]:
    """Deterministic hashing-based embedding (no external model required).

    Produces a fixed-dimension unit vector from word + character-bigram
    hashes so the lightweight store works even when Ollama embeddings are
    unavailable (e.g. serverless production)."""
    vec = [0.0] * dim
    tokens = re.findall(r"[a-z0-9]{2,}", text.lower())
    features = list(tokens)
    features += ["".join(ch) for ch in zip(text.lower(), text.lower()[1:])]
    for tok in features:
        h = blake2b(tok.encode(), digest_size=8).digest()
        idx = int.from_bytes(h[:4], "little") % dim
        sign = 1.0 if h[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


class KnowledgeIndex:
    def __init__(self):
        self.documents: List[Tuple[str, str, str]] = []  # (id, text, source)
        self.vectors: Optional[np.ndarray] = None
        self.built = False
        self.mode = "none"
        self.ollama = OllamaClient()
        self._cache_file = Path(settings.chroma_dir) / "index.json"

    # ------------------------------------------------------------ build
    def build(self, force: bool = False) -> bool:
        """Load/refresh the index from the knowledge/ folder."""
        self.documents = []
        root = Path(settings.knowledge_dir)
        if not root.exists():
            return False

        for path in sorted(root.rglob("*.md")):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").strip()
            except Exception:
                continue
            if not text:
                continue
            self.documents.append((path.stem, text, str(path)))

        if not self.documents:
            return False

        self.mode = self._try_chroma() if HAS_CHROMA else "lightweight"
        if self.mode == "lightweight":
            self._build_vectors(force)
        self.built = True
        return True

    def _build_vectors(self, force: bool = False) -> None:
        if self._cache_file.exists() and not force:
            try:
                data = json.loads(self._cache_file.read_text())
                if data.get("count") == len(self.documents):
                    self.vectors = np.array(data["vectors"])
                    return
            except Exception:
                pass
        try:
            vecs = self.ollama.embed([d[1] for d in self.documents])
            self.vectors = np.array(vecs, dtype="float32")
            self.embed_engine = "ollama"
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            self._cache_file.write_text(json.dumps({
                "count": len(self.documents),
                "vectors": self.vectors.tolist(),
            }))
        except (OllamaError, Exception) as e:
            # No Ollama embeddings available -> deterministic hash embeddings
            self.vectors = np.array(
                [_hash_embed(d[1]) for d in self.documents], dtype="float32"
            )
            self.embed_engine = "hash"
            self.mode = "lightweight"

    def _try_chroma(self) -> str:
        try:
            client = chromadb.PersistentClient(path=settings.chroma_dir)
            col = client.get_or_create_collection("knowledge")
            col.upsert(
                ids=[d[0] for d in self.documents],
                documents=[d[1] for d in self.documents],
                metadatas=[{"source": d[2]} for d in self.documents],
            )
            self._chroma_col = col
            return "chroma"
        except Exception:
            return "lightweight"

    # ------------------------------------------------------------ search
    def search(self, query: str, top_k: Optional[int] = None) -> List[dict]:
        k = top_k or settings.rag_top_k
        if not self.built:
            self.build()
        if not self.documents:
            return []
        if self.mode == "chroma":
            try:
                res = self._chroma_col.query(query_texts=[query], n_results=k)
                ids = res["ids"][0]
                docs = res["documents"][0]
                metas = res["metadatas"][0]
                return [
                    {"text": d, "source": m.get("source", "")}
                    for d, m in zip(docs, metas)
                ]
            except Exception:
                pass
        if self.vectors is not None:
            try:
                qv = self._query_embed(query)
                sims = self.vectors @ qv / (
                    np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(qv) + 1e-9
                )
                idx = np.argsort(sims)[::-1][:k]
                return [
                    {"text": self.documents[i][1], "source": self.documents[i][2],
                     "score": float(sims[i])}
                    for i in idx
                ]
            except Exception:
                pass
        # keyword fallback
        terms = query.lower().split()
        scored = []
        for doc_id, text, src in self.documents:
            score = sum(1 for t in terms if t in text.lower())
            if score:
                scored.append((score, text, src))
        scored.sort(key=lambda x: -x[0])
        return [{"text": t, "source": s} for _, t, s in scored[:k]]

    def _query_embed(self, query: str) -> np.ndarray:
        """Embed the query using the same engine as the index."""
        if getattr(self, "embed_engine", None) == "ollama":
            return np.array(self.ollama.embed([query])[0], dtype="float32")
        return np.array(_hash_embed(query), dtype="float32")

    def context_for(self, query: str, top_k: Optional[int] = None) -> Tuple[str, bool]:
        """Return (context_block, used_rag)."""
        hits = self.search(query, top_k)
        if not hits:
            return "", False
        block = "\n\n".join(
            f"[Source: {h['source']}]\n{h['text'][:2500]}" for h in hits
        )
        return block, True


knowledge_index = KnowledgeIndex()
