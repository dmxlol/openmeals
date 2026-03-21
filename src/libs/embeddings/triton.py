class TritonProvider:
    def __init__(self, url: str, model_name: str, dimension: int) -> None:
        self._url = url
        self._model_name = model_name
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
