from datetime import datetime
from pydantic import BaseModel, validator, Field
from typing import Any, Optional


class ChatMessageSchema(BaseModel):
    id: int
    message: str
    from_customer_id: int
    to_customer_id: int
    created_at: datetime
    is_viewed: bool


class SendMessageSchema(BaseModel):
	message: str


class ChatSchema(BaseModel):
    id: int
    name: str
    with_customer_id: int
    last_message: Optional[str]
    last_message_sender_id: Optional[int]
    last_message_created_at: Optional[datetime]
    viewed_all_messages: Optional[bool]
