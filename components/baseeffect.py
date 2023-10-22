import abc
from typing import Any

from components.colors import Color


class BaseEffect(abc.ABC):
    @abc.abstractmethod
    def get_color(self, progress: float) -> Color:
        """Must return the current color at time ``progress``, which is a float between
        (including) 0  and 1, specifying the progress of the effect."""

    @property
    @abc.abstractmethod
    def duration(self) -> float:
        """Must return the default duration of the effect."""

    @property
    @abc.abstractmethod
    def repeat(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def stay_on(self) -> bool:
        ...

    @abc.abstractmethod
    def edit(self, **kwargs: Any) -> None:
        ...
