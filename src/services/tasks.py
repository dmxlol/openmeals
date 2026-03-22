import hashlib
import logging
import typing as t
from io import BytesIO

from PIL import Image

from core.celery import celery_app
from core.config import settings
from libs.embeddings import get_embedding_provider
from libs.s3 import delete_file, download_file, upload_file

if t.TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import Bucket


@celery_app.task
def embed_text(text: str) -> list[float]:
    provider = get_embedding_provider(settings)
    [embedding] = provider.embed([text])
    return embedding


def process_image_file(bucket: "Bucket", raw_key: str, entity_type: str, entity_id: str) -> str:
    raw_bytes = download_file(bucket, raw_key)
    logging.info("Downloaded object from %s at %s (%d bytes)", bucket, raw_key, len(raw_bytes))
    try:
        img = Image.open(BytesIO(raw_bytes))
    except Image.UnidentifiedImageError as e:
        delete_file(bucket, raw_key)
        msg = f"Cannot identify image at {raw_key} ({len(raw_bytes)} bytes) — raw file deleted"
        raise ValueError(msg) from e
    max_dim = settings.s3.image_max_dimension
    img.thumbnail((max_dim, max_dim))
    buffer = BytesIO()
    img.save(buffer, format="WEBP", quality=settings.s3.image_webp_quality)
    processed_bytes = buffer.getvalue()

    content_hash = hashlib.sha256(processed_bytes).hexdigest()[:16]
    processed_key = f"{entity_type}/{entity_id}/{content_hash}.webp"

    cache_max_age = settings.s3.image_cache_max_age
    upload_file(
        bucket=bucket,
        key=processed_key,
        body=processed_bytes,
        content_type="image/webp",
        cache_control=f"public, max-age={cache_max_age}, immutable",
    )

    delete_file(bucket, raw_key)
    return processed_key
