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


APP = FastAPI()
MANAGER = WebSocketManager()


class Data:
    def __init__(self):
        self.color = Color(red=0, green=0, blue=0, white=0)
        self.status: bool = False

    def get_color(self) -> Color:
        return self.color

    def get_status(self) -> bool:
        return self.status

    def __call__(self) -> "Data":
        return self


DATA = Data()


@APP.get("/api/color", response_model=Color)
async def get_color():
    return DATA.color


@APP.get("/api/status", response_model=bool)
async def get_status():
    return DATA.status


@APP.put("/api/updateRGB")
async def update_rgb(rgb_color: RGBColor):
    DATA.color.update_rgb(rgb_color)
    await MANAGER.broadcast_json({'updateRGB': rgb_color.dict()})


@APP.put("/api/updateWhite")
async def update_white(
    white: int = Body(..., ge=0, le=100, embed=True)
):
    DATA.color.white = white
    await MANAGER.broadcast_json({'updateWhite': white})


@APP.websocket("/ws")
async def websocket(websocket: WebSocket):
    await MANAGER.connect(websocket)
    try:
        while True:
            json_data = await websocket.receive_json()
            if rgb_data := json_data.get('updateRGB'):
                try:
                    new_rgb = RGBColor(**rgb_data)
                except ValidationError:
                    # TODO: Logging
                    continue

                DATA.color.update_rgb(new_rgb)
            elif white := json_data.get('updateWhite'):
                new_white = int(white)
                if not 0 <= new_white <= 100:
                    # TODO: logging
                    continue

                DATA.color.white = new_white
            elif (status := json_data.get('updateStatus')) is not None:
                DATA.status = status

            await MANAGER.broadcast_json(json_data, exclude=websocket)
    except WebSocketDisconnect:
        MANAGER.disconnect(websocket)


# Order matters!
APP.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:APP", host="led-alarm.local", port=8000, log_level=logging.DEBUG)
