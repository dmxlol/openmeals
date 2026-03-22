import hashlib
import struct


class MockProvider:
    """Deterministic mock embedding provider for testing.

    Produces reproducible vectors seeded by input text hash,
    so identical inputs always yield the same embedding.
    """

    def __init__(self, dimension: int = 768) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._text_to_vector(text) for text in texts]

    def _text_to_vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        seed = struct.unpack("<I", digest[:4])[0]
        rng = _LCG(seed)
        raw = [rng.next_float() for _ in range(self._dimension)]
        norm = sum(x * x for x in raw) ** 0.5
        return [x / norm for x in raw]


class _LCG:
    """Minimal linear congruential generator (no external deps)."""

    def __init__(self, seed: int) -> None:
        self._state = seed & 0xFFFFFFFF

    def next_float(self) -> float:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return (self._state / 0xFFFFFFFF) * 2 - 1
