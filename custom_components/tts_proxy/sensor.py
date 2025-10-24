from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TTSProxyQueueSizeSensor(data, entry)], True)

class TTSProxyQueueSizeSensor(SensorEntity):
    _attr_icon = "mdi:format-list-numbered"

    def __init__(self, data, entry: ConfigEntry) -> None:
        self._queue = data["queue"]
        self._name = f"{data['name']} Queue"
        self._attr_unique_id = f"{entry.entry_id}_queue_size"
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=data["name"],
            manufacturer="TTS Proxy",
            model="Queued Forwarder",
        )

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._queue.size

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info