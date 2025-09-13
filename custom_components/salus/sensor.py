"""Salus sensor platform."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature

from . import DOMAIN, SalusDevice


_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Salus room temperature sensors."""
    _LOGGER.info("Setting up Salus room temperature sensors")
    devices: list[SalusDevice] = hass.data[DOMAIN]["devices"]
    sensors = [SalusRoomTemperatureSensor(device) for device in devices]
    async_add_entities(sensors)


class SalusRoomTemperatureSensor(SensorEntity):
    """Dummy sensor for the room temperature."""

    def __init__(self, device: SalusDevice) -> None:
        self._device = device
        self._attr_name = f"{device.name} Room Temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    async def async_added_to_hass(self) -> None:
        self._device.register_listener(self.async_write_ha_state)

    @property
    def native_value(self) -> float:
        """Return the device room temperature."""
        temperature = self._device.room_temperature
        _LOGGER.debug(
            "Reporting room temperature %s for %s", temperature, self._device.name
        )
        return temperature

    @property
    def unique_id(self) -> str:
        return f"{self._device.id}_temperature"

    @property
    def device_info(self) -> dict:
        """Return device information for this sensor."""
        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.name,
            "manufacturer": "Salus",
        }
