import hashlib
import math
from typing import List


class MockEmbedder:
    """Deterministic embedding backend suitable for local testing."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def __call__(self, text: str) -> List[float]:
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        seed = int(digest, 16)
        vector: List[float] = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]


_mock_embed = MockEmbedder()
