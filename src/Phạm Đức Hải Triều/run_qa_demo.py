from __future__ import annotations

from pathlib import Path
from typing import Callable, List

from agent import KnowledgeBaseAgent
from chunking import ChunkingStrategyComparator, SentenceChunker
from embeddings import MockEmbedder
from models import Document
from store import EmbeddingStore


def mock_llm(prompt: str) -> str:
    lines = [line for line in prompt.splitlines() if line.startswith("- (")]
    if not lines:
        return "Answer: I could not find relevant information in the indexed content."

    top_result = lines[0]
    return (
        "Answer: I found relevant context in the indexed chunks.\n"
        f"Top matching chunk:\n{top_result}\n\n"
        "Use that chunk to answer the question as accurately as possible."
    )


def load_sample_text() -> str:
    root = Path(__file__).resolve().parents[2]
    sample_file = root / "data" / "python_intro.txt"
    if sample_file.exists():
        return sample_file.read_text(encoding="utf-8")

    return (
        "Python is a popular programming language. It is easy to learn and widely used for web development, "
        "data analysis, artificial intelligence, and scientific computing. Python supports multiple programming "
        "paradigms, including object-oriented, procedural, and functional programming."
    )


def build_store(text: str) -> EmbeddingStore:
    chunker = SentenceChunker(max_sentences_per_chunk=2)
    chunks = chunker.chunk(text)
    store = EmbeddingStore(embedding_fn=MockEmbedder())
    documents: List[Document] = []

    for index, chunk in enumerate(chunks, start=1):
        documents.append(Document(id=f"chunk-{index}", content=chunk, metadata={"source": "sample"}))

    store.add_documents(documents)
    return store


def print_chunking_report(text: str) -> None:
    comparator = ChunkingStrategyComparator()
    report = comparator.compare(text, chunk_size=200)

    print("Chunking strategy comparison:")
    for strategy, stats in report.items():
        print(f"  {strategy}")
        for key, value in stats.items():
            print(f"    {key}: {value}")
    print()


def run_interactive_demo() -> None:
    text = load_sample_text()
    print("Loaded sample text for Q&A demo.\n")
    print_chunking_report(text)

    store = build_store(text)
    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm)

    print(f"Indexed {store.count()} chunks from sample text.")
    print("Type a question to ask the agent, or 'exit' to quit.\n")

    while True:
        question = input("Question> ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        answer = agent.answer(question, top_k=3)
        print(f"\n{answer}\n")


if __name__ == "__main__":
    run_interactive_demo()
