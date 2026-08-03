import re
from typing import Dict, List

import numpy as np


class FixedSizeChunker:
    """Split text into fixed-size chunks with optional overlap."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = max(1, chunk_size)
        self.overlap = max(0, min(overlap, self.chunk_size - 1))

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []

        cleaned = text.strip()
        if len(cleaned) <= self.chunk_size:
            return [cleaned]

        step = self.chunk_size - self.overlap
        chunks: List[str] = []
        for start in range(0, len(cleaned), step):
            chunks.append(cleaned[start : start + self.chunk_size])
            if start + self.chunk_size >= len(cleaned):
                break
        return chunks


class SentenceChunker:
    """Split text into sentence-based chunks using punctuation boundaries."""

    ABBREVIATIONS = {
        "mr.", "mrs.", "ms.", "dr.", "jr.", "sr.", "st.", "gov.", "prof.",
        "capt.", "lt.", "col.", "sgt.", "rev.", "hon.", "messrs.", "mme.",
        "mlle.", "mx.", "tp.", "etc.", "e.g.", "i.e.", "vs.",
    }

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def _split_sentences(self, text: str) -> List[str]:
        candidate_sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences: List[str] = []

        for candidate in candidate_sentences:
            stripped = candidate.strip()
            if not stripped:
                continue

            if sentences:
                previous = sentences[-1]
                last_word = previous.split()[-1].lower() if previous.split() else ""
                if last_word in self.ABBREVIATIONS:
                    sentences[-1] = previous + " " + stripped
                    continue

            sentences.append(stripped)

        return sentences

    def chunk(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        normalized = re.sub(r"\s+", " ", text.strip())
        sentences = self._split_sentences(normalized)

        chunks: List[str] = []
        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[start : start + self.max_sentences_per_chunk]).strip()
            if chunk:
                chunks.append(chunk)

        return chunks


class RecursiveChunker:
    """Recursively split text using separators in priority order."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: List[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = list(separators) if separators is not None else self.DEFAULT_SEPARATORS.copy()
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        cleaned_text = text.strip()
        raw_chunks = self._split(cleaned_text, self.separators)
        return [chunk.strip() for chunk in raw_chunks if chunk.strip()]

    def _split(self, current_text: str, remaining_separators: List[str]) -> List[str]:
        if not current_text:
            return []

        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if separator == "":
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        if separator not in current_text:
            return self._split(current_text, next_separators)

        pieces = current_text.split(separator)
        chunks: List[str] = []
        current_piece: List[str] = []

        for piece in pieces:
            candidate = separator.join(current_piece + [piece]) if current_piece else piece
            if len(candidate) <= self.chunk_size:
                current_piece.append(piece)
                continue

            if current_piece:
                chunks.append(separator.join(current_piece))
                current_piece = []

            if len(piece) > self.chunk_size:
                chunks.extend(self._split(piece, next_separators))
            else:
                current_piece = [piece]

        if current_piece:
            chunks.append(separator.join(current_piece))

        return chunks


def compute_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two numeric vectors."""
    a = np.asarray(vec_a, dtype=float)
    b = np.asarray(vec_b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("Vectors must have the same dimensions")

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


class ChunkingStrategyComparator:
    """Compare built-in chunking strategies for a sample text."""

    def compare(self, text: str, chunk_size: int = 200) -> Dict[str, Dict[str, float]]:
        fixed = FixedSizeChunker(chunk_size=chunk_size).chunk(text)
        sentence = SentenceChunker().chunk(text)
        recursive = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def compute_stats(chunks: List[str]) -> Dict[str, float]:
            sizes = [len(chunk) for chunk in chunks]
            count = len(sizes)
            return {
                "count": float(count),
                "avg_length": float(sum(sizes) / count) if count else 0.0,
                "max_length": float(max(sizes)) if count else 0.0,
                "min_length": float(min(sizes)) if count else 0.0,
                "chunks": chunks,
            }

        return {
            "fixed_size": compute_stats(fixed),
            "by_sentences": compute_stats(sentence),
            "recursive": compute_stats(recursive),
        }


if __name__ == "__main__":
    sample_text = (
        "The quick brown fox jumps over the lazy dog. "
        "A fox is a small omnivorous mammal. "
        "Dogs are loyal companions and working animals. "
        "Brown bears live in forests across the northern hemisphere. "
        "Jumping is a physical activity that requires leg strength."
    )

    print("Sample text:", sample_text)

    fixed_chunker = FixedSizeChunker(chunk_size=50, overlap=5)
    print("FixedSizeChunker chunks:", fixed_chunker.chunk(sample_text))

    sentence_chunker = SentenceChunker(max_sentences_per_chunk=2)
    print("SentenceChunker chunks:", sentence_chunker.chunk(sample_text))

    recursive_chunker = RecursiveChunker(chunk_size=60)
    print("RecursiveChunker chunks:", recursive_chunker.chunk(sample_text))

    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    print("Cosine similarity of a and b:", compute_similarity(a, b))

    comparator = ChunkingStrategyComparator()
    print("Chunking strategy comparison:", comparator.compare(sample_text, chunk_size=60))
