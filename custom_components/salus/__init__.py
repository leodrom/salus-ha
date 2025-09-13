"""Salus integration."""

from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import random

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

    def __init__(self, device_id: str, name: str) -> None:
        self.id = device_id
        self.name = name
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


PLATFORMS = ["climate", "sensor"]


async def async_setup(hass, config):
    """Set up the Salus integration."""
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=config[DOMAIN],
            )
        )
    return True


async def async_setup_entry(hass, entry: config_entries.ConfigEntry):
    """Set up Salus from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    _LOGGER.info("Setting up Salus integration")
    _LOGGER.debug("Configuration username: %s", username)

    devices: list[SalusDevice] = []
    for index in range(1, 5):
        device_id = f"{random.randint(0, 99999999):08d}"
        devices.append(SalusDevice(device_id, f"Salus Device {index}"))

    hass.data[DOMAIN][entry.entry_id] = {
        "devices": devices,
        "username": username,
        "password": password,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Salus integration setup complete")
    return True


async def async_unload_entry(hass, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
