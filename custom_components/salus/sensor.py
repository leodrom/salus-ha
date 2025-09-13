"""Salus sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Salus room temperature sensor."""
    async_add_entities([SalusRoomTemperatureSensor()])


class SalusRoomTemperatureSensor(SensorEntity):
    """Dummy sensor for the room temperature."""

    _attr_name = "Salus Room Temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS

    @property
    def native_value(self) -> float:
        """Return a constant room temperature."""
        return 23.0
