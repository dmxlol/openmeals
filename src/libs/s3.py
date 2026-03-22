import logging
import typing as t
from functools import lru_cache

import boto3

if t.TYPE_CHECKING:
    from mypy_boto3_s3 import S3ServiceResource
    from mypy_boto3_s3.service_resource import Bucket

CONTENT_TYPE_EXT: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


@lru_cache(maxsize=1)
def get_s3_resource() -> "S3ServiceResource":
    return boto3.resource("s3")


def ext_from_content_type(content_type: str) -> str:
    ext = CONTENT_TYPE_EXT.get(content_type)
    if ext is None:
        msg = f"Unsupported content type: {content_type}"
        raise ValueError(msg)
    return ext


def generate_presigned_post(
    bucket: "Bucket",
    key: str,
    content_type: str,
    max_bytes: int,
    expiry: int,
) -> tuple[str, dict]:
    result = bucket.meta.client.generate_presigned_post(
        Bucket=bucket.name,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, max_bytes],
        ],
        ExpiresIn=expiry,
    )
    return result["url"], result["fields"]


def download_file(bucket: "Bucket", key: str) -> bytes:
    response = bucket.Object(key).get()
    b = response["Body"].read()
    logging.info(f"File {key} downloaded from bucket {bucket.name}")
    return b


def upload_file(
    bucket: "Bucket",
    key: str,
    body: bytes,
    content_type: str,
    cache_control: str | None = None,
) -> None:
    params: dict[str, t.Any] = {
        "Key": key,
        "Body": body,
        "ContentType": content_type,
    }
    if cache_control:
        params["CacheControl"] = cache_control
    bucket.put_object(**params)
    logging.info(f"File {key} uploaded to bucket {bucket.name}")


def delete_file(bucket: "Bucket", key: str) -> None:
    bucket.Object(key).delete()
    logging.info(f"File {key} deleted from bucket {bucket.name}")
