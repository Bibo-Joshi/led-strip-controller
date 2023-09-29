import asyncio
from typing import Any

from starlette.websockets import WebSocket

from components.alarm import Alarm
from components.colors import Color, RGBColor


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast_white(self, white: int, exclude: WebSocket = None) -> None:
        return await self.broadcast_json({"updateWhite": white}, exclude=exclude)

    async def broadcast_rgb(self, rgb_color: RGBColor, exclude: WebSocket = None) -> None:
        return await self.broadcast_json({"updateRGB": rgb_color.dict()}, exclude=exclude)

    async def broadcast_color(self, color: Color, exclude: WebSocket = None) -> None:
        return await self.broadcast_json({"updateColor": color.dict()}, exclude=exclude)

    async def broadcast_status(self, status: bool, exclude: WebSocket = None) -> None:
        return await self.broadcast_json({"updateStatus": status}, exclude=exclude)

    async def broadcast_alarm(self, alarm: Alarm, exclude: WebSocket = None) -> None:
        # Need .json() instead of .dict() due to datetime objects
        return await self.broadcast_json({"setAlarm": alarm.json()}, exclude=exclude)

    async def broadcast_delete_alarm(self, uid: str, exclude: WebSocket = None) -> None:
        return await self.broadcast_json({"deleteAlarm": uid}, exclude=exclude)

    async def broadcast_json(self, json: Any, exclude: WebSocket = None) -> None:
        async with self._lock:
            await asyncio.gather(
                *(
                    connection.send_json(json)
                    for connection in self.active_connections
                    if connection is not exclude
                )
            )
