from typing import Callable, List

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """A retrieval-augmented generation agent that uses a vector store."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self._llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if not question or not question.strip():
            return ""

        results = self.store.search(question, top_k=top_k)
        context_lines: List[str] = []
        for record in results:
            content = record.get("content", "")
            score = record.get("score", 0.0)
            context_lines.append(f"- ({score:.4f}) {content}")

        context_text = "\n".join(context_lines) if context_lines else "No relevant context was found."
        prompt = (
            "You are a helpful assistant. Answer the question using the context below.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question.strip()}\n"
            "Answer:"
        )

        return self._llm_fn(prompt)
