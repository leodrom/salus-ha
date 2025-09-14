from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback

from . import DOMAIN


class SalusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Salus integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title="Salus", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_import(self, user_input: dict):
        """Handle import from configuration.yaml."""
        return await self.async_step_user(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow for this handler."""
        return SalusOptionsFlow(config_entry)


class SalusOptionsFlow(config_entries.OptionsFlow):
    """Handle Salus options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Salus options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        """Manage Salus options."""
        current = {
            CONF_USERNAME: self.config_entry.options.get(
                CONF_USERNAME, self.config_entry.data[CONF_USERNAME]
            ),
            CONF_PASSWORD: self.config_entry.options.get(
                CONF_PASSWORD, self.config_entry.data[CONF_PASSWORD]
            ),
        }
        if user_input is not None:
            reload_requested = user_input.pop("reload", False)
            if reload_requested or user_input != current:
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self.config_entry.entry_id)
                )
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=current[CONF_USERNAME]): str,
                vol.Required(CONF_PASSWORD, default=current[CONF_PASSWORD]): str,
                vol.Optional("reload", default=False): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
