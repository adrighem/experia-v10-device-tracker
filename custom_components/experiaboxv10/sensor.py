"""Sensor platform for ExperiaBox v10."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfInformation, UnitOfDataRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ExperiaBoxV10Coordinator
from .entity import ExperiaBoxV10Entity

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="uptime",
        name="Uptime",
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="s",
    ),
    SensorEntityDescription(
        key="external_ip",
        name="External IP",
        icon="mdi:ip",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="link_status",
        name="WAN Link Status",
        icon="mdi:lan-connect",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="bytes_received",
        name="Data Received",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="bytes_sent",
        name="Data Sent",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="throughput_down",
        name="Download Speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="throughput_up",
        name="Upload Speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="client_count",
        name="Active Clients",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="last_new_device",
        name="Last New Device",
        icon="mdi:account-alert",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ExperiaBox v10 sensor."""
    coordinator: ExperiaBoxV10Coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ExperiaBoxV10Sensor(coordinator, description) for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class ExperiaBoxV10Sensor(ExperiaBoxV10Entity, SensorEntity):
    """Represent an ExperiaBox v10 sensor."""

    def __init__(
        self,
        coordinator: ExperiaBoxV10Coordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.data.router_info.serial_number}_{description.key}"
        )

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        if self.entity_description.key == "uptime":
            return self.coordinator.data.router_info.uptime
        if self.entity_description.key == "external_ip":
            return self.coordinator.data.wan_info.external_ip
        if self.entity_description.key == "link_status":
            return self.coordinator.data.wan_info.link_status
        if self.entity_description.key == "bytes_received":
            return self.coordinator.data.traffic_info.bytes_received
        if self.entity_description.key == "bytes_sent":
            return self.coordinator.data.traffic_info.bytes_sent
        if self.entity_description.key == "throughput_down":
            return self.coordinator.data.throughput_down
        if self.entity_description.key == "throughput_up":
            return self.coordinator.data.throughput_up
        if self.entity_description.key == "client_count":
            return len([d for d in self.coordinator.data.devices if d.active])
        if self.entity_description.key == "last_new_device":
            return self.coordinator.data.last_new_device
        return None
