import asyncio
import datetime
import logging
import time
import zoneinfo
from collections.abc import Collection, Coroutine
from types import MappingProxyType
from typing import Any, Literal

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocket

from components.alarm import Alarm, EditAlarm
from components.api import setup_api
from components.basebridge import BaseBridge
from components.baseeffect import BaseEffect
from components.basepersistence import BasePersistence
from components.colors import Color, RGBColor
from components.template_filters import FILTERS
from components.websocketmanager import WebSocketManager

_logger = logging.getLogger(__name__)


def _map_weekdays(ids: Collection[int]) -> str:
    mapping = {0: "sun", 1: "mon", 2: "tue", 3: "wed", 4: "thu", 5: "fri", 6: "sat", 7: "sun"}
    return ",".join(mapping[id_] for id_ in ids)


class Controller:
    def __init__(self, bridge: BaseBridge, persistence: BasePersistence = None) -> None:
        self.bridge = bridge
        self._alarms: dict[str, Alarm] = {}
        self.alarms = MappingProxyType(self._alarms)
        self.scheduler = AsyncIOScheduler()
        self._templates = Jinja2Templates(directory="static")
        self._templates.env.filters.update(FILTERS)
        self.fast_api: FastAPI = FastAPI(
            routes=[
                Route("/", endpoint=self.__static_page),
                Mount("/static", StaticFiles(directory="static"), name="static"),
            ]
        )
        setup_api(self)
        self.websocket_manager = WebSocketManager()
        self.persistence = persistence

        self._color = Color(red=0, green=0, blue=0, white=0)
        self._status: bool = False
        self._effect_task: asyncio.Task | None = None
        self._effect_stop_event = asyncio.Event()
        self._spawned_tasks: set[asyncio.Task] = set()
        self._running: bool = False
        self.__color_persistence_event = asyncio.Event()
        self.__color_persistence_task: asyncio.Task | None = None

    def __static_page(self, request: Request) -> Response:
        return self._templates.TemplateResponse(
            "index.html.jinja2", context={"request": request, "alarms": self.alarms}
        )

    @property
    def running(self) -> bool:
        return self._running

    async def start(self) -> None:
        self.scheduler.start()
        await self.bridge.initialize()
        if self.persistence:
            await self.set_status(await self.persistence.get_status())
            await self.set_color(await self.persistence.get_color())
            self._alarms.update(await self.persistence.get_alarms())

            self.__color_persistence_task = asyncio.create_task(
                self._color_updater(), name="Controller:color_updater"
            )

        for uid, alarm in self.alarms.items():
            if alarm.active:
                self._schedule_alarm(uid)
        self._running = True

    async def stop(self) -> None:
        self.scheduler.shutdown()
        await self.bridge.shutdown()
        await self._cancel_current_effect()
        await asyncio.gather(*self._spawned_tasks, return_exceptions=True)

        if self.persistence:
            self.__color_persistence_event.set()
            if self.__color_persistence_task:
                await self.__color_persistence_task
            self.__color_persistence_task = None
            self.__color_persistence_event.clear()

            await self.persistence.update_color(self.color)
            await self.persistence.flush()

        self._running = False

    async def run(
        self,
        port: int = 8000,
        log_level: int = logging.WARNING,
        use_colors: bool = False,
        **kwargs: Any,
    ) -> None:
        await self.start()
        server = uvicorn.Server(
            config=uvicorn.Config(
                app=self.fast_api, port=port, log_level=log_level, use_colors=use_colors, **kwargs
            )
        )
        await server.serve()
        await self.stop()

    def create_task(self, future: asyncio.Future | Coroutine) -> asyncio.Task:
        task = asyncio.create_task(
            self.__create_task_callback(
                future=future,
            )
        )

        if self.running:
            self._spawned_tasks.add(task)
            task.add_done_callback(self._spawned_tasks.discard)
        else:
            _logger.warning(
                "Tasks created via `Controller.create_task` while the controller is not "
                "running won't be automatically awaited!"
            )

        return task

    @staticmethod
    async def __create_task_callback(
        future: asyncio.Future | Coroutine,
    ) -> Any:
        try:
            return await future
        except Exception as exception:  # pylint: disable=broad-except
            _logger.exception("Future %s raised exception.", future, exc_info=exception)

    async def _color_updater(self) -> None:
        # Update the color in regular intervals. Exit only when the stop event has been set
        while not self.__color_persistence_event.is_set():
            if not self.persistence:
                return

            await self.persistence.update_color(self.color)
            try:
                await asyncio.wait_for(
                    self.__color_persistence_event.wait(),
                    timeout=self.persistence.update_interval,
                )
                return
            except asyncio.TimeoutError:
                pass

    @property
    def color(self) -> Color:
        return self._color

    @property
    def status(self) -> bool:
        return self._status

    async def set_status(self, status: bool, from_websocket: WebSocket = None) -> None:
        self._status = status

        if not self.status:
            await self.bridge.set_off()
        else:
            await self.bridge.set_color(self.color)

        await self.websocket_manager.broadcast_status(status, exclude=from_websocket)

        if self.persistence:
            self.create_task(self.persistence.update_status(status))

    async def set_white(self, white: int, from_websocket: WebSocket = None) -> Literal[True]:
        await self.set_color(
            Color(
                white=white, red=self._color.red, green=self._color.green, blue=self._color.blue
            ),
            from_websocket=from_websocket,
        )
        return True

    async def set_rgb(self, color: RGBColor, from_websocket: WebSocket = None) -> Literal[True]:
        await self.set_color(
            Color(white=self._color.white, red=color.red, green=color.green, blue=color.blue),
            from_websocket=from_websocket,
        )
        return True

    async def _set_color(self, color: Color, from_websocket: WebSocket = None) -> None:
        self._color = color
        if self.status:
            await self.bridge.set_color(color)
        await self.websocket_manager.broadcast_color(color, exclude=from_websocket)

    async def _cancel_current_effect(self) -> None:
        if self._effect_task:
            self._effect_stop_event.set()
            await self._effect_task
            self._effect_stop_event.clear()

    async def set_color(self, color: Color, from_websocket: WebSocket = None) -> None:
        await self._cancel_current_effect()
        await self._set_color(color, from_websocket=from_websocket)

    async def _run_effect(self, effect: BaseEffect, scale: float) -> None:
        delta = 1 / 32
        start = time.monotonic()
        duration = effect.duration * scale
        first_color = True
        while not self._effect_stop_event.is_set():
            progress: float = time.monotonic() - start
            if progress > duration:
                if effect.repeat:
                    progress = progress - duration
                else:
                    if not effect.stay_on:
                        await self.set_status(False)
                    return

            if first_color:
                await self._set_color(effect.get_color(progress=progress / duration))
                self.create_task(self.set_status(status=True))
                first_color = False
            else:
                await self._set_color(effect.get_color(progress=progress / duration))

            await asyncio.sleep(delta)

    async def run_effect(self, effect: BaseEffect, scale: float) -> None:
        await self._cancel_current_effect()
        self._effect_task = self.create_task(self._run_effect(effect=effect, scale=scale))

    async def add_alarm(self, alarm: Alarm) -> str:
        self._alarms[alarm.uid] = alarm
        if alarm.active:
            self._schedule_alarm(alarm.uid)

        if self.persistence:
            self.create_task(self.persistence.update_alarm(alarm))

        await self.websocket_manager.broadcast_alarm(alarm)
        return alarm.uid

    def _schedule_alarm(self, uid: str) -> None:
        alarm = self.alarms[uid]
        job = self.scheduler.get_job(uid)

        if not alarm.active:
            if job is not None:
                job.remove()
            return

        kwargs = {
            "kwargs": {"effect": alarm.effect, "scale": 1},
            "name": uid,
        }

        if alarm.weekdays:
            kwargs["trigger"] = CronTrigger(
                day_of_week=_map_weekdays(alarm.weekdays),
                hour=alarm.effect.start.hour,
                minute=alarm.effect.start.minute,
                second=alarm.effect.start.second,
                timezone=zoneinfo.ZoneInfo(alarm.effect.timezone),
            )
        else:
            tzinfo = zoneinfo.ZoneInfo(alarm.effect.timezone)
            now = datetime.datetime.now(tz=tzinfo)
            datetime_start = datetime.datetime.combine(
                now.date(), alarm.effect.start, tzinfo=tzinfo
            )
            if now > datetime_start:
                datetime_start += datetime.timedelta(days=1)

            kwargs["trigger"] = DateTrigger(run_date=datetime_start, timezone=tzinfo)

        if alarm.weekdays:
            func = self.run_effect
        else:

            async def wrapper(effect: BaseEffect, scale: float) -> None:
                self.create_task(
                    self.edit_alarm(uid=alarm.uid, edited_alarm=EditAlarm(active=False))
                )
                return await self.run_effect(effect=effect, scale=scale)

            func = wrapper

        if job is not None:
            job.modify(**kwargs, func=func)
            job.reschedule(**kwargs)
        else:
            kwargs["id"] = uid
            self.scheduler.add_job(func=func, **kwargs)

    async def delete_alarm(self, uid: str, from_websocket: WebSocket = None) -> Literal[True]:
        try:
            alarm = self._alarms.pop(uid)
        except KeyError as exc:
            raise ValueError("No alarm with this uid known.") from exc

        if (job := self.scheduler.get_job(uid)) is not None:
            job.remove()

        if self.persistence:
            self.create_task(self.persistence.drop_alarm(alarm))

        await self.websocket_manager.broadcast_delete_alarm(uid, exclude=from_websocket)

        return True

    async def edit_alarm(
        self, uid: str, edited_alarm: EditAlarm, from_websocket: WebSocket = None
    ) -> Literal[True]:
        try:
            alarm = self.alarms[uid]
        except KeyError as exc:
            raise ValueError("No alarm with this uid known.") from exc

        alarm.edit(edited_alarm)
        self._schedule_alarm(uid)

        if self.persistence:
            self.create_task(self.persistence.update_alarm(alarm))

        await self.websocket_manager.broadcast_alarm(alarm, exclude=from_websocket)

        return True
