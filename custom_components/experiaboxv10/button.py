"""Button platform for ExperiaBox v10."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import ExperiaBoxV10Api
from .const import DOMAIN
from .coordinator import ExperiaBoxV10Coordinator
from .entity import ExperiaBoxV10Entity


class ExperiaBoxV10ButtonEntityDescription(ButtonEntityDescription):
    """Class describing ExperiaBox v10 button entities."""

    def __init__(
        self,
        press_fn: Callable[[ExperiaBoxV10Api], Coroutine[Any, Any, None]],
        **kwargs: Any,
    ) -> None:
        """Initialize the button description."""
        super().__init__(**kwargs)
        self.press_fn = press_fn


BUTTON_TYPES: tuple[ExperiaBoxV10ButtonEntityDescription, ...] = (
    ExperiaBoxV10ButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart",
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda api: api.reboot(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ExperiaBox v10 button."""
    coordinator: ExperiaBoxV10Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        ExperiaBoxV10Button(coordinator, description) for description in BUTTON_TYPES
    )


class ExperiaBoxV10Button(ExperiaBoxV10Entity, ButtonEntity):
    """Represent an ExperiaBox v10 button."""

    entity_description: ExperiaBoxV10ButtonEntityDescription

    def __init__(
        self,
        coordinator: ExperiaBoxV10Coordinator,
        description: ExperiaBoxV10ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.data.router_info.serial_number}_{description.key}"
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.entity_description.press_fn(self.coordinator.api)
