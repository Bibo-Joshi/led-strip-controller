import uuid
from typing import Literal

from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    Field,
    conint,
    conset,
)

from components.alarmeffect import AlarmEffect


def _build_uuid_string() -> str:
    return uuid.uuid4().hex


class InputAlarm(BaseModel):
    effect: AlarmEffect
    active: bool = True
    weekdays: conset(conint(ge=0, le=6), max_length=7) = {  # type: ignore[valid-type]
        0,
        1,
        2,
        3,
        4,
        5,
        6,
    }


class EditAlarm(BaseModel):
    effect: None | AlarmEffect = None
    active: bool | None = None
    weekdays: conset(conint(ge=0, le=6), max_length=7) | None = None  # type: ignore[valid-type]


class Alarm(InputAlarm):
    uid: str = Field(default_factory=_build_uuid_string)

    @classmethod
    def from_input_alarm(cls, input_alarm: InputAlarm) -> "Alarm":
        return cls(**input_alarm.model_dump())

    def edit(self, edited_alarm: EditAlarm) -> Literal[True]:
        if edited_alarm.effect is not None:
            self.effect = edited_alarm.effect
        if edited_alarm.active is not None:
            self.active = edited_alarm.active
        if edited_alarm.weekdays is not None:
            self.weekdays = edited_alarm.weekdays
        return True
