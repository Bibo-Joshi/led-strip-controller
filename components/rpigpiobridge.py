from components.basebridge import BaseBridge
from components.colors import Color

try:
    import RPi.GPIO as GPIO  # pylint: disable=consider-using-from-import
except ImportError as exc:
    raise ImportError("Can't use RPiGPIOBridge if RPi.GPIO is not installed!") from exc


class _P9813:
    def __init__(self, clock: int, data: int) -> None:
        GPIO.setwarnings(True)
        GPIO.setmode(GPIO.BCM)
        self.__clock = clock
        self.__data = data
        GPIO.setup(self.__clock, GPIO.OUT)
        GPIO.setup(self.__data, GPIO.OUT)

    def __send_clock(self) -> None:
        GPIO.output(self.__clock, False)
        GPIO.output(self.__clock, True)

    def __send_32_zero(self) -> None:
        for _ in range(32):
            GPIO.output(self.__data, False)
            self.__send_clock()

    def __send_data(self, data: int) -> None:
        self.__send_32_zero()
        for _ in range(32):
            if (data & 0x80000000) != 0:
                GPIO.output(self.__data, True)
            else:
                GPIO.output(self.__data, False)
            data <<= 1
            self.__send_clock()
        self.__send_32_zero()

    @staticmethod
    def __get_code(data: int) -> int:
        tmp = 0
        if (data & 0x80) == 0:
            tmp |= 0x02
        if (data & 0x40) == 0:
            tmp |= 0x01
        return tmp

    def set_color(self, red: int, green: int, blue: int) -> None:
        data = 0
        data |= 0x03 << 30
        data |= self.__get_code(blue)
        data |= self.__get_code(green)
        data |= self.__get_code(red)
        data |= blue << 16
        data |= green << 8
        data |= red

        self.__send_data(data)

    @staticmethod
    def shutdown() -> None:
        GPIO.cleanup()


class RPiGPIOBridge(BaseBridge):
    def __init__(self, rgb_clock: int, rgb_data: int, white_clock: int, white_data: int) -> None:
        self._white = _P9813(clock=white_clock, data=white_data)
        self._rgb = _P9813(clock=rgb_clock, data=rgb_data)

    async def set_color(self, color: Color) -> None:
        """Sets the color on the RGBW strip."""
        self._rgb.set_color(red=color.red, green=color.green, blue=color.blue)
        self._white.set_color(red=color.white, green=0, blue=0)

    async def initialize(self) -> None:
        pass

    async def shutdown(self) -> None:
        self._white.shutdown()
        self._rgb.shutdown()
