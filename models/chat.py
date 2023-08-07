import sqlalchemy as sa

from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, Optional

from common.models import TimeStampedMixin
from common.types import BaseModel
from models.customer import Customer


class Chat(BaseModel, table=True):
    __tablename__ = "chats"

    id: int = Field(default=None, primary_key=True)

    from_customer_id: int = Field(
        sa_column=sa.Column(
            sa.Integer,
            sa.ForeignKey("customers.id", name="fk_relation_from_customer"),
            default=None,
            nullable=False,
        )
    )
    from_customer: Customer = Relationship(
        back_populates="initiated_chats",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "Customer.id == Chat.from_customer_id",
        },
    )

    to_customer_id: int = Field(
        sa_column=sa.Column(
            sa.Integer,
            sa.ForeignKey("customers.id", name="fk_relation_to_customer"),
            default=None,
            nullable=False,
        )
    )
    to_customer: Customer = Relationship(
        back_populates="got_chats",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "Customer.id == Chat.to_customer_id",
        },
    )

    messages: list["ChatMessage"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
        },
    )


class ChatMessage(BaseModel, TimeStampedMixin, table=True):
    __tablename__ = "chat_messages"

    id: int = Field(default=None, primary_key=True)

    message: str
    is_from_from_customer: bool
    is_viewed: bool = Field(default=False)

    chat_id: int = Field(foreign_key="chats.id")
    chat: Chat = Relationship(back_populates="messages")
