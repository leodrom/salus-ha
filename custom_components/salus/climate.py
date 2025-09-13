"""Salus climate platform."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from . import DOMAIN, SalusDevice


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Salus climate entity."""
    device: SalusDevice = hass.data[DOMAIN]["device"]
    entity = SalusThermostat(device)
    async_add_entities([entity])


class SalusThermostat(ClimateEntity):
    """Representation of a dummy Salus thermostat."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.OFF]
    _attr_name = "Salus Thermostat"

    def __init__(self, device: SalusDevice) -> None:
        self._device = device

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
        self._device.hvac_mode = hvac_mode
        self._device._notify()

    async def async_set_temperature(self, **kwargs) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            self._device.target_temperature = temperature
            self._device._notify()
