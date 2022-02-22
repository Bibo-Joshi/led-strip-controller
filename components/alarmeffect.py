import datetime as dtm
import zoneinfo
from typing import Any

from pydantic import BaseModel, Field, PrivateAttr  # pylint: disable=no-name-in-module

from components.baseeffect import BaseEffect
from components.colors import Color


class AlarmEffect(BaseModel, BaseEffect):
    start: dtm.time
    end: dtm.time
    off: dtm.time
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
        if dtm_end <= dtm_start or dtm_off <= dtm_end:
            raise ValueError("Ordering of times is invalid!")

        self._start_end = (dtm_end - dtm_start).seconds
        self._end_off = (dtm_off - dtm_end).seconds
        self._start_off = self._start_end + self._end_off
        self._value_diff = self.end_value - self.start_value

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
