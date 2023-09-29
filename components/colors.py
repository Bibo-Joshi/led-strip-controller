from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class RGBColor(BaseModel):
    red: int = Field(ge=0, le=255)
    green: int = Field(ge=0, le=255)
    blue: int = Field(ge=0, le=255)


class Color(RGBColor):
    white: int = Field(ge=0, le=255)
