"""Salus sensor platform."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo

from . import DOMAIN, SalusDevice


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Salus room temperature sensors from config entry."""
    _LOGGER.info("Setting up Salus room temperature sensors")
    data = hass.data[DOMAIN][entry.entry_id]
    devices: list[SalusDevice] = data["devices"]
    sensors = [SalusRoomTemperatureSensor(device) for device in devices]
    async_add_entities(sensors)


class SalusRoomTemperatureSensor(SensorEntity):
    """Dummy sensor for the room temperature."""

    def __init__(self, device: SalusDevice) -> None:
        self._device = device
        self._attr_name = f"{device.name} Room Temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.id)},
            name=device.name,
            manufacturer="Salus",
        )

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
