import datetime as dtm
import zoneinfo
from typing import Any

from pydantic import BaseModel, Field, PrivateAttr  # pylint: disable=no-name-in-module

from components.baseeffect import BaseEffect
from components.colors import Color


class InputAlarmEffect(BaseModel):
    start: dtm.time | None = Field(default=None, example="06:00")
    end: dtm.time | None = Field(default=None, example="07:00")
    off: dtm.time | None = Field(default=None, example="08:00")
    timezone: str | None = None
    start_value: int | None = Field(default=None, ge=0, le=255)
    end_value: int | None = Field(default=None, ge=0, le=255)


class AlarmEffect(BaseModel, BaseEffect):
    start: dtm.time = Field(example="06:00")
    end: dtm.time = Field(example="07:00")
    off: dtm.time = Field(example="08:00")
    timezone: str = "Europe/Berlin"
    start_value: int = Field(default=0, ge=0, le=255)
    end_value: int = Field(default=255, ge=0, le=255)

    _start_end: int = PrivateAttr()
    _end_off: int = PrivateAttr()
    _start_off: int = PrivateAttr()
    _value_diff: int = PrivateAttr()

    def __init__(self, **data: Any):
        super().__init__(**data)

        today = dtm.date.today()
        tzinfo = zoneinfo.ZoneInfo(self.timezone)

        dtm_start = dtm.datetime.combine(today, self.start, tzinfo)
        dtm_end = dtm.datetime.combine(today, self.end, tzinfo)
        dtm_off = dtm.datetime.combine(today, self.off, tzinfo)

        if dtm_end <= dtm_start:
            dtm_end += dtm.timedelta(days=1)

        if dtm_off <= dtm_end:
            dtm_off += dtm.timedelta(days=1)

        self._start_end = (dtm_end - dtm_start).seconds
        self._end_off = (dtm_off - dtm_end).seconds
        self._start_off = self._start_end + self._end_off
        self._value_diff = self.end_value - self.start_value

    def edit(self, effect: InputAlarmEffect = None, **kwargs: Any) -> None:
        if not isinstance(effect, AlarmEffect):
            raise TypeError("Can only edit AlarmEffect")
        self.__class__(
            start=effect.start or self.start,
            end=effect.end or self.end,
            off=effect.off or self.off,
            timezone=effect.timezone or self.timezone,
            start_value=effect.start_value or self.start_value,
            end_value=effect.end_value or self.end_value,
        )

    @property
    def duration(self) -> float:
        return self._start_off

    @property
    def repeat(self) -> bool:
        return False

    @property
    def stay_on(self) -> bool:
        return False

    def get_color(self, progress: float) -> Color:
        at_time = progress * self._start_off

        if at_time > self._start_end:
            return Color(white=self.end_value, red=0, green=0, blue=0)

        tran_progress = at_time / self._start_end
        return Color(
            white=int(self.start_value + tran_progress * self._value_diff),
            red=0,
            green=0,
            blue=0,
        )
