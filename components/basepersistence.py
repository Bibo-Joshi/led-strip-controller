import abc

from components.alarm import Alarm
from components.colors import Color


class BasePersistence(abc.ABC):
    def __init__(self, update_interval: float = 1):
        self.update_interval = update_interval

    @abc.abstractmethod
    async def flush(self) -> None: ...

    @abc.abstractmethod
    async def get_status(self) -> bool: ...

    @abc.abstractmethod
    async def get_color(self) -> Color: ...

    @abc.abstractmethod
    async def get_alarms(self) -> dict[str, Alarm]: ...

    @abc.abstractmethod
    async def update_status(self, status: bool) -> None: ...

    @abc.abstractmethod
    async def update_color(self, color: Color) -> None: ...

    @abc.abstractmethod
    async def update_alarm(self, alarm: Alarm) -> None: ...

    @abc.abstractmethod
    async def drop_alarm(self, alarm: Alarm | str) -> None: ...
