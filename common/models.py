from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from sqlmodel import Field


class TimeStampedMixin(BaseModel):
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )
