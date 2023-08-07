import datetime
from typing import Optional, Any

from pydantic import BaseSettings, validator
from pydantic.fields import Field

DICT_SETTINGS = {'SENDGRID_SETTINGS': True, 'PINPOINT_SETTINGS': True}

def parse_json_string(json_string, name):
    if isinstance(json_string, dict):
        return json_string

    try:
        value_dict = json.loads(json_string)
    except Exception:
        raise ValueError(f"{name} is not a valid json")
    return value_dict


class Settings(BaseSettings):
    CORS_ALLOWED_ORIGINS: tuple[str, ...]
    SECRET_KEY: str
    DEBUG = False

    SQLALCHEMY_DATABASE_URI = Field(
        "postgresql://test:test@localhost/test",
        env=["DATABASE_URL", "SQLALCHEMY_DATABASE_URI"],
    )
    SQLALCHEMY_ECHO = False

    USER_ACCESS_TOKEN_LIFETIME: datetime.timedelta = datetime.timedelta(hours=24)
    USER_REFRESH_TOKEN_LIFETIME: datetime.timedelta = datetime.timedelta(days=180)

    AWS_ACCESS_KEY_ID = Field("test_aws_access_key_id", env=["AWS_ACCESS_KEY_ID"])
    AWS_SECRET_ACCESS_KEY = Field("test_aws_secret_access_key", env=["AWS_SECRET_ACCESS_KEY"])
    AWS_S3_REGION_NAME = Field("test_aws_s3_region_name", env=["AWS_S3_REGION_NAME"])
    AWS_S3_PHOTOS_BUCKET = Field("test_aws_s3_photos_bucket", env=["AWS_S3_PHOTOS_BUCKET"])

    SENDGRID_SETTINGS: dict[str, Any] = {
        "api_key": "test_key",
        "from_email": "test_from_email",
        "report_template_id": "test_report_id",
        "report_to_emails": ["test_email1", "test_email2"],
    }

    PINPOINT_SETTINGS: dict[str, Any] = {
        "project_id": "test_project_id",
        "origination_number": "test_origination_number",
        "message_type": "test_message_type",
    }

    REDIS_URL = Field(
        "redis://127.0.0.1:6379",
        env=["REDIS_TLS_URL", "REDIS_URL"]
    )

    REDIS_CONNECTIONS_LIMIT = 17

    @validator("SQLALCHEMY_DATABASE_URI")
    def clean_postgres_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql://", 1)
        return value


    class Config:
        env_file = ".env"
        
        @classmethod
        def parse_json_settings(cls, field_name, value: str) -> dict[str, Any]:
            if field_name not in DICT_SETTINGS:
                return value

            return parse_json_string(value, field_name)
