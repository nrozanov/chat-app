import contextlib
import logging
from typing import AsyncIterator

from aiobotocore.session import get_session
from types_aiobotocore_s3.client import S3Client

from config.settings import settings

logger = logging.getLogger("s3")


@contextlib.asynccontextmanager
async def create_client() -> AsyncIterator[S3Client]:
    session = get_session()

    async with session.create_client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    ) as client:
        yield client


async def upload_image_binary(
    *, bucket: str, key: str, data: bytes, content_type: str = "image/jpeg"
) -> None:
    async with create_client() as client:
        logger.info(f"Uploading {key} to {bucket}")
        resp = await client.put_object(
            Bucket=bucket, Key=key, Body=data, ContentType=content_type
        )
        logger.info(f"AWS response:\n{resp}")


async def delete_objects(*, bucket: str, keys: list[str]) -> None:
    async with create_client() as client:
        logger.info(f"Deleting {keys} from {bucket}")
        resp = await client.delete_objects(
            Bucket=bucket, Delete={"Objects": [{"Key": key} for key in keys]}
        )
        logger.info(f"AWS response:\n{resp}")


def get_url(bucket: str, key: str) -> str:
    return f"https://{bucket}.s3.amazonaws.com/{key}"
