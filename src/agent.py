from typing import Callable

try:
    from .store import EmbeddingStore
except ImportError:  # pragma: no cover
    from store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # TODO: store references to store and llm_fn
        pass

    def answer(self, question: str, top_k: int = 3) -> str:
        # TODO: retrieve chunks, build prompt, call llm_fn
        raise NotImplementedError("Implement KnowledgeBaseAgent.answer")


if __name__ == "__main__":
    print("KnowledgeBaseAgent module loaded successfully.")
    print("This script defines KnowledgeBaseAgent but does not execute agent logic by default.")
    print("Import KnowledgeBaseAgent from the package to use it in your application.")
