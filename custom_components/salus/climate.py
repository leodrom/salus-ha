"""Salus climate platform."""

from __future__ import annotations

import logging

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from . import DOMAIN, SalusDevice


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Salus climate entity from a config entry."""
    _LOGGER.info("Setting up Salus climate entity")
    devices: list[SalusDevice] = hass.data[DOMAIN][entry.entry_id]["devices"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    entities = [SalusThermostat(device, api) for device in devices]
    async_add_entities(entities)


class SalusThermostat(ClimateEntity):
    """Representation of a dummy Salus thermostat."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

    def __init__(self, device: SalusDevice, api) -> None:
        self._device = device
        self._api = api
        self._attr_name = device.name

    @property
    def unique_id(self) -> str:
        return self._device.id

    @property
    def device_info(self) -> dict:
        """Return device information for this thermostat."""
        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.name,
            "manufacturer": "Salus",
            "serial_number": self._device.id,
        }

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
            await self.hass.async_add_executor_job(
                self._api.set_temperature, self._device.id, temperature
            )
            self._device.target_temperature = temperature
            self._device._notify()

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
