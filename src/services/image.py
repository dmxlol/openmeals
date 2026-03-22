import typing as t
from enum import StrEnum

from fastapi import Depends
from ulid import ULID

from core.config import settings
from libs.s3 import ext_from_content_type, generate_presigned_post
from libs.types import get_s3_bucket_dependency


class ImageContentType(StrEnum):
    JPEG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"
    GIF = "image/gif"


if t.TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import Bucket


class UploadResultDto(t.NamedTuple):
    upload_url: str
    upload_fields: dict
    raw_key: str


class ImageManager:
    def __init__(self, bucket: "Bucket") -> None:
        self.bucket = bucket

    def generate_upload_url(self, entity_type: str, entity_id: str, content_type: str) -> UploadResultDto:
        raw_key = f"raw/{entity_type}/{entity_id}/{ULID()}.{ext_from_content_type(content_type)}"
        upload_url, upload_fields = generate_presigned_post(
            bucket=self.bucket,
            key=raw_key,
            content_type=content_type,
            max_bytes=settings.s3.image_max_upload_bytes,
            expiry=settings.s3.presigned_url_expiry_seconds,
        )
        return UploadResultDto(upload_url=upload_url, upload_fields=upload_fields, raw_key=raw_key)


def get_image_manager(bucket: "Bucket" = Depends(get_s3_bucket_dependency)) -> ImageManager:
    return ImageManager(bucket)


ImageManagerDependency = t.Annotated[ImageManager, Depends(get_image_manager)]
