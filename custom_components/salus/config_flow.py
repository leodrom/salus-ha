"""Config flow for Salus integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from . import DOMAIN


class SalusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Salus."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Salus", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)
