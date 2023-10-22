import datetime as dtm
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Literal

from fastapi import Body, HTTPException
from pydantic import ValidationError
from starlette.websockets import WebSocket, WebSocketDisconnect

from components.alarm import Alarm, EditAlarm, InputAlarm
from components.alarmeffect import AlarmEffect
from components.colors import Color, RGBColor

if TYPE_CHECKING:
    from components.controller import Controller

_logger = logging.getLogger(__name__)


def setup_api(controller: "Controller") -> None:
    @controller.fast_api.get("/api/color", response_model=Color)
    async def get_color() -> Color:
        return controller.color

    @controller.fast_api.get("/api/status", response_model=bool)
    async def get_status() -> bool:
        return controller.status

    @controller.fast_api.put("/api/updateRGB", response_model=bool)
    async def update_rgb(rgb_color: RGBColor) -> Literal[True]:
        return await controller.set_rgb(rgb_color)

    @controller.fast_api.put("/api/updateWhite", response_model=bool)
    async def update_white(white: int = Body(..., ge=0, le=255, embed=True)) -> Literal[True]:
        return await controller.set_white(white)

    @controller.fast_api.put("/api/addAlarm", response_model=str)
    async def add_alarm(alarm: InputAlarm) -> str:
        effective_alarm = Alarm.from_input_alarm(alarm)
        await controller.add_alarm(effective_alarm)
        return effective_alarm.uid

    @controller.fast_api.get("/api/getAlarms", response_model=list[Alarm])
    async def show_alarms() -> list[Alarm]:
        return list(controller.alarms.values())

    @controller.fast_api.post("/api/deleteAlarm", response_model=bool)
    async def delete_alarm(uid: str) -> Literal[True]:
        try:
            return await controller.delete_alarm(uid)
        except ValueError as exc:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Alarm not found."
            ) from exc

    @controller.fast_api.put("/api/editAlarm", response_model=bool)
    async def edit_alarm(uid: str, alarm: EditAlarm) -> Literal[True]:
        try:
            return await controller.edit_alarm(uid=uid, edited_alarm=alarm)
        except ValueError as exc:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Alarm not found."
            ) from exc

    @controller.fast_api.websocket("/ws")
    async def web_socket(websocket: WebSocket) -> None:
        await controller.websocket_manager.connect(websocket)
        try:
            while True:
                json_data = await websocket.receive_json()
                _logger.info("Websocket received data `%s`", json_data)
                if rgb_data := json_data.get("updateRGB"):
                    try:
                        new_rgb = RGBColor(**rgb_data)
                    except ValidationError:
                        _logger.warning(
                            "Websocket got invalid data `%s` for `updateRGB`. Ignoring.", rgb_data
                        )
                        continue

                    await controller.set_rgb(new_rgb, from_websocket=websocket)
                elif (white := json_data.get("updateWhite")) is not None:
                    new_white = int(white)
                    if not 0 <= new_white <= 255:
                        _logger.warning(
                            "Websocket got invalid data `%s` for `updateWhite`. Ignoring.", white
                        )
                        continue

                    await controller.set_white(new_white, from_websocket=websocket)
                elif (status := json_data.get("updateStatus")) is not None:
                    await controller.set_status(status, from_websocket=websocket)
                elif (edit_alarm_data := json_data.get("editAlarm")) is not None:
                    uid = edit_alarm_data.get("uid")
                    edited_alarm_data = edit_alarm_data.get("editedAlarm", {})
                    _logger.info("Editing alarm `%s` with data `%s`", uid, edited_alarm_data)
                    try:
                        edited_alarm = EditAlarm(**edited_alarm_data)
                    except ValidationError:
                        _logger.warning(
                            "Websocket got invalid data `%s` for `editAlarm`. Ignoring.",
                            edited_alarm_data,
                        )
                        continue

                    await controller.edit_alarm(
                        uid=uid, edited_alarm=edited_alarm, from_websocket=websocket
                    )
                elif (delete_alarm_uid := json_data.get("deleteAlarm")) is not None:
                    await controller.delete_alarm(delete_alarm_uid, from_websocket=websocket)
                elif (json_data.get("addNewAlarm")) is not None:
                    alarm = Alarm(
                        effect=AlarmEffect(
                            start=dtm.time(6, 0), end=dtm.time(7, 0), off=dtm.time(8, 0)
                        ),
                        active=False,
                    )
                    await controller.add_alarm(alarm)

        except WebSocketDisconnect:
            controller.websocket_manager.disconnect(websocket)
