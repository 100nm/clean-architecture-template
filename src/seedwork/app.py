from abc import ABC

from pydantic import BaseModel, ConfigDict


class DTO(BaseModel, ABC):
    model_config = ConfigDict(frozen=True)


class Message(DTO, ABC): ...


class Command(Message, ABC): ...


class Event(Message, ABC): ...


class Query(Message, ABC): ...
