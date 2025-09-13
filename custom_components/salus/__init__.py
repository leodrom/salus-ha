"""Salus integration."""

from __future__ import annotations

import logging

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

PLATFORMS = ["climate", "sensor"]

DOMAIN = "salus"


_LOGGER = logging.getLogger(__name__)


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


async def async_setup(hass, config):
    """Set up the Salus integration (placeholder for YAML support)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, entry):
    """Set up Salus from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    _LOGGER.info("Setting up Salus integration")
    _LOGGER.debug("Configuration username: %s", username)

    devices = [
        SalusDevice("device_1", "Salus Device 1"),
        SalusDevice("device_2", "Salus Device 2"),
        SalusDevice("device_3", "Salus Device 3"),
        SalusDevice("device_4", "Salus Device 4"),
    ]

    hass.data[DOMAIN][entry.entry_id] = {
        "devices": devices,
        "username": username,
        "password": password,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Salus integration setup complete")
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
