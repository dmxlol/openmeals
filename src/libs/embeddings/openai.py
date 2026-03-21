class OpenAIProvider:
    def __init__(self, api_key: str, model_name: str, dimension: int) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
