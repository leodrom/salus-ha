"""Salus sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS

from . import DOMAIN, SalusDevice


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Salus sensors."""
    device: SalusDevice = hass.data[DOMAIN]
    sensors: list[SensorEntity] = [
        SalusRoomTemperatureSensor(device),
        SalusTargetTemperatureSensor(device),
    ]
    async_add_entities(sensors)


class SalusRoomTemperatureSensor(SensorEntity):
    """Sensor for the room temperature."""

    _attr_name = "Salus Room Temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS

    def __init__(self, device: SalusDevice) -> None:
        self._device = device

    async def async_added_to_hass(self) -> None:
        self._device.register_listener(self.async_write_ha_state)

    @property
    def native_value(self) -> float:
        return self._device.room_temperature


class SalusTargetTemperatureSensor(SensorEntity):
    """Sensor for the target temperature."""

    _attr_name = "Salus Target Temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS

    def __init__(self, device: SalusDevice) -> None:
        self._device = device

    async def async_added_to_hass(self) -> None:
        self._device.register_listener(self.async_write_ha_state)

    @property
    def native_value(self) -> float:
        return self._device.target_temperature
