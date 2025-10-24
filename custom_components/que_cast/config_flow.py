"""Config flow for Que Cast."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from .const import DOMAIN

DATA_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Required("media_player"): selector.EntitySelector(
        selector.EntitySelectorConfig(domain=["media_player"])
    ),
    vol.Optional("tts_engine", default="tts.speak"): vol.In([
        "tts.speak", "tts.google_translate_say", "tts.cloud_say", "tts.polly_say"
    ]),
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
})

class QueCastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Que Cast."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return QueCastOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_only")

        if user_input is not None:
            await self.async_set_unique_id(user_input["name"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

class QueCastOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Que Cast options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(k, default=self.config_entry.options.get(k, v.default)): v
                for k, v in DATA_SCHEMA.schema.items()
            })
        )
