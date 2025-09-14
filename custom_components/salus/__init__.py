"""Salus integration."""

from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import ConfigEntryAuthFailed
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from .salus import Salus

DOMAIN = "salus"


_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class SalusDevice:
    """Representation of a Salus thermostat."""

    def __init__(self, device_id: str, name: str, code: str = "", online: bool = False) -> None:
        self.id = device_id
        self.name = name
        self.code = code
        self.online = online
        self.room_temperature: float = 0.0
        self.target_temperature: float = 0.0
        self.hvac_mode: HVACMode = HVACMode.HEAT
        self._listeners: list[callable] = []

    def register_listener(self, callback) -> None:
        """Register a callback to be notified on state changes."""
        self._listeners.append(callback)

    def _notify(self) -> None:
        for callback in self._listeners:
            callback()


PLATFORMS = ["climate", "sensor"]


async def async_setup(hass, config):
    """Set up the Salus integration."""
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=config[DOMAIN],
            )
        )
    return True


async def async_setup_entry(hass, entry: config_entries.ConfigEntry):
    """Set up Salus from a config entry."""
    username = entry.options.get(CONF_USERNAME, entry.data[CONF_USERNAME])
    password = entry.options.get(CONF_PASSWORD, entry.data[CONF_PASSWORD])

    _LOGGER.info("Setting up Salus integration")
    _LOGGER.debug("Configuration username: %s", username)

    api = Salus()

    def _login_and_fetch():
        api.do_login(username, password)
        if not api.check_login_error_status():
            raise ConfigEntryAuthFailed(api.error_message)
        token = api.parse_token()
        devices_raw = api.parse_devices_page()
        devices_detailed = []
        for dev in devices_raw:
            try:
                detailed = api.get_device_info(dev.id)
                # Preserve the friendly name parsed from the devices page
                detailed.name = dev.name or detailed.name
                devices_detailed.append(detailed)
            except Exception as err:  # pragma: no cover - network issues
                _LOGGER.error("Unable to get info for device %s: %s", dev.id, err)
        return token, devices_detailed

    try:
        token, api_devices = await hass.async_add_executor_job(_login_and_fetch)
    except ConfigEntryAuthFailed:
        _LOGGER.error("Invalid credentials provided for Salus")
        raise
    except Exception as err:  # pragma: no cover - network issues
        _LOGGER.error("Error communicating with Salus: %s", err)
        return False

    _LOGGER.info("Received security token %s", token)

    devices: list[SalusDevice] = []
    for api_dev in api_devices:
        device = SalusDevice(api_dev.id, api_dev.name, api_dev.code, api_dev.online)
        device.room_temperature = api_dev.current_temperature
        device.target_temperature = api_dev.target_temperature
        device.hvac_mode = (
            HVACMode.HEAT if api_dev.status == "on" else HVACMode.OFF
        )
        devices.append(device)

    hass.data[DOMAIN][entry.entry_id] = {
        "devices": devices,
        "username": username,
        "password": password,
        "token": token,
        "api": api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info(
        "Salus integration setup complete with %s device(s)", len(devices)
    )
    return True


async def async_unload_entry(hass, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
