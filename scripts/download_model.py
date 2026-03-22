import sys

from sentence_transformers import SentenceTransformer

from core.config import settings

if __name__ == "__main__":
    model = SentenceTransformer(settings.embedding.model)
    sys.stdout.write(f"Model '{settings.embedding.model}' downloaded to {model.model_card_data.model_id}\n")
    sys.stdout.write(f"Dimension: {model.get_sentence_embedding_dimension()}\n")
