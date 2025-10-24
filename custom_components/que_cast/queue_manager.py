"""Queue manager for Que Cast."""
import asyncio
import json
import logging
from datetime import time
from typing import Optional
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class QueCastQueueItem:
    def __init__(self, message: str, language: str = "", options: str = "{}",
                 priority: int = 0, volume: Optional[float] = None,
                 pre_roll: Optional[int] = None, interrupt: bool = False):
        self.message = message
        self.language = language or None
        self.options = options
        self.priority = priority
        self.volume = volume
        self.pre_roll = pre_roll
        self.interrupt = interrupt
        self.timestamp = dt_util.utcnow()
        self.id = hash(f"{message}{language}{self.timestamp}")

class QueCastQueueManager:
    def __init__(self, hass: HomeAssistant, instance_id: str, config: dict):
        self._hass = hass
        self._instance_id = instance_id
        self._config = config
        self._media_player = config["media_player"]
        self._tts_engine = config.get("tts_engine", "tts.speak")
        self._default_language = config.get("default_language")
        self._default_options = config.get("default_options", "{}")
        self._day_volume = config.get("day_volume", 0.5)
        self._night_volume = config.get("night_volume", 0.3)
        self._quiet_start = time.fromisoformat(config.get("quiet_start", "22:00"))
        self._quiet_end = time.fromisoformat(config.get("quiet_end", "07:00"))
        self._pre_roll_sound = config.get("pre_roll_sound", "")
        self._pre_roll_ms = config.get("pre_roll_ms", 100)
        self._post_grace_ms = config.get("post_grace_ms", 200)
        self._ducking_enabled = config.get("ducking_enabled", True)
        self._detection_mode = config.get("detection_mode", "timer")
        
        self._queue: list[QueCastQueueItem] = []  # Explicitly initialize as instance variable
        self._current_item: Optional[QueCastQueueItem] = None
        self._is_playing = False
        self._task: Optional[asyncio.Task] = None
        self._original_volumes = {}
        self._lock = asyncio.Lock()
    
    async def async_start(self) -> None:
        """Start the queue manager."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._queue_worker())
    
    async def async_stop(self) -> None:
        """Stop the queue manager."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def enqueue_speak(self, message: str, language: str = "", options: str = "{}",
                           interrupt: bool = False, priority: int = 0,
                           volume: Optional[float] = None, pre_roll: Optional[int] = None) -> None:
        """Enqueue a speak request."""
        item = QueCastQueueItem(
            message, language, options, priority, volume,
            pre_roll or self._pre_roll_ms, interrupt
        )
        
        async with self._lock:
            if interrupt and self._current_item:
                self._current_item = None
                await self._stop_current()
            
            # Insert by priority (higher priority first)
            inserted = False
            for i, existing in enumerate(self._queue):
                if -priority > -existing.priority:
                    self._queue.insert(i, item)
                    inserted = True
                    break
            if not inserted:
                self._queue.append(item)
        
        await self.async_start()
    
    async def clear_queue(self) -> None:
        """Clear the queue."""
        async with self._lock:
            self._queue.clear()
    
    async def skip_current(self) -> None:
        """Skip current item."""
        async with self._lock:
            if self._current_item:
                self._current_item = None
                await self._stop_current()
    
    @property
    def queue(self) -> list:
        """Return the current queue."""
        return self._queue
    
    async def _queue_worker(self) -> None:
        """Main queue worker."""
        while True:
            try:
                await self._process_next_item()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.error(f"Queue worker error: {e}")
                await asyncio.sleep(5)
    
    async def _process_next_item(self) -> None:
        """Process next queue item."""
        async with self._lock:
            if not self._queue and not self._current_item:
                self._is_playing = False
                return
        
        if self._current_item:
            if await self._is_current_done():
                await self._finish_current()
            return
        
        async with self._lock:
            if self._queue:
                self._current_item = self._queue.pop(0)
        
        if self._current_item:
            await self._play_current_item()
    
    async def _play_current_item(self) -> None:
        """Play current item."""
        self._is_playing = True
        
        volume = self._get_current_volume(self._current_item.volume)
        
        if self._ducking_enabled:
            await self._duck_other_players(volume)
        
        if self._pre_roll_sound:
            await self._play_pre_roll()
            await asyncio.sleep(self._pre_roll_ms / 1000.0)
        
        try:
            service_data = {
                "entity_id": self._media_player,
                "message": self._current_item.message,
                "cache": False,
            }
            if self._current_item.language:
                service_data["language"] = self._current_item.language
            try:
                opts = json.loads(self._current_item.options or self._default_options)
                service_data.update(opts)
            except json.JSONDecodeError:
                pass
            
            await self._hass.services.async_call(
                self._tts_engine, "speak", service_data, blocking=True
            )
            
            await self._hass.services.async_call(
                "media_player", "volume_set",
                {"entity_id": self._media_player, "volume_level": volume},
                blocking=True
            )
        except Exception as e:
            _LOGGER.error(f"TTS error: {e}")
            self._current_item = None
    
    async def _is_current_done(self) -> bool:
        """Check if current item is done."""
        if self._detection_mode == "state":
            state = self._hass.states.get(self._media_player)
            return state and state.state in ["idle", "off", "paused"]
        else:
            duration = 5.0
            if self._current_item.timestamp:
                elapsed = (dt_util.utcnow() - self._current_item.timestamp).total_seconds()
                return elapsed > duration
        return False
    
    async def _finish_current(self) -> None:
        """Finish current item."""
        if self._ducking_enabled:
            await self._restore_volumes()
        
        await asyncio.sleep(self._post_grace_ms / 1000.0)
        self._current_item = None
        self._is_playing = False
    
    async def _stop_current(self) -> None:
        """Stop current playback."""
        await self._hass.services.async_call(
            "media_player", "media_stop",
            {"entity_id": self._media_player},
            blocking=True
        )
        if self._ducking_enabled:
            await self._restore_volumes()
        self._is_playing = False
    
    async def _play_pre_roll(self) -> None:
        """Play pre-roll sound."""
        if self._pre_roll_sound:
            await self._hass.services.async_call(
                "media_player", "play_media",
                {
                    "entity_id": self._media_player,
                    "media_content_id": self._pre_roll_sound,
                    "media_content_type": "music"
                },
                blocking=True
            )
    
    def _get_current_volume(self, override: Optional[float]) -> float:
        """Get appropriate volume based on time."""
        if override is not None:
            return override
        
        now = dt_util.now().time()
        if self._is_quiet_time(now):
            return self._night_volume
        return self._day_volume
    
    def _is_quiet_time(self, now_time: time) -> bool:
        """Check if current time is quiet hours."""
        if self._quiet_start < self._quiet_end:
            return self._quiet_start <= now_time <= self._quiet_end
        return now_time >= self._quiet_start or now_time <= self._quiet_end
    
    async def _duck_other_players(self, tts_volume: float) -> None:
        """Duck other media players."""
        self._original_volumes.clear()
        for entity in self._hass.states.async_all("media_player"):
            if entity.entity_id != self._media_player and entity.state == "playing":
                vol = entity.attributes.get("volume_level", 0.5)
                self._original_volumes[entity.entity_id] = vol
                duck_vol = max(0.1, vol * 0.3)
                await self._hass.services.async_call(
                    "media_player", "volume_set",
                    {"entity_id": entity.entity_id, "volume_level": duck_vol}
                )
    
    async def _restore_volumes(self) -> None:
        """Restore original volumes."""
        for entity_id, vol in self._original_volumes.items():
            await self._hass.services.async_call(
                "media_player", "volume_set",
                {"entity_id": entity_id, "volume_level": vol}
            )
        self._original_volumes.clear()
