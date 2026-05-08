"""Switch platform for ExperiaBox v10."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import ExperiaBoxV10Api
from .const import DOMAIN
from .coordinator import ExperiaBoxV10Coordinator, ExperiaBoxV10Data
from .entity import ExperiaBoxV10Entity


class ExperiaBoxV10SwitchEntityDescription(SwitchEntityDescription):
    """Class describing ExperiaBox v10 switch entities."""

    def __init__(
        self,
        is_on_fn: Callable[[ExperiaBoxV10Data], bool | None],
        turn_on_fn: Callable[[ExperiaBoxV10Api], Coroutine[Any, Any, None]],
        turn_off_fn: Callable[[ExperiaBoxV10Api], Coroutine[Any, Any, None]],
        **kwargs: Any,
    ) -> None:
        """Initialize the switch description."""
        super().__init__(**kwargs)
        self.is_on_fn = is_on_fn
        self.turn_on_fn = turn_on_fn
        self.turn_off_fn = turn_off_fn


SWITCH_TYPES: tuple[ExperiaBoxV10SwitchEntityDescription, ...] = (
    ExperiaBoxV10SwitchEntityDescription(
        key="guest_wifi",
        name="Guest Wi-Fi",
        icon="mdi:wifi-lock",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda data: data.guest_wifi_enabled,
        turn_on_fn=lambda api: api.set_guest_wifi(True),
        turn_off_fn=lambda api: api.set_guest_wifi(False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ExperiaBox v10 switch."""
    coordinator: ExperiaBoxV10Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        ExperiaBoxV10Switch(coordinator, description) for description in SWITCH_TYPES
    )


class ExperiaBoxV10Switch(ExperiaBoxV10Entity, SwitchEntity):
    """Represent an ExperiaBox v10 switch."""

    entity_description: ExperiaBoxV10SwitchEntityDescription

    def __init__(
        self,
        coordinator: ExperiaBoxV10Coordinator,
        description: ExperiaBoxV10SwitchEntityDescription,
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
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.entity_description.turn_on_fn(self.coordinator.api)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.entity_description.turn_off_fn(self.coordinator.api)
        await self.coordinator.async_request_refresh()
