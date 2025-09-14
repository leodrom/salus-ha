"""Salus sensor platform."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.components.climate.const import HVACMode

from . import DOMAIN, SalusDevice


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Salus room temperature sensors."""
    _LOGGER.info("Setting up Salus room temperature sensors")
    devices: list[SalusDevice] = hass.data[DOMAIN][entry.entry_id]["devices"]
    token: str = hass.data[DOMAIN][entry.entry_id]["token"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    sensors = []
    for device in devices:
        sensors.append(SalusRoomTemperatureSensor(device, api))
        sensors.append(SalusBatterySensor(device, api))
    sensors.append(SalusTokenSensor(token))
    async_add_entities(sensors)


class SalusRoomTemperatureSensor(SensorEntity):
    """Sensor for the room temperature."""

    def __init__(self, device: SalusDevice, api) -> None:
        self._device = device
        self._api = api
        self._attr_name = f"{device.name} Room Temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    async def async_added_to_hass(self) -> None:
        self._device.register_listener(self.async_write_ha_state)

    async def async_update(self) -> None:
        info = await self.hass.async_add_executor_job(
            self._api.get_device_info, self._device.id
        )
        self._device.room_temperature = info.current_temperature
        self._device.target_temperature = info.target_temperature
        self._device.hvac_mode = (
            HVACMode.HEAT if info.status == "on" else HVACMode.OFF
        )
        self._device._notify()

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
            "serial_number": self._device.id,
        }


class SalusBatterySensor(SensorEntity):
    """Sensor for the battery level."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, device: SalusDevice, api) -> None:
        self._device = device
        self._api = api
        self._attr_name = f"{device.name} Battery"
        self._battery: int | None = None

    async def async_update(self) -> None:
        data = await self.hass.async_add_executor_job(
            self._api.check_device_battery, self._device.id
        )
        if data:
            self._battery = (
                data.get("battery")
                or data.get("battery_level")
                or data.get("batteryLevel")
            )
        else:
            self._battery = None

    @property
    def native_value(self):
        return self._battery

    @property
    def unique_id(self) -> str:
        return f"{self._device.id}_battery"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.name,
            "manufacturer": "Salus",
            "serial_number": self._device.id,
        }


class SalusTokenSensor(SensorEntity):
    """Sensor exposing the security token."""

    _attr_icon = "mdi:key"

    def __init__(self, token: str) -> None:
        self._token = token
        self._attr_name = "Salus Security Token"

    @property
    def unique_id(self) -> str:
        return "salus_security_token"

    @property
    def native_value(self) -> str:
        return self._token
