"""Salus climate platform."""

from __future__ import annotations

import logging

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo

from . import DOMAIN, SalusDevice


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Salus climate entities from config entry."""
    _LOGGER.info("Setting up Salus climate entity")
    data = hass.data[DOMAIN][entry.entry_id]
    devices: list[SalusDevice] = data["devices"]
    entities = [SalusThermostat(device) for device in devices]
    async_add_entities(entities)


class SalusThermostat(ClimateEntity):
    """Representation of a dummy Salus thermostat."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

    def __init__(self, device: SalusDevice) -> None:
        self._device = device
        self._attr_name = device.name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.id)},
            name=device.name,
            manufacturer="Salus",
        )

    @property
    def unique_id(self) -> str:
        return self._device.id

    async def async_added_to_hass(self) -> None:
        self._device.register_listener(self.async_write_ha_state)

    @property
    def hvac_mode(self) -> HVACMode:
        return self._device.hvac_mode

    @property
    def current_temperature(self) -> float:
        return self._device.room_temperature

    @property
    def target_temperature(self) -> float:
        return self._device.target_temperature

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        _LOGGER.info("Setting HVAC mode to %s", hvac_mode)
        self._device.hvac_mode = hvac_mode
        self._device._notify()

    async def async_set_temperature(self, **kwargs) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            _LOGGER.info("Setting target temperature to %s", temperature)
            self._device.target_temperature = temperature
            self._device._notify()
