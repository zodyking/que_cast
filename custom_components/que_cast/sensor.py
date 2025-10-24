from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


class QueCastQueueSizeSensor(SensorEntity):
    _attr_icon = "mdi:playlist-queue"
    _attr_native_unit_of_measurement = "items"

    def __init__(self, hass: HomeAssistant, instance_id: str, config: dict):
        self._hass = hass
        self._instance_id = instance_id
        self._attr_name = f"Que Cast {config['name']} Queue Size"
        self._attr_unique_id = f"{instance_id}_queue_size"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, instance_id)},
            "name": config["name"],
            "manufacturer": "Que Cast",
        }

    @property
    def native_value(self):
        queue_manager = self._hass.data[DOMAIN][self._instance_id]["queue_manager"]
        return len(queue_manager.queue)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    instance_id = entry.entry_id
    config = hass.data[DOMAIN][instance_id]["config"]
    async_add_entities([QueCastQueueSizeSensor(hass, instance_id, config)])
