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
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        context_blocks: list[str] = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or "không rõ"
            doc_id = metadata.get("doc_id") or result.get("id") or "không rõ"
            context_blocks.append(
                f"[Nguồn {index} | doc_id={doc_id} | source={source}]\n"
                f"{result['content']}"
            )

        context = "\n\n".join(context_blocks)
        prompt = (
            "Bạn là trợ lý hỏi đáp dựa trên cơ sở tri thức.\n"
            "Chỉ sử dụng thông tin trong phần NGỮ CẢNH để trả lời. "
            "Không tự bổ sung dữ kiện. Nếu ngữ cảnh không đủ, hãy nói rõ "
            "rằng chưa đủ thông tin. Khi có thể, hãy nêu nhãn nguồn đã sử dụng.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI:\n{question}\n\n"
            "TRẢ LỜI:"
        )
        return self.llm_fn(prompt)
