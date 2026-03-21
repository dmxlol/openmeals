from sentence_transformers import SentenceTransformer


class SentenceTransformerProvider:
    def __init__(self, model_name: str) -> None:
        self._model = SentenceTransformer(model_name)

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
