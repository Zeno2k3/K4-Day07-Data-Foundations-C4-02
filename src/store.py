from __future__ import annotations

from typing import Any, Callable

try:
    from .chunking import _dot
    from .embeddings import _mock_embed
    from .models import Document
except ImportError:  # pragma: no cover
    from chunking import _dot
    from embeddings import _mock_embed
    from models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # TODO: initialize chromadb client + collection
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # TODO: build a normalized stored record for one document
        raise NotImplementedError("Implement EmbeddingStore._make_record")

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # TODO: run in-memory similarity search over provided records
        raise NotImplementedError("Implement EmbeddingStore._search_records")

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        # TODO: embed each doc and add to store
        raise NotImplementedError("Implement EmbeddingStore.add_documents")

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        # TODO: embed query, compute similarities, return top_k
        raise NotImplementedError("Implement EmbeddingStore.search")

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # TODO
        raise NotImplementedError("Implement EmbeddingStore.get_collection_size")

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # TODO: filter by metadata, then search among filtered chunks
        raise NotImplementedError("Implement EmbeddingStore.search_with_filter")

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        # TODO: remove all stored chunks where metadata['doc_id'] == doc_id
        raise NotImplementedError("Implement EmbeddingStore.delete_document")


if __name__ == "__main__":
    print("EmbeddingStore module loaded successfully.")
    print("This script defines EmbeddingStore but does not execute storage operations by default.")
    print("Import EmbeddingStore from the package to use it in your application.")
