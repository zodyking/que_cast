from __future__ import annotations
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        TTSProxyClearQueueButton(hass, entry, data),
        TTSProxySkipCurrentButton(hass, entry, data),
    ])

class _BaseButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, data) -> None:
        self._hass = hass
        self._entry = entry
               self._queue = data["queue"]
        self._base_name = data["name"]
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=data["name"],
            manufacturer="TTS Proxy",
            model="Queued Forwarder",
        )

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

class TTSProxyClearQueueButton(_BaseButton):
    @property
    def name(self):
        return f"{self._base_name} — Clear Queue"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_clear_queue"

    @property
    def icon(self):
        return "mdi:broom"

    async def async_press(self) -> None:
        await self._queue.clear_queue()

class TTSProxySkipCurrentButton(_BaseButton):
    @property
    def name(self):
        return f"{self._base_name} — Skip Current"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_skip_current"

    @property
    def icon(self):
        return "mdi:skip-next"

    async def async_press(self) -> None:
        await self._queue.skip_current()