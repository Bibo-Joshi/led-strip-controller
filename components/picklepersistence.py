import copy
import pathlib
import pickle

from components.alarm import Alarm
from components.basepersistence import BasePersistence
from components.colors import Color


class PicklePersistence(BasePersistence):
    def __init__(self, file_path: pathlib.Path | str, update_interval: float = 1):
        super().__init__(update_interval=update_interval)
        self.file_path = pathlib.Path(file_path)
        self._status: bool = False
        self._color: Color = Color(white=0, red=0, green=0, blue=0)
        self._alarms: dict[str, Alarm] = {}
        self._loaded = False

    async def _dump(self) -> None:
        data = {"status": self._status, "color": self._color, "alarms": self._alarms}
        self.file_path.write_bytes(pickle.dumps(data))

    async def _load(self) -> None:
        if self.file_path.is_file():
            data = pickle.loads(self.file_path.read_bytes())
            self._status = data["status"]
            self._color = data["color"]
            self._alarms = data["alarms"]
            self._status = data["status"]

        self._loaded = True

    async def flush(self) -> None:
        await self._dump()

    async def get_status(self) -> bool:
        if not self._loaded:
            await self._load()
        return self._status

    async def get_color(self) -> Color:
        if not self._loaded:
            await self._load()
        return copy.deepcopy(self._color)

    async def get_alarms(self) -> dict[str, Alarm]:
        if not self._loaded:
            await self._load()
        return copy.deepcopy(self._alarms)

    async def update_status(self, status: bool) -> None:
        self._status = status
        await self._dump()

    async def update_color(self, color: Color) -> None:
        self._color = color
        await self._dump()

    async def update_alarm(self, alarm: Alarm) -> None:
        self._alarms[alarm.uid] = alarm
        await self._dump()

    async def drop_alarm(self, alarm: Alarm | str) -> None:
        self._alarms.pop(alarm.uid if isinstance(alarm, Alarm) else alarm, None)
        await self._dump()
