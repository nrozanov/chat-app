from common.types import ZipCode
from datetime import date
from typing import TYPE_CHECKING, Optional
from config.settings import settings

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from common.models import TimeStampedMixin
from common.types import BaseModel
from models.user import User

if TYPE_CHECKING:
    from models.chat import Chat


class Customer(BaseModel, TimeStampedMixin, table=True):
    __tablename__ = "customers"

    id: int = Field(default=None, primary_key=True)

    name: str = Field(max_length=100)
    zip_code: ZipCode = Field()
    bio: Optional[str]
    occupation: Optional[str]

    user_id: int = Field(foreign_key="users.id", unique=True)
    user: User = Relationship(back_populates="customer")

    initiated_chats: "Chat" = Relationship(
        back_populates="from_customer",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "primaryjoin": "Customer.id == Chat.from_customer_id",
        },
    )
    got_chats: "Chat" = Relationship(
        back_populates="to_customer",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "primaryjoin": "Customer.id == Chat.to_customer_id",
        },
    )

    def __str__(self) -> str:
        return self.name
