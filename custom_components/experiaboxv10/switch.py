"""Switch platform for ExperiaBox v10."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ExperiaBoxV10Coordinator
from .entity import ExperiaBoxV10Entity

SWITCH_TYPES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="guest_wifi",
        name="Guest Wi-Fi",
        icon="mdi:wifi-lock",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ExperiaBox v10 switch."""
    coordinator: ExperiaBoxV10Coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ExperiaBoxV10Switch(coordinator, description) for description in SWITCH_TYPES
    ]

    async_add_entities(entities)


class ExperiaBoxV10Switch(ExperiaBoxV10Entity, SwitchEntity):
    """Represent an ExperiaBox v10 switch."""

    def __init__(
        self,
        coordinator: ExperiaBoxV10Coordinator,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.data.router_info.serial_number}_{description.key}"
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self.entity_description.key == "guest_wifi":
            return self.coordinator.data.guest_wifi_enabled
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if self.entity_description.key == "guest_wifi":
            await self.coordinator.api.set_guest_wifi(True)
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        if self.entity_description.key == "guest_wifi":
            await self.coordinator.api.set_guest_wifi(False)
            await self.coordinator.async_request_refresh()
