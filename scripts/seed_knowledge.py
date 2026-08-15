"""Rebuild the RAG knowledge index from the knowledge/ folder.

Usage: python scripts/seed_knowledge.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings  # noqa: E402
from app.rag import knowledge_index  # noqa: E402

print(f"[*] Knowledge dir: {settings.knowledge_dir}")
ok = knowledge_index.build(force=True)
if not ok:
    print("[!] No markdown files found under knowledge/. Add some and retry.")
    sys.exit(1)
print(f"[+] Index ready: {len(knowledge_index.documents)} documents "
      f"({knowledge_index.mode} store)")

q = input("Try a test query (or Enter to skip): ").strip()
if q:
    for hit in knowledge_index.search(q):
        print(f"  - {hit['source']}  (score {hit.get('score', 'n/a'):.3f})" if 'score' in hit
              else f"  - {hit['source']}")
