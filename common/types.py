from typing import Any, Protocol, TypeVar, Union, ClassVar

from pydantic.types import condecimal, constr
from sqlmodel import SQLModel


class BaseModel(SQLModel):
    id: ClassVar[int | str]

DataDict = dict[str, Any]

Price = condecimal(max_digits=9, decimal_places=2)

JSONType = Union[str, int, float, bool, None, dict[str, Any], list[dict[str, Any]]]

APIResponseType: Any = [int, dict[str, Any]]

ModelType = TypeVar("ModelType", bound=BaseModel)

ZipCode = constr(min_length=5, max_length=5, regex="^\d+$")


class Dataclass(Protocol):
    __dataclass_fields__: dict[str, Any]
