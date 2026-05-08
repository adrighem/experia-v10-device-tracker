"""Binary sensor platform for ExperiaBox v10."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from typing import Any

from .const import DOMAIN
from .coordinator import ExperiaBoxV10Coordinator, ExperiaBoxV10Data
from .entity import ExperiaBoxV10Entity


class ExperiaBoxV10BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing ExperiaBox v10 binary sensor entities."""

    def __init__(
        self,
        is_on_fn: Callable[[ExperiaBoxV10Data], bool | None],
        **kwargs: Any,
    ) -> None:
        """Initialize the binary sensor description."""
        super().__init__(**kwargs)
        self.is_on_fn = is_on_fn


BINARY_SENSOR_TYPES: tuple[ExperiaBoxV10BinarySensorEntityDescription, ...] = (
    ExperiaBoxV10BinarySensorEntityDescription(
        key="connectivity",
        name="Connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda data: data.wan_info.connected,
    ),
    ExperiaBoxV10BinarySensorEntityDescription(
        key="new_device_detected",
        name="New Device Detected",
        device_class=BinarySensorDeviceClass.SAFETY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.new_device_detected,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ExperiaBox v10 binary sensor."""
    coordinator: ExperiaBoxV10Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        ExperiaBoxV10BinarySensor(coordinator, description)
        for description in BINARY_SENSOR_TYPES
    )


class ExperiaBoxV10BinarySensor(ExperiaBoxV10Entity, BinarySensorEntity):
    """Represent an ExperiaBox v10 binary sensor."""

    entity_description: ExperiaBoxV10BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: ExperiaBoxV10Coordinator,
        description: ExperiaBoxV10BinarySensorEntityDescription,
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
        return self.entity_description.is_on_fn(self.coordinator.data)
