from __future__ import annotations

import os
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


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
        self._client = None
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            persist_dir = os.getenv("CHROMA_PERSIST_DIR")
            if persist_dir:
                self._client = chromadb.PersistentClient(path=persist_dir)
            else:
                self._client = chromadb.EphemeralClient()
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._client = None
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": f"{doc.id}::{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": [float(value) for value in self._embedding_fn(doc.content)],
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        query_embedding = [float(value) for value in self._embedding_fn(query)]
        results: list[dict[str, Any]] = []
        for record in records:
            embedding = record["embedding"]
            if len(query_embedding) != len(embedding):
                raise ValueError("Query and document embeddings must have the same dimensions")
            results.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": dict(record["metadata"]),
                    "score": _dot(query_embedding, embedding),
                }
            )

        results.sort(key=lambda result: result["score"], reverse=True)
        return results[:top_k]

    def _search_chroma(
        self,
        query: str,
        top_k: int,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        if top_k <= 0 or self._collection is None or self._collection.count() == 0:
            return []

        query_embedding = [float(value) for value in self._embedding_fn(query)]
        query_args: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, self._collection.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if metadata_filter:
            if len(metadata_filter) == 1:
                query_args["where"] = dict(metadata_filter)
            else:
                query_args["where"] = {
                    "$and": [{key: value} for key, value in metadata_filter.items()]
                }

        raw_results = self._collection.query(**query_args)
        ids = (raw_results.get("ids") or [[]])[0]
        documents = (raw_results.get("documents") or [[]])[0]
        metadatas = (raw_results.get("metadatas") or [[]])[0]
        distances = (raw_results.get("distances") or [[]])[0]
        return [
            {
                "id": record_id,
                "content": content,
                "metadata": dict(metadata or {}),
                "score": 1.0 - float(distance),
            }
            for record_id, content, metadata, distance in zip(
                ids, documents, metadatas, distances
            )
        ]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[record["id"] for record in records],
                    documents=[record["content"] for record in records],
                    embeddings=[record["embedding"] for record in records],
                    metadatas=[record["metadata"] for record in records],
                )
            except Exception:
                self._use_chroma = False
                self._client = None
                self._collection = None

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma:
            try:
                return self._search_chroma(query, top_k)
            except Exception:
                self._use_chroma = False
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            try:
                return int(self._collection.count())
            except Exception:
                self._use_chroma = False
        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)
        if self._use_chroma:
            try:
                return self._search_chroma(query, top_k, metadata_filter)
            except Exception:
                self._use_chroma = False

        filtered_records = [
            record
            for record in self._store
            if all(
                record["metadata"].get(key) == value
                for key, value in metadata_filter.items()
            )
        ]
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        matching_ids = [
            record["id"]
            for record in self._store
            if record["metadata"].get("doc_id") == doc_id
        ]
        if not matching_ids:
            return False

        matching_id_set = set(matching_ids)
        self._store = [
            record for record in self._store if record["id"] not in matching_id_set
        ]
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=matching_ids)
            except Exception:
                self._use_chroma = False
        return True
