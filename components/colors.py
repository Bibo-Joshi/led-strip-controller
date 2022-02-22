from typing import Annotated

from pydantic import BaseModel, conint  # pylint: disable=no-name-in-module


class RGBColor(BaseModel):
    red: Annotated[int, conint(ge=0, le=255)]
    green: Annotated[int, conint(ge=0, le=255)]
    blue: Annotated[int, conint(ge=0, le=255)]


class Color(RGBColor):
    white: Annotated[int, conint(ge=0, le=255)]
