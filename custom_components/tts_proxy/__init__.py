
from __future__ import annotations
import json
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN, DEFAULTS,
    CONF_TARGET_MEDIA_PLAYER, CONF_TTS_SERVICE, CONF_TTS_DEFAULT_LANGUAGE, CONF_TTS_DEFAULT_OPTIONS,
    CONF_QUIET_HOURS, CONF_DAY_VOLUME, CONF_NIGHT_VOLUME, CONF_PRE_ROLL_MS,
    CONF_DUCK_ENABLE, CONF_DUCK_TARGETS, CONF_DUCK_VOLUME, CONF_RESTORE_AFTER_MS,
    CONF_DETECT_DONE_MODE, CONF_MAX_SPEECH_SECONDS
)
from .queue import TTSQueue
from .config_flow import TTSProxyOptionsFlow

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]

SERVICE_SPEAK = "speak"
SERVICE_SCHEMA = vol.Schema({
    vol.Required("message"): cv.string,
    vol.Optional("proxy_id"): cv.string,
    vol.Optional("media_player_entity_id"): cv.entity_id,
    vol.Optional("language"): cv.string,
    vol.Optional("options", default={}): dict,
    vol.Optional("interrupt", default=False): cv.boolean,
    vol.Optional("priority", default=0): vol.Coerce(int),
    vol.Optional("volume_override"): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
    vol.Optional("pre_roll_ms"): vol.All(vol.Coerce(int), vol.Range(min=0, max=1000)),
})

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    raw = {**entry.data, **(entry.options or {})}
    conf = {
        "target_media_player": raw[CONF_TARGET_MEDIA_PLAYER],
        "tts_service": raw.get(CONF_TTS_SERVICE, DEFAULTS[CONF_TTS_SERVICE]),
        "default_language": raw.get(CONF_TTS_DEFAULT_LANGUAGE),
        "default_options": _safe_json(raw.get(CONF_TTS_DEFAULT_OPTIONS, DEFAULTS[CONF_TTS_DEFAULT_OPTIONS])),
        "quiet_hours": raw.get(CONF_QUIET_HOURS, DEFAULTS[CONF_QUIET_HOURS]),
        "day_volume": float(raw.get(CONF_DAY_VOLUME, DEFAULTS[CONF_DAY_VOLUME])),
        "night_volume": float(raw.get(CONF_NIGHT_VOLUME, DEFAULTS[CONF_NIGHT_VOLUME])),
        "pre_roll_ms": int(raw.get(CONF_PRE_ROLL_MS, DEFAULTS[CONF_PRE_ROLL_MS])),
        "duck_enable": bool(raw.get(CONF_DUCK_ENABLE, DEFAULTS[CONF_DUCK_ENABLE])),
        "duck_targets": _split_targets(raw.get(CONF_DUCK_TARGETS, DEFAULTS[CONF_DUCK_TARGETS])),
        "duck_volume": float(raw.get(CONF_DUCK_VOLUME, DEFAULTS[CONF_DUCK_VOLUME])),
        "restore_after_ms": int(raw.get(CONF_RESTORE_AFTER_MS, DEFAULTS[CONF_RESTORE_AFTER_MS])),
        "detect_done_mode": raw.get(CONF_DETECT_DONE_MODE, DEFAULTS[CONF_DETECT_DONE_MODE]),
        "max_speech_seconds": int(raw.get(CONF_MAX_SPEECH_SECONDS, DEFAULTS[CONF_MAX_SPEECH_SECONDS])),
    }

    proxy_name = entry.title or "TTS Proxy"
    q = TTSQueue(hass, entry.entry_id, proxy_name, conf)
    await q.start()

    hass.data[DOMAIN][entry.entry_id] = {"queue": q, "name": proxy_name, "conf": conf}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if SERVICE_SPEAK not in hass.services.async_services().get(DOMAIN, {}):
        async def handle_speak(call: ServiceCall) -> None:
            data = SERVICE_SCHEMA(call.data)
            q_inst = _resolve_queue(hass, data.get("proxy_id"), data.get("media_player_entity_id"))
            await q_inst.enqueue(
                message=data["message"],
                media_player_entity_id=data.get("media_player_entity_id"),
                language=data.get("language"),
                options=data.get("options"),
                interrupt=bool(data.get("interrupt")),
                priority=int(data.get("priority")),
                volume_override=data.get("volume_override"),
                pre_roll_ms=data.get("pre_roll_ms"),
            )
        hass.services.async_register(DOMAIN, SERVICE_SPEAK, handle_speak)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data:
        await data["queue"].stop()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not hass.data[DOMAIN]:
        try:
            hass.services.async_remove(DOMAIN, SERVICE_SPEAK)
        except Exception:
            pass
    return unload_ok

async def async_get_options_flow(config_entry: ConfigEntry):
    return TTSProxyOptionsFlow(config_entry)

def _resolve_queue(hass: HomeAssistant, proxy_id: Optional[str], mp: Optional[str]) -> TTSQueue:
    domains = hass.data.get(DOMAIN) or {}
    if not domains:
        raise ValueError("No TTS Proxy instances loaded")
    if proxy_id:
        for eid, d in domains.items():
            if eid == proxy_id or d["name"] == proxy_id:
                return d["queue"]
    if mp:
        for d in domains.values():
            if d["conf"]["target_media_player"] == mp:
                return d["queue"]
    return next(iter(domains.values()))["queue"]

def _safe_json(s: Any) -> Dict[str, Any]:
    if isinstance(s, dict):
        return s
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        return {}

def _split_targets(v) -> list[str]:
    if isinstance(v, list):
        return v
    if not v:
        return []
    return [x.strip() for x in str(v).split(",") if x.strip()]
