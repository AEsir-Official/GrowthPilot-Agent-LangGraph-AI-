from __future__ import annotations

import re
from collections import Counter


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


class KeywordVectorStore:
    """A tiny keyword store for first-round local RAG."""

    def __init__(self, documents: list[dict[str, str]]) -> None:
        self.documents = documents
        self.document_terms = [Counter(tokenize(doc.get("content", ""))) for doc in documents]

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        query_terms = Counter(tokenize(query))
        if not query_terms:
            return self.documents[:top_k]

        scored: list[tuple[int, dict[str, str]]] = []
        for doc, terms in zip(self.documents, self.document_terms):
            score = sum(min(count, terms.get(term, 0)) for term, count in query_terms.items())
            scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for score, doc in scored[:top_k] if score > 0] or self.documents[:top_k]
