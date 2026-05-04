"""Binary sensor platform for ExperiaBox v10."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ExperiaBoxV10Coordinator
from .entity import ExperiaBoxV10Entity

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="connectivity",
        name="Connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="new_device_detected",
        name="New Device Detected",
        device_class=BinarySensorDeviceClass.SAFETY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ExperiaBox v10 binary sensor."""
    coordinator: ExperiaBoxV10Coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ExperiaBoxV10BinarySensor(coordinator, description)
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(entities)


class ExperiaBoxV10BinarySensor(ExperiaBoxV10Entity, BinarySensorEntity):
    """Represent an ExperiaBox v10 binary sensor."""

    def __init__(
        self,
        coordinator: ExperiaBoxV10Coordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.data.router_info.serial_number}_{description.key}"
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.entity_description.key == "connectivity":
            return self.coordinator.data.wan_info.connected
        if self.entity_description.key == "new_device_detected":
            return self.coordinator.data.new_device_detected
        return None
