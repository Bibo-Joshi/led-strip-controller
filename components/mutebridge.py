from components.basebridge import BaseBridge
from components.colors import Color


class MuteBridge(BaseBridge):
    """A bridge that doesn't do anything - for testing without an actual LED strip."""

    async def set_color(self, color: Color) -> None:
        """Sets the color on the RGBW strip."""

    async def initialize(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass
