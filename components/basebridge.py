import abc

from components.colors import Color


class BaseBridge(abc.ABC):
    @abc.abstractmethod
    async def set_color(self, color: Color) -> None:
        """Sets the color on the RGBW strip."""

    @abc.abstractmethod
    async def initialize(self) -> None:
        ...

    @abc.abstractmethod
    async def shutdown(self) -> None:
        ...

    async def set_off(self) -> None:
        await self.set_color(Color(red=0, green=0, blue=0, white=0))
