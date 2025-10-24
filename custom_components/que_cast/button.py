from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


class QueCastClearQueueButton(ButtonEntity):
    _attr_icon = "mdi:delete"

    def __init__(self, hass: HomeAssistant, instance_id: str, config: dict):
        self._hass = hass
        self._instance_id = instance_id
        self._attr_name = f"Que Cast {config['name']} Clear Queue"
        self._attr_unique_id = f"{instance_id}_clear_queue"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, instance_id)},
            "name": config["name"],
            "manufacturer": "Que Cast",
        }

    async def async_press(self) -> None:
        queue_manager = self._hass.data[DOMAIN][self._instance_id]["queue_manager"]
        await queue_manager.clear_queue()


class QueCastSkipCurrentButton(ButtonEntity):
    _attr_icon = "mdi:skip-forward"

    def __init__(self, hass: HomeAssistant, instance_id: str, config: dict):
        self._hass = hass
        self._instance_id = instance_id
        self._attr_name = f"Que Cast {config['name']} Skip Current"
        self._attr_unique_id = f"{instance_id}_skip_current"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, instance_id)},
            "name": config["name"],
            "manufacturer": "Que Cast",
        }

    async def async_press(self) -> None:
        queue_manager = self._hass.data[DOMAIN][self._instance_id]["queue_manager"]
        await queue_manager.skip_current()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    instance_id = entry.entry_id
    config = hass.data[DOMAIN][instance_id]["config"]
    async_add_entities(
        [
            QueCastClearQueueButton(hass, instance_id, config),
            QueCastSkipCurrentButton(hass, instance_id, config),
        ]
    )
