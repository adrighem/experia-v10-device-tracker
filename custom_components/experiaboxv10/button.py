"""Button platform for ExperiaBox v10."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ExperiaBoxV10Coordinator
from .entity import ExperiaBoxV10Entity

BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ExperiaBox v10 button."""
    coordinator: ExperiaBoxV10Coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ExperiaBoxV10Button(coordinator, description) for description in BUTTON_TYPES
    ]

    async_add_entities(entities)


class ExperiaBoxV10Button(ExperiaBoxV10Entity, ButtonEntity):
    """Represent an ExperiaBox v10 button."""

    def __init__(
        self,
        coordinator: ExperiaBoxV10Coordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.data.router_info.serial_number}_{description.key}"
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        if self.entity_description.key == "reboot":
            await self.coordinator.api.reboot()
