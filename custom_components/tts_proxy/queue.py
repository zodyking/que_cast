
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any, Dict, Optional, Tuple, List

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.const import STATE_PLAYING, STATE_BUFFERING

_LOGGER = logging.getLogger(__name__)

@dataclass(order=True)
class QueueItem:
    sort_key: Tuple[int, int]
    message: str = field(compare=False)
    media_player_entity_id: Optional[str] = field(compare=False, default=None)
    language: Optional[str] = field(compare=False, default=None)
    options: Optional[Dict[str, Any]] = field(compare=False, default=None)
    interrupt: bool = field(compare=False, default=False)
    volume_override: Optional[float] = field(compare=False, default=None)
    pre_roll_ms: Optional[int] = field(compare=False, default=None)

class TTSQueue:
    def __init__(self, hass: HomeAssistant, entry_id: str, name: str, conf: Dict[str, Any]) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.name = name
        self.conf = conf
        self._queue: asyncio.PriorityQueue[QueueItem] = asyncio.PriorityQueue()
        self._idx = 0
        self._worker_task: Optional[asyncio.Task] = None
        self._stopped = asyncio.Event()
        self._current_target: Optional[str] = None
        self._duck_restore: Dict[str, Optional[float]] = {}

    @property
    def size(self) -> int:
        return self._queue.qsize()

    async def start(self) -> None:
        if self._worker_task is None:
            self._stopped.clear()
            self._worker_task = asyncio.create_task(self._worker(), name=f"tts_proxy_worker_{self.entry_id}")

    async def stop(self) -> None:
        self._stopped.set()
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except Exception:
                pass
            self._worker_task = None

    def _in_quiet_hours(self, now: Optional[datetime] = None) -> bool:
        window = self.conf.get("quiet_hours")
        if not window:
            return False
        if now is None:
            now = dt_util.now()
        try:
            start_s, end_s = window.split("-")
            s_h, s_m = [int(x) for x in start_s.split(":")]
            e_h, e_m = [int(x) for x in end_s.split(":")]
            start_t, end_t = time(s_h, s_m), time(e_h, e_m)
        except Exception:
            start_t, end_t = time(22, 0), time(7, 0)
        now_t = now.time()
        if start_t <= end_t:
            return start_t <= now_t < end_t
        return now_t >= start_t or now_t < end_t

    async def enqueue(self, *, message: str, media_player_entity_id: Optional[str], language: Optional[str],
                      options: Optional[Dict[str, Any]], interrupt: bool, priority: int,
                      volume_override: Optional[float], pre_roll_ms: Optional[int]) -> None:
        self._idx += 1
        item = QueueItem(
            sort_key=(-priority, self._idx),
            message=message,
            media_player_entity_id=media_player_entity_id,
            language=language,
            options=options,
            interrupt=interrupt,
            volume_override=volume_override,
            pre_roll_ms=pre_roll_ms,
        )
        if interrupt:
            await self._interrupt_now(item.media_player_entity_id or self.conf["target_media_player"])
        await self._queue.put(item)

    async def clear_queue(self) -> None:
        try:
            while True:
                self._queue.get_nowait()
                self._queue.task_done()
        except asyncio.QueueEmpty:
            pass

    async def skip_current(self) -> None:
        target = self._current_target or self.conf["target_media_player"]
        await self.hass.services.async_call("media_player", "media_stop", {"entity_id": target}, blocking=False)

    async def _interrupt_now(self, target: str) -> None:
        await self.clear_queue()
        await self.hass.services.async_call("media_player", "media_stop", {"entity_id": target}, blocking=False)

    async def _worker(self) -> None:
        while not self._stopped.is_set():
            item: QueueItem = await self._queue.get()
            try:
                await self._handle_item(item)
            except Exception:
                _LOGGER.exception("tts_proxy: error handling item on %s", self.entry_id)
            finally:
                self._queue.task_done()

    async def _handle_item(self, item: QueueItem) -> None:
        target = item.media_player_entity_id or self.conf["target_media_player"]
        self._current_target = target
        tts_service = self.conf.get("tts_service") or "tts.speak"
        domain, svc = tts_service.split(".", 1) if "." in tts_service else ("tts", "speak")

        volume = item.volume_override if item.volume_override is not None else (
            self.conf["night_volume"] if self._in_quiet_hours() else self.conf["day_volume"]
        )
        volume = max(0.0, min(1.0, volume))

        if self.conf.get("duck_enable"):
            await self._duck(True)

        await self.hass.services.async_call("media_player", "volume_set",
                                            {"entity_id": target, "volume_level": volume}, blocking=False)
        pre_roll_ms = item.pre_roll_ms if item.pre_roll_ms is not None else int(self.conf.get("pre_roll_ms") or 0)
        if pre_roll_ms > 0:
            await asyncio.sleep(pre_roll_ms / 1000)

        data = {"media_player_entity_id": target, "message": item.message}
        lang = item.language if item.language is not None else self.conf.get("default_language")
        if lang:
            data["language"] = lang
        opts = {}
        default_opts = self.conf.get("default_options") or {}
        if default_opts:
            opts.update(default_opts)
        if item.options:
            opts.update(item.options)
        if opts:
            data["options"] = opts

        await self.hass.services.async_call(domain, svc, data, blocking=True)

        await self._wait_until_idle(target)

        restore_ms = int(self.conf.get("restore_after_ms") or 0)
        if restore_ms > 0:
            await asyncio.sleep(restore_ms / 1000)

        if self.conf.get("duck_enable"):
            await self._duck(False)

        self._current_target = None

    async def _duck(self, enable: bool) -> None:
        targets: List[str] = self.conf.get("duck_targets") or []
        if not targets:
            return
        if enable:
            self._duck_restore = {}
            for ent in targets:
                st = self.hass.states.get(ent)
                prev = None
                if st and (lvl := st.attributes.get("volume_level")) is not None:
                    try:
                        prev = float(lvl)
                    except Exception:
                        prev = None
                self._duck_restore[ent] = prev
                try:
                    await self.hass.services.async_call("media_player", "volume_set",
                        {"entity_id": ent, "volume_level": self.conf.get("duck_volume", 0.15)}, blocking=False)
                except Exception:
                    pass
        else:
            for ent, prev in self._duck_restore.items():
                try:
                    if prev is not None:
                        await self.hass.services.async_call("media_player", "volume_set",
                            {"entity_id": ent, "volume_level": max(0.0, min(1.0, prev))}, blocking=False)
                except Exception:
                    pass
            self._duck_restore = {}

    async def _wait_until_idle(self, target: str) -> None:
        mode = (self.conf.get("detect_done_mode") or "state").lower()
        if mode == "timer":
            est = max(2.0, min(float(self.conf.get("max_speech_seconds") or 45), 90.0))
            await asyncio.sleep(est)
            return

        max_wait = max(4.0, min(float(self.conf.get("max_speech_seconds") or 45), 120.0))
        total = 0.0
        interval = 0.25
        while total < max_wait:
            st = self.hass.states.get(target)
            if st is None or st.state not in (STATE_PLAYING, STATE_BUFFERING):
                await asyncio.sleep(0.2)
                break
            await asyncio.sleep(interval)
            total += interval
