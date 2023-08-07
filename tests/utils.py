import contextlib
import datetime
from typing import Any, Optional

from config.settings import settings


def serialize_datetime(value: Optional[datetime.datetime]) -> Optional[str]:
    if not value:
        return None
    return value.isoformat()


@contextlib.contextmanager
def override_settings(**kwargs):
    original_vals: dict[str, Any] = {}

    for key, val in kwargs.items():
        original_vals[key] = getattr(settings, key)
        setattr(settings, key, val)

    try:
        yield
    finally:
        for key, val in original_vals.items():
            setattr(settings, key, val)
