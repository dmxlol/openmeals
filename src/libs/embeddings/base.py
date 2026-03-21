import typing as t


class EmbeddingProvider(t.Protocol):
    @property
    def dimension(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...
