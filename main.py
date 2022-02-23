import asyncio
import logging
from typing import Set, Any

import uvicorn
from fastapi import FastAPI, Depends, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError, Field
from starlette.websockets import WebSocket, WebSocketDisconnect


class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_json(self, json: Any, exclude: WebSocket = None):
        await asyncio.gather(
            *(
                connection.send_json(json)
                for connection in self.active_connections
                if connection is not exclude
            )
        )


class RGBColor(BaseModel):
    red: int = Field(..., ge=0, le=255)
    green: int = Field(..., ge=0, le=255)
    blue: int = Field(..., ge=0, le=255)

    def update_rgb(self, rgb_color: "RGBColor"):
        self.red = rgb_color.red
        self.green = rgb_color.green
        self.blue = rgb_color.blue


class Color(RGBColor):
    white: int = Field(..., ge=0, le=100)


class Data:
    def __init__(self):
        self.color = Color(red=0, green=0, blue=0, white=0)

    def get_color(self) -> Color:
        return self.color

    def __call__(self) -> "Data":
        return self


DATA = Data()
APP = FastAPI()
RGB_MANAGER = WebSocketManager()
WHITE_MANAGER = WebSocketManager()


@APP.get("/api/color", response_model=Color)
async def get_color(color: Color = Depends(DATA.get_color)):
    # return HTT
    return color


@APP.put("/api/updateRGB")
async def update_rgb(rgb_color: RGBColor, data: Data = Depends(DATA)):
    data.color.update_rgb(rgb_color)


@APP.put("/api/updateWhite")
async def update_white(
    white: int = Body(..., ge=0, le=100, embed=True), data: Data = Depends(DATA)
):
    data.color.white = white


@APP.websocket("/ws/rgb")
async def rgb_websocket(websocket: WebSocket, data: Data = Depends(DATA)):
    await RGB_MANAGER.connect(websocket)
    try:
        while True:
            try:
                json_data = await websocket.receive_json()
                new_rgb = RGBColor(**json_data)
            except ValidationError:
                # TODO: Logging
                continue

            data.color.update_rgb(new_rgb)
            await RGB_MANAGER.broadcast_json(new_rgb.dict(), exclude=websocket)
    except WebSocketDisconnect:
        RGB_MANAGER.disconnect(websocket)


@APP.websocket("/ws/white")
async def white_websocket(websocket: WebSocket, data: Data = Depends(DATA)):
    await WHITE_MANAGER.connect(websocket)
    try:
        while True:
            json_data = await websocket.receive_json()
            new_white = int(json_data["white"])
            if not 0 <= new_white <= 100:
                # TODO: logging
                continue

            data.color.white = new_white
            await WHITE_MANAGER.broadcast_json(json_data, exclude=websocket)
    except WebSocketDisconnect:
        WHITE_MANAGER.disconnect(websocket)


# Order matters!
APP.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:APP", host="led-alarm.local", port=8000, log_level=logging.DEBUG)
