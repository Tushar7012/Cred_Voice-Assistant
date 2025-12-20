import os
import faiss
import json
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(__file__)
INDEX_PATH = os.path.join(BASE_DIR, "faiss.index")
DOCS_PATH = os.path.join(BASE_DIR, "documents.json")

# Load embedding model once
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Lazy-loaded globals
_index = None
_documents = []


def load_index():
    global _index, _documents

    if not os.path.exists(INDEX_PATH) or not os.path.exists(DOCS_PATH):
        print("⚠️ FAISS index or documents not found. RAG disabled.")
        _index = None
        _documents = []
        return

    _index = faiss.read_index(INDEX_PATH)

    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        _documents = json.load(f)


def retrieve_context(query: str, k: int = 3) -> str:
    """
    Retrieve relevant government scheme context.
    Safe even if FAISS is missing.
    """

    global _index, _documents

    if _index is None:
        load_index()

    if _index is None or not _documents:
        return ""

    query_embedding = embedding_model.encode([query])
    distances, indices = _index.search(query_embedding, k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(_documents):
            results.append(_documents[idx])

    return "\n".join(results)
