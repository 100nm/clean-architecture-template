from abc import ABC

from pydantic import BaseModel, ConfigDict


class Entity[ID](BaseModel, ABC):
    id: ID

    model_config = ConfigDict(validate_assignment=True)


class AggregateRoot[ID](Entity[ID], ABC): ...


class ValueObject(BaseModel, ABC):
    model_config = ConfigDict(frozen=True)
