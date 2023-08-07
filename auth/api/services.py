import boto3
import contextlib
import logging

from config.db import redis_manager
from botocore.exceptions import ClientError
from random import randint
from typing import AsyncIterator

from aiobotocore.session import get_session
from types_aiobotocore_s3.client import S3Client

from config.settings import settings

pinpoint_settings = settings.PINPOINT_SETTINGS

logger = logging.getLogger("sendgrid")

@contextlib.asynccontextmanager
async def create_client() -> AsyncIterator[S3Client]:
    session = get_session()

    async with session.create_client(
        "pinpoint",
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    ) as client:
        yield client


async def send_code(phone_number: str, code_len: int = 6, send_message=True) -> str:
    code = ''.join(
        ["{}".format(randint(0, 9)) for num in range(0, code_len)]
    )
    
    await redis_manager.set_cache_value(phone_number, code)
    
    if not send_message:
        return code

    message = f'Your verification code is {code}'

    async with create_client() as client:
        try:
            response = await client.send_messages(
                ApplicationId=pinpoint_settings["project_id"],
                MessageRequest={
                    'Addresses': {phone_number: {'ChannelType': 'SMS'}},
                    'MessageConfiguration': {
                        'SMSMessage': {
                            'Body': message,
                            'MessageType': pinpoint_settings["message_type"],
                            'OriginationNumber': pinpoint_settings["origination_number"]
                        }
                    }
                }
            )
        except ClientError as e:
            logger.exception(f"Couldn't send message: {str(e)}")
        else:
            logger.info(
                f"Code to {phone_number} sending stating: {response['MessageResponse']['Result'][phone_number]['DeliveryStatus']}"
            )
    return code


async def get_code(phone_number: str) -> str | None:
    code = await redis_manager.get_cache_value(phone_number)
    if code:
        code = code.decode('utf-8')

    return code
