from pathlib import Path
import importlib.util

BASE_DIR = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


chunking = load_module("personal_chunking", BASE_DIR / "chunking.py")
store_module = load_module("personal_store", BASE_DIR / "store.py")
agent_module = load_module("personal_agent", BASE_DIR / "agent.py")


def main() -> None:
    text = (
        "The quick brown fox jumps over the lazy dog. "
        "Machine learning uses data to make predictions. "
        "Python is widely used for NLP and RAG systems."
    )

    chunker = chunking.SentenceChunker(max_sentences_per_chunk=2)
    chunks = chunker.chunk(text)
    print("Chunks:", chunks)

    store = store_module.EmbeddingStore(
        collection_name="personal_store",
        embedding_fn=lambda text: [float(len(text))] * 5,
    )
    docs = [
        type("Doc", (), {"id": f"doc{i}", "content": content, "metadata": {}})
        for i, content in enumerate(chunks, start=1)
    ]
    store.add_documents(docs)

    agent = agent_module.KnowledgeBaseAgent(store=store, llm_fn=lambda prompt: "This is a mocked answer.")
    answer = agent.answer("What topic does this text discuss?", top_k=2)
    print("Answer:\n", answer)


if __name__ == "__main__":
    main()
