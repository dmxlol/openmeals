from sentence_transformers import SentenceTransformer

from core.config import settings

if __name__ == "__main__":
    model = SentenceTransformer(settings.embedding.model)
    print(f"Model '{settings.embedding.model}' downloaded to {model.model_card_data.model_id}")
    print(f"Dimension: {model.get_sentence_embedding_dimension()}")
