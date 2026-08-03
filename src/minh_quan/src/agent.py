from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # Retrieve top-k relevant chunks from the store.
        chunks = self.store.retrieve(question, top_k)

        # Build a prompt with the chunks as context.
        context = "\n\n".join(chunks)
        prompt = f"""
        Dựa vào ngữ cảnh sau, hãy trả lời câu hỏi.

        Ngữ cảnh:
        {context}

        Câu hỏi: {question}
        Trả lời:"""

        # Call the LLM to generate an answer.
        return self.llm_fn(prompt)
