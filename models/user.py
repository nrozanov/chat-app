from datetime import datetime, date
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship

from common.models import TimeStampedMixin
from common.types import BaseModel

if TYPE_CHECKING:
    from models.customer import Customer

class User(BaseModel, TimeStampedMixin, table=True):
    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)
    email: str = Field(sa_column_kwargs={"unique": True})
    phone_number: str = Field(sa_column_kwargs={"unique": True})

    last_login: Optional[datetime]

    customer: Optional["Customer"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )

    def __str__(self) -> str:
        return f"User #{self.id} - {self.email} - {self.phone_number}"

    def __repr__(self) -> str:
        return f"<User {self.id}>"
