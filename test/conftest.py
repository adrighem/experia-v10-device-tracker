"""Common test configuration and mocks."""
import sys
from unittest.mock import MagicMock
from types import ModuleType
from typing import Any

# Create dummy modules
def mock_module(name):
    m = ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m

homeassistant = mock_module("homeassistant")
homeassistant.core = mock_module("homeassistant.core")
homeassistant.const = mock_module("homeassistant.const")
homeassistant.exceptions = mock_module("homeassistant.exceptions")
homeassistant.config_entries = mock_module("homeassistant.config_entries")
homeassistant.data_entry_flow = mock_module("homeassistant.data_entry_flow")
homeassistant.helpers = mock_module("homeassistant.helpers")
homeassistant.helpers.aiohttp_client = mock_module("homeassistant.helpers.aiohttp_client")
homeassistant.helpers.update_coordinator = mock_module("homeassistant.helpers.update_coordinator")
homeassistant.helpers.entity_platform = mock_module("homeassistant.helpers.entity_platform")
homeassistant.helpers.entity = mock_module("homeassistant.helpers.entity")
homeassistant.components = mock_module("homeassistant.components")
homeassistant.components.device_tracker = mock_module("homeassistant.components.device_tracker")
homeassistant.components.sensor = mock_module("homeassistant.components.sensor")
homeassistant.components.binary_sensor = mock_module("homeassistant.components.binary_sensor")
homeassistant.components.button = mock_module("homeassistant.components.button")
homeassistant.components.switch = mock_module("homeassistant.components.switch")
voluptuous = mock_module("voluptuous")

# Mock constants
homeassistant.const.CONF_HOST = "host"
homeassistant.const.CONF_USERNAME = "username"
homeassistant.const.CONF_PASSWORD = "password"

class UnitOfInformation:
    BYTES = "B"
homeassistant.const.UnitOfInformation = UnitOfInformation

class UnitOfDataRate:
    BYTES_PER_SECOND = "B/s"
homeassistant.const.UnitOfDataRate = UnitOfDataRate

class Platform:
    DEVICE_TRACKER = "device_tracker"
    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"
    BUTTON = "button"
    SWITCH = "switch"
homeassistant.const.Platform = Platform

class EntityCategory:
    DIAGNOSTIC = "diagnostic"
    CONFIG = "config"
homeassistant.const.EntityCategory = EntityCategory

class MockEntity:
    @property
    def unique_id(self):
        return getattr(self, "_attr_unique_id", None)

class ScannerEntity(MockEntity): pass
homeassistant.components.device_tracker.ScannerEntity = ScannerEntity
homeassistant.components.device_tracker.SourceType = MagicMock
homeassistant.components.device_tracker.SourceType.ROUTER = "router"

class SensorDeviceClass:
    DURATION = "duration"
    DATA_SIZE = "data_size"
    DATA_RATE = "data_rate"
homeassistant.components.sensor.SensorDeviceClass = SensorDeviceClass
class SensorStateClass:
    TOTAL_INCREASING = "total_increasing"
    MEASUREMENT = "measurement"
homeassistant.components.sensor.SensorStateClass = SensorStateClass
class SensorEntity(MockEntity): pass
homeassistant.components.sensor.SensorEntity = SensorEntity
class SensorEntityDescription:
    def __init__(self, **kwargs):
        for k, v in kwargs.items(): setattr(self, k, v)
homeassistant.components.sensor.SensorEntityDescription = SensorEntityDescription

class BinarySensorDeviceClass:
    CONNECTIVITY = "connectivity"
    SAFETY = "safety"
homeassistant.components.binary_sensor.BinarySensorDeviceClass = BinarySensorDeviceClass
class BinarySensorEntity(MockEntity): pass
homeassistant.components.binary_sensor.BinarySensorEntity = BinarySensorEntity
class BinarySensorEntityDescription:
    def __init__(self, **kwargs):
        for k, v in kwargs.items(): setattr(self, k, v)
homeassistant.components.binary_sensor.BinarySensorEntityDescription = BinarySensorEntityDescription

class ButtonEntity(MockEntity): pass
homeassistant.components.button.ButtonEntity = ButtonEntity
class ButtonEntityDescription:
    def __init__(self, **kwargs):
        for k, v in kwargs.items(): setattr(self, k, v)
homeassistant.components.button.ButtonEntityDescription = ButtonEntityDescription

class SwitchEntity(MockEntity): pass
homeassistant.components.switch.SwitchEntity = SwitchEntity
class SwitchEntityDescription:
    def __init__(self, **kwargs):
        for k, v in kwargs.items(): setattr(self, k, v)
homeassistant.components.switch.SwitchEntityDescription = SwitchEntityDescription

class DataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = None
    def __class_getitem__(cls, _): return cls
    async def async_config_entry_first_refresh(self): pass
    def async_add_listener(self, listener): return lambda: None
    async def async_request_refresh(self): pass

homeassistant.helpers.update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
homeassistant.helpers.update_coordinator.UpdateFailed = Exception

class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator
    def __class_getitem__(cls, _): return cls
homeassistant.helpers.update_coordinator.CoordinatorEntity = CoordinatorEntity

class ConfigFlow:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
homeassistant.config_entries.ConfigFlow = ConfigFlow

class OptionsFlow:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
homeassistant.config_entries.OptionsFlow = OptionsFlow

class ConfigEntry: pass
homeassistant.config_entries.ConfigEntry = ConfigEntry
homeassistant.config_entries.ConfigFlowResult = Any

class DeviceInfo(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
homeassistant.helpers.entity.DeviceInfo = DeviceInfo

homeassistant.core.HomeAssistant = MagicMock
homeassistant.core.callback = lambda x: x

homeassistant.helpers.aiohttp_client.async_get_clientsession = MagicMock()

homeassistant.data_entry_flow.ConfigFlowResult = Any

homeassistant.helpers.entity_platform.AddEntitiesCallback = Any

voluptuous.Schema = MagicMock
voluptuous.Required = MagicMock
voluptuous.Optional = MagicMock
