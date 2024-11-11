"""Config flow for MPK Łódź integration."""
import voluptuous as vol
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME, CONF_ID
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    CONF_NUM,
    CONF_GROUP,
    CONF_STOPS,
    CONF_LINES,
    CONF_DIRECTIONS,
)

class MPKLodzOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for MPK Łódź integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Convert comma-separated strings to lists
            lines = [line.strip() for line in user_input.get(CONF_LINES, "").split(",") if line.strip()]
            directions = [dir.strip() for dir in user_input.get(CONF_DIRECTIONS, "").split(",") if dir.strip()]

            return self.async_create_entry(
                title="",
                data={
                    CONF_ID: user_input[CONF_ID],
                    CONF_NUM: user_input[CONF_NUM],
                    CONF_GROUP: user_input[CONF_GROUP],
                    CONF_LINES: lines,
                    CONF_DIRECTIONS: directions,
                },
            )

        stop = self.config_entry.data[CONF_STOPS][0]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ID, default=stop.get(CONF_ID, 0)): vol.Coerce(int),
                    vol.Optional(CONF_NUM, default=stop.get(CONF_NUM, 0)): vol.Coerce(int),
                    vol.Optional(CONF_GROUP, default=stop.get(CONF_GROUP, 0)): vol.Coerce(int),
                    vol.Optional(CONF_LINES, default=",".join(stop.get(CONF_LINES, []))): str,
                    vol.Optional(CONF_DIRECTIONS, default=",".join(stop.get(CONF_DIRECTIONS, []))): str,
                }
            )
        )

class MPKLodzConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MPK Łódź."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Convert comma-separated strings to lists
            lines = [line.strip() for line in user_input.get(CONF_LINES, "").split(",") if line.strip()]
            directions = [dir.strip() for dir in user_input.get(CONF_DIRECTIONS, "").split(",") if dir.strip()]

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_STOPS: [{
                        CONF_ID: user_input.get(CONF_ID, 0),
                        CONF_NUM: user_input.get(CONF_NUM, 0),
                        CONF_GROUP: user_input.get(CONF_GROUP, 0),
                        CONF_LINES: lines,
                        CONF_DIRECTIONS: directions
                    }]
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_ID, default=0): vol.Coerce(int),
                    vol.Optional(CONF_NUM, default=0): vol.Coerce(int),
                    vol.Optional(CONF_GROUP, default=0): vol.Coerce(int),
                    vol.Optional(CONF_LINES, default=""): str,
                    vol.Optional(CONF_DIRECTIONS, default=""): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MPKLodzOptionsFlow:
        """Get the options flow for this handler."""
        return MPKLodzOptionsFlow(config_entry)
