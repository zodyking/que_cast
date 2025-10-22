from __future__ import annotations
import json
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN, DEFAULTS,
    CONF_TARGET_MEDIA_PLAYER, CONF_TTS_SERVICE, CONF_TTS_DEFAULT_LANGUAGE, CONF_TTS_DEFAULT_OPTIONS,
    CONF_QUIET_HOURS, CONF_DAY_VOLUME, CONF_NIGHT_VOLUME, CONF_PRE_ROLL_MS,
    CONF_DUCK_ENABLE, CONF_DUCK_TARGETS, CONF_DUCK_VOLUME, CONF_RESTORE_AFTER_MS,
    CONF_DETECT_DONE_MODE, CONF_MAX_SPEECH_SECONDS
)

STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="TTS Proxy"): str,
        vol.Required(CONF_TARGET_MEDIA_PLAYER): str,
        vol.Optional(CONF_TTS_SERVICE, default=DEFAULTS[CONF_TTS_SERVICE]): str,
        vol.Optional(CONF_TTS_DEFAULT_LANGUAGE, default=DEFAULTS[CONF_TTS_DEFAULT_LANGUAGE]): vol.Any(str, None),
        vol.Optional(CONF_TTS_DEFAULT_OPTIONS, default=json.dumps(DEFAULTS[CONF_TTS_DEFAULT_OPTIONS])): str,
        vol.Optional(CONF_QUIET_HOURS, default=DEFAULTS[CONF_QUIET_HOURS]): str,
        vol.Optional(CONF_DAY_VOLUME, default=DEFAULTS[CONF_DAY_VOLUME]): vol.Coerce(float),
        vol.Optional(CONF_NIGHT_VOLUME, default=DEFAULTS[CONF_NIGHT_VOLUME]): vol.Coerce(float),
        vol.Optional(CONF_PRE_ROLL_MS, default=DEFAULTS[CONF_PRE_ROLL_MS]): vol.Coerce(int),

        vol.Optional(CONF_DUCK_ENABLE, default=DEFAULTS[CONF_DUCK_ENABLE]): bool,
        vol.Optional(CONF_DUCK_TARGETS, default=""): str,
        vol.Optional(CONF_DUCK_VOLUME, default=DEFAULTS[CONF_DUCK_VOLUME]): vol.Coerce(float),
        vol.Optional(CONF_RESTORE_AFTER_MS, default=DEFAULTS[CONF_RESTORE_AFTER_MS]): vol.Coerce(int),

        vol.Optional(CONF_DETECT_DONE_MODE, default=DEFAULTS[CONF_DETECT_DONE_MODE]): vol.In(["state", "timer"]),
        vol.Optional(CONF_MAX_SPEECH_SECONDS, default=DEFAULTS[CONF_MAX_SPEECH_SECONDS]): vol.Coerce(int),
    }
)

class TTSProxyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_SCHEMA)

        errors = {}
        try:
            j = user_input.get(CONF_TTS_DEFAULT_OPTIONS, "{}").strip() or "{}"
            json.loads(j)
        except Exception:
            errors["base"] = "invalid_default_options_json"
            return self.async_show_form(step_id="user", data_schema=STEP_SCHEMA, errors=errors)

        return self.async_create_entry(title=user_input.get(CONF_NAME, "TTS Proxy"), data=user_input)

    async def async_step_import(self, import_input):
        return await self.async_step_user(import_input)

class TTSProxyOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        data = {**DEFAULTS, **self.config_entry.data, **(self.config_entry.options or {})}
        schema = vol.Schema(
            {
                vol.Optional(CONF_TARGET_MEDIA_PLAYER, default=data[CONF_TARGET_MEDIA_PLAYER]): str,
                vol.Optional(CONF_TTS_SERVICE, default=data[CONF_TTS_SERVICE]): str,
                vol.Optional(CONF_TTS_DEFAULT_LANGUAGE, default=data[CONF_TTS_DEFAULT_LANGUAGE]): vol.Any(str, None),
                vol.Optional(CONF_TTS_DEFAULT_OPTIONS, default=json.dumps(data[CONF_TTS_DEFAULT_OPTIONS])): str,
                vol.Optional(CONF_QUIET_HOURS, default=data[CONF_QUIET_HOURS]): str,
                vol.Optional(CONF_DAY_VOLUME, default=data[CONF_DAY_VOLUME]): vol.Coerce(float),
                vol.Optional(CONF_NIGHT_VOLUME, default=data[CONF_NIGHT_VOLUME]): vol.Coerce(float),
                vol.Optional(CONF_PRE_ROLL_MS, default=data[CONF_PRE_ROLL_MS]): vol.Coerce(int),

                vol.Optional(CONF_DUCK_ENABLE, default=data[CONF_DUCK_ENABLE]): bool,
                vol.Optional(CONF_DUCK_TARGETS, default=",".join(data[CONF_DUCK_TARGETS] or [])): str,
                vol.Optional(CONF_DUCK_VOLUME, default=data[CONF_DUCK_VOLUME]): vol.Coerce(float),
                vol.Optional(CONF_RESTORE_AFTER_MS, default=data[CONF_RESTORE_AFTER_MS]): vol.Coerce(int),

                vol.Optional(CONF_DETECT_DONE_MODE, default=data[CONF_DETECT_DONE_MODE]): vol.In(["state", "timer"]),
                vol.Optional(CONF_MAX_SPEECH_SECONDS, default=data[CONF_MAX_SPEECH_SECONDS]): vol.Coerce(int),
            }
        )
        if user_input is None:
            return self.async_show_form(step_id="init", data_schema=schema)

        try:
            j = user_input.get(CONF_TTS_DEFAULT_OPTIONS, "{}").strip() or "{}"
            json.loads(j)
        except Exception:
            return self.async_show_form(step_id="init", data_schema=schema, errors={"base": "invalid_default_options_json"})

        return self.async_create_entry(title="", data=user_input)

async def async_get_options_flow(config_entry):
    return TTSProxyOptionsFlow(config_entry)