"""DataUpdateCoordinator for ExperiaBox v10."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .const import DOMAIN, CONF_TRACK_WIRED_DEVICES
from .api import ExperiaBoxV10Api, Device

_LOGGER = logging.getLogger(__name__)

class ExperiaBoxV10Coordinator(DataUpdateCoordinator[list[Device]]):
    """Class to manage fetching ExperiaBox v10 data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.api = ExperiaBoxV10Api(
            async_get_clientsession(hass),
            entry.data[CONF_HOST],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        self.track_wired_devices = entry.options.get(CONF_TRACK_WIRED_DEVICES, False)

    async def _async_update_data(self) -> list[Device]:
        """Update data via library."""
        try:
            return await self.api.get_devices(self.track_wired_devices)
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with ExperiaBox: {exception}") from exception
