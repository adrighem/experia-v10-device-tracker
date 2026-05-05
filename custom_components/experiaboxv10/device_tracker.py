"""Support for ZTE H369A router."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ExperiaBoxV10Coordinator
from .api import Device
from .entity import ExperiaBoxV10Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ExperiaBox v10 tracker."""
    coordinator: ExperiaBoxV10Coordinator = hass.data[DOMAIN][entry.entry_id]

    tracked: set[str] = set()

    @callback
    def async_update_entities() -> None:
        """Add new entities when they are discovered."""
        new_entities = []
        for device in coordinator.data.devices:
            if device.mac not in tracked:
                new_entities.append(
                    ExperiaBoxV10DeviceScannerEntity(coordinator, device.mac)
                )
                tracked.add(device.mac)

        if new_entities:
            async_add_entities(new_entities)

    # Initial update
    async_update_entities()

    # Listen for future updates
    entry.async_on_unload(coordinator.async_add_listener(async_update_entities))


class ExperiaBoxV10DeviceScannerEntity(ExperiaBoxV10Entity, ScannerEntity):
    """Represent a tracked device."""

    def __init__(self, coordinator: ExperiaBoxV10Coordinator, mac: str) -> None:
        """Initialize the device."""
        super().__init__(coordinator)
        self._mac = mac

    @property
    def _device(self) -> Device | None:
        """Helper to get device from coordinator."""
        for device in self.coordinator.data.devices:
            if device.mac == self._mac:
                return device
        return None

    @property
    def name(self) -> str | None:
        """Return the name of the device."""
        device = self._device
        if device and device.name:
            return device.name
        return self._mac

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._mac

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        device = self._device
        return device.active if device else False

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.ROUTER

    @property
    def mac_address(self) -> str:
        """Return the mac address."""
        return self._mac

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        device = self._device
        if device:
            return {"ip": device.ip}
        return {}
