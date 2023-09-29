import uuid
from typing import Literal

from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    Field,
    conint,
    conset,
)

from components.alarmeffect import AlarmEffect, InputAlarmEffect


def _build_uuid_string() -> str:
    # Prefix with UUID_ to avoid leading numbers
    # as those might be problematic in JavaScript
    return f"UUID_{uuid.uuid4().hex}"


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
    effect: None | InputAlarmEffect = None
    active: bool | None = None
    weekdays: conset(conint(ge=0, le=6), max_length=7) | None = None  # type: ignore[valid-type]


class Alarm(InputAlarm):
    uid: str = Field(default_factory=_build_uuid_string)

    @classmethod
    def from_input_alarm(cls, input_alarm: InputAlarm) -> "Alarm":
        return cls(**input_alarm.model_dump())

    def edit(self, edited_alarm: EditAlarm) -> Literal[True]:
        if edited_alarm.effect is not None:
            for attr in edited_alarm.effect.model_fields_set:
                setattr(self.effect, attr, getattr(edited_alarm.effect, attr))
        if edited_alarm.active is not None:
            self.active = edited_alarm.active
        if edited_alarm.weekdays is not None:
            self.weekdays = edited_alarm.weekdays
        return True
