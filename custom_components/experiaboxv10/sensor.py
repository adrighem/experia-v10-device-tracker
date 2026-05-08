"""Sensor platform for ExperiaBox v10."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ExperiaBoxV10Coordinator, ExperiaBoxV10Data
from .entity import ExperiaBoxV10Entity


@dataclass(kw_only=True, frozen=True)
class ExperiaBoxV10SensorEntityDescription(SensorEntityDescription):
    """Class describing ExperiaBox v10 sensor entities."""

    value_fn: Callable[[ExperiaBoxV10Data], str | int | float | None]
    attributes_fn: Callable[[ExperiaBoxV10Data], dict[str, Any]] | None = None


SENSOR_TYPES: tuple[ExperiaBoxV10SensorEntityDescription, ...] = (
    ExperiaBoxV10SensorEntityDescription(
        key="uptime",
        name="Uptime",
        native_unit_of_measurement="s",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.router_info.uptime,
    ),
    ExperiaBoxV10SensorEntityDescription(
        key="external_ip",
        name="External IP",
        icon="mdi:ip",
        value_fn=lambda data: data.wan_info.external_ip,
    ),
    ExperiaBoxV10SensorEntityDescription(
        key="link_status",
        name="WAN Link Status",
        icon="mdi:lan-connect",
        value_fn=lambda data: data.wan_info.link_status,
    ),
    ExperiaBoxV10SensorEntityDescription(
        key="bytes_received",
        name="Data Received",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.traffic_info.bytes_received,
    ),
    ExperiaBoxV10SensorEntityDescription(
        key="bytes_sent",
        name="Data Sent",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.traffic_info.bytes_sent,
    ),
    ExperiaBoxV10SensorEntityDescription(
        key="throughput_down",
        name="Download Speed",
        native_unit_of_measurement="B/s",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.throughput_down,
    ),
    ExperiaBoxV10SensorEntityDescription(
        key="throughput_up",
        name="Upload Speed",
        native_unit_of_measurement="B/s",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.throughput_up,
    ),
    ExperiaBoxV10SensorEntityDescription(
        key="client_count",
        name="Active Clients",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len([d for d in data.devices if d.active]),
        attributes_fn=lambda data: {
            "total_devices": len(data.devices),
            "first_device": data.devices[0].mac if data.devices else None,
        },
    ),
    ExperiaBoxV10SensorEntityDescription(
        key="last_new_device",
        name="Last New Device",
        icon="mdi:account-plus",
        value_fn=lambda data: data.last_new_device,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ExperiaBox v10 sensors."""
    coordinator: ExperiaBoxV10Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ExperiaBoxV10Sensor(coordinator, description) for description in SENSOR_TYPES
    )


class ExperiaBoxV10Sensor(ExperiaBoxV10Entity, SensorEntity):
    """Represent an ExperiaBox v10 sensor."""

    entity_description: ExperiaBoxV10SensorEntityDescription

    def __init__(
        self,
        coordinator: ExperiaBoxV10Coordinator,
        description: ExperiaBoxV10SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.data.router_info.serial_number}_{description.key}"

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.entity_description.attributes_fn:
            return self.entity_description.attributes_fn(self.coordinator.data)
        return None
