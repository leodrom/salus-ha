"""Salus integration."""

from __future__ import annotations

from homeassistant.components.climate.const import HVACMode

DOMAIN = "salus"


class SalusDevice:
    """Dummy device holding the Salus thermostat state."""

    def __init__(self) -> None:
        self.room_temperature: float = 20.0
        self.target_temperature: float = 22.0
        self.hvac_mode: HVACMode = HVACMode.AUTO
        self._listeners: list[callable] = []

    def register_listener(self, callback) -> None:
        """Register a callback to be notified on state changes."""
        self._listeners.append(callback)

    def _notify(self) -> None:
        for callback in self._listeners:
            callback()


async def async_setup(hass, config):
    """Set up the Salus integration."""
    device = SalusDevice()
    hass.data[DOMAIN] = device

    hass.helpers.discovery.load_platform("climate", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)
    return True
