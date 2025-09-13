"""Salus sensor platform."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature


_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Salus room temperature sensor."""
    _LOGGER.info("Setting up Salus room temperature sensor")
    async_add_entities([SalusRoomTemperatureSensor()])


class SalusRoomTemperatureSensor(SensorEntity):
    """Dummy sensor for the room temperature."""

    _attr_name = "Salus Room Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> float:
        """Return a constant room temperature."""
        temperature = 23.0
        _LOGGER.debug("Reporting room temperature %s", temperature)
        return temperature
