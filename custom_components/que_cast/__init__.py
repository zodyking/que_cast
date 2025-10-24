"""Que Cast - TTS and Media Proxy Integration."""

from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .queue_manager import QueCastQueueManager

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Que Cast integration (YAML not used)."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    instance_id = entry.entry_id
    config = entry.data

    media_player = config.get("media_player")
    if not hass.states.get(media_player):
        _LOGGER.error("Media player %s not found", media_player)
        return False

    queue_manager = QueCastQueueManager(hass, instance_id, config)
    hass.data[DOMAIN][instance_id] = {
        "queue_manager": queue_manager,
        "config": config,
        "entry": entry,
    }

    # Expose platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])

    await queue_manager.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    instance_id = entry.entry_id
    if instance_id in hass.data[DOMAIN]:
        queue_manager = hass.data[DOMAIN][instance_id]["queue_manager"]
        await queue_manager.async_stop()
        del hass.data[DOMAIN][instance_id]

    await hass.config_entries.async_forward_entry_unload(entry, ["sensor", "button"])
    return True


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register Que Cast services."""

    async def speak_service(call: ServiceCall) -> None:
        instance_id = call.data.get("instance_id")
        if not instance_id or instance_id not in hass.data[DOMAIN]:
            _LOGGER.error("Invalid instance_id: %s", instance_id)
            return

        queue_manager: QueCastQueueManager = hass.data[DOMAIN][instance_id]["queue_manager"]
        await queue_manager.enqueue_speak(
            message=call.data.get("message"),
            language=call.data.get("language", ""),
            options=call.data.get("options", "{}"),
            interrupt=call.data.get("interrupt", False),
            priority=call.data.get("priority", 0),
            volume=call.data.get("volume_override"),
            pre_roll=call.data.get("pre_roll_ms"),
        )

    hass.services.async_register(
        DOMAIN,
        "speak",
        speak_service,
        schema=vol.Schema(
            {
                vol.Required("instance_id"): str,
                vol.Required("message"): str,
                vol.Optional("language"): str,
                vol.Optional("options"): str,
                vol.Optional("interrupt", default=False): bool,
                vol.Optional("priority", default=0): int,
                vol.Optional("volume_override"): vol.All(vol.Coerce(float), vol.Range(0.0, 1.0)),
                vol.Optional("pre_roll_ms"): int,
            }
        ),
    )
