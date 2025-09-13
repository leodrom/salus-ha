"""Salus integration."""

from __future__ import annotations

import logging

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.discovery import async_load_platform
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

DOMAIN = "salus"


_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class SalusDevice:
    """Dummy device holding the Salus thermostat state."""

    def __init__(self) -> None:
        self.room_temperature: float = 20.0
        self.target_temperature: float = 22.0
        self.hvac_mode: HVACMode = HVACMode.HEAT
        self._listeners: list[callable] = []

    def register_listener(self, callback) -> None:
        """Register a callback to be notified on state changes."""
        self._listeners.append(callback)

    def _notify(self) -> None:
        for callback in self._listeners:
            callback()


async def async_setup(hass, config):
    """Set up the Salus integration."""
    conf = config[DOMAIN]
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    _LOGGER.info("Setting up Salus integration")
    _LOGGER.debug("Configuration username: %s", username)

    device = SalusDevice()
    hass.data[DOMAIN] = {
        "device": device,
        "username": username,
        "password": password,
    }

    _LOGGER.debug("Creating Salus platforms")
    hass.async_create_task(
        async_load_platform(hass, "climate", DOMAIN, {}, config)
    )
    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )
    _LOGGER.info("Salus integration setup complete")
    return True
