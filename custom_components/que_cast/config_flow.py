from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required("media_player"): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["media_player"])
        ),
        vol.Optional("tts_engine", default="tts.speak"): vol.In(
            ["tts.speak", "tts.google_translate_say", "tts.cloud_say", "tts.polly_say"]
        ),
        vol.Optional("default_language", default=""): str,
        vol.Optional("default_options", default="{}"): str,
        vol.Optional("day_volume", default=0.5): vol.All(vol.Coerce(float), vol.Range(0.0, 1.0)),
        vol.Optional("night_volume", default=0.3): vol.All(vol.Coerce(float), vol.Range(0.0, 1.0)),
        vol.Optional("quiet_start", default="22:00"): str,
        vol.Optional("quiet_end", default="07:00"): str,
        vol.Optional("pre_roll_sound", default=""): str,
        vol.Optional("pre_roll_ms", default=100): int,
        vol.Optional("post_grace_ms", default=200): int,
        vol.Optional("ducking_enabled", default=True): bool,
        vol.Optional("detection_mode", default="timer"): vol.In(["timer", "state"]),
    }
)


class QueCastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return QueCastOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_only")

        if user_input is not None:
            await self.async_set_unique_id(user_input["name"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)


class QueCastOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Que Cast options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        def _d(key: str, fallback):
            if key in self.config_entry.options:
                return self.config_entry.options[key]
            if key in self.config_entry.data:
                return self.config_entry.data[key]
            return fallback

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("name", default=_d("name", "")): str,
                    vol.Optional("media_player", default=_d("media_player", "")): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["media_player"])
                    ),
                    vol.Optional("tts_engine", default=_d("tts_engine", "tts.speak")): vol.In(
                        ["tts.speak", "tts.google_translate_say", "tts.cloud_say", "tts.polly_say"]
                    ),
                    vol.Optional("default_language", default=_d("default_language", "")): str,
                    vol.Optional("default_options", default=_d("default_options", "{}")): str,
                    vol.Optional("day_volume", default=_d("day_volume", 0.5)): vol.All(vol.Coerce(float), vol.Range(0.0, 1.0)),
                    vol.Optional("night_volume", default=_d("night_volume", 0.3)): vol.All(vol.Coerce(float), vol.Range(0.0, 1.0)),
                    vol.Optional("quiet_start", default=_d("quiet_start", "22:00")): str,
                    vol.Optional("quiet_end", default=_d("quiet_end", "07:00")): str,
                    vol.Optional("pre_roll_sound", default=_d("pre_roll_sound", "")): str,
                    vol.Optional("pre_roll_ms", default=_d("pre_roll_ms", 100)): int,
                    vol.Optional("post_grace_ms", default=_d("post_grace_ms", 200)): int,
                    vol.Optional("ducking_enabled", default=_d("ducking_enabled", True)): bool,
                    vol.Optional("detection_mode", default=_d("detection_mode", "timer")): vol.In(["timer", "state"]),
                }
            ),
        )
