import asyncio
import logging
from logging.handlers import RotatingFileHandler

from components.basebridge import BaseBridge
from components.controller import Controller
from components.picklepersistence import PicklePersistence

try:
    from components.rpigpiobridge import RPiGPIOBridge

    bridge: BaseBridge = RPiGPIOBridge(rgb_clock=3, rgb_data=2, white_clock=6, white_data=5)
except ImportError:
    from components.mutebridge import MuteBridge

    bridge = MuteBridge()

logging.basicConfig(
    handlers=[RotatingFileHandler("./led-alarm.log", maxBytes=100000, backupCount=10)],
    level=logging.WARNING,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logging.getLogger("apscheduler").setLevel(logging.DEBUG)


async def main() -> None:
    controller = Controller(
        bridge=bridge,
        persistence=PicklePersistence("persistence.pickle"),
    )
    await controller.run(host="0.0.0.0")


if __name__ == "__main__":
    asyncio.run(main())
