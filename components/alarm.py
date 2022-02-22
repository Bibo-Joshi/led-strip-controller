import uuid
from typing import Literal

from pydantic import BaseModel, Field, conint  # pylint: disable=no-name-in-module

from components.alarmeffect import AlarmEffect


def _build_uuid_string() -> str:
    return uuid.uuid4().hex


class InputAlarm(BaseModel):
    effect: AlarmEffect
    active: bool = True
    weekdays: list[int] = Field(
        default=[0, 1, 2, 3, 4, 5, 6], item_type=conint(ge=0, le=6), max_items=7, unique_items=True
    )


class EditAlarm(BaseModel):
    effect: None | AlarmEffect = None
    active: bool | None = None
    weekdays: list[int] | None = Field(
        default=None, item_type=conint(ge=0, le=6), max_items=7, unique_items=True
    )


class Alarm(InputAlarm):
    uid: str = Field(default_factory=_build_uuid_string)

    @classmethod
    def from_input_alarm(cls, input_alarm: InputAlarm) -> "Alarm":
        return cls(**input_alarm.dict())

    def edit(self, edited_alarm: EditAlarm) -> Literal[True]:
        if edited_alarm.effect is not None:
            self.effect = edited_alarm.effect
        if edited_alarm.active is not None:
            self.active = edited_alarm.active
        if edited_alarm.weekdays is not None:
            self.weekdays = edited_alarm.weekdays
        return True
