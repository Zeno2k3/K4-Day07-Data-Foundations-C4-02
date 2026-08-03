from __future__ import annotations

from typing import Any, Callable, Dict, List

from chunking import compute_similarity
from models import Document


class EmbeddingStore:
    """A simple in-memory vector store for text documents."""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], List[float]] | None = None,
    ) -> None:
        self._collection_name = collection_name
        self._embedding_fn = embedding_fn or (lambda text: [0.0])
        self._store: List[Dict[str, Any]] = []

    def _make_record(self, doc: Document) -> Dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        metadata = {"doc_id": doc.id}
        if isinstance(doc.metadata, dict):
            metadata.update(doc.metadata)

        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        query_vector = self._embedding_fn(query)
        scored: List[Dict[str, Any]] = []
        for record in records:
            score = compute_similarity(query_vector, record["embedding"])
            scored.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": record["metadata"],
                    "score": float(score),
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: List[Document]) -> None:
        if not docs:
            return

        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self._search_records(query, self._store, top_k)

    def count(self) -> int:
        return len(self._store)

    def clear(self) -> None:
        self._store.clear()

    def delete(self) -> None:
        self.clear()
