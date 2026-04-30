"""Common test configuration and mocks."""
import sys
from unittest.mock import MagicMock
from types import ModuleType
from typing import Any

# Create dummy modules
def mock_module(name):
    m = ModuleType(name)
    sys.modules[name] = m
    return m

homeassistant = mock_module("homeassistant")
homeassistant_core = mock_module("homeassistant.core")
homeassistant_const = mock_module("homeassistant.const")
homeassistant_exceptions = mock_module("homeassistant.exceptions")
homeassistant_config_entries = mock_module("homeassistant.config_entries")
homeassistant_data_entry_flow = mock_module("homeassistant.data_entry_flow")
homeassistant_helpers = mock_module("homeassistant.helpers")
homeassistant_helpers_aiohttp_client = mock_module("homeassistant.helpers.aiohttp_client")
homeassistant_helpers_update_coordinator = mock_module("homeassistant.helpers.update_coordinator")
homeassistant_helpers_entity_platform = mock_module("homeassistant.helpers.entity_platform")
homeassistant_components = mock_module("homeassistant.components")
homeassistant_components_device_tracker = mock_module("homeassistant.components.device_tracker")
voluptuous = mock_module("voluptuous")

# Set up attributes
homeassistant.core = homeassistant_core
homeassistant.const = homeassistant_const
homeassistant.exceptions = homeassistant_exceptions
homeassistant.config_entries = homeassistant_config_entries
homeassistant.data_entry_flow = homeassistant_data_entry_flow
homeassistant.helpers = homeassistant_helpers
homeassistant.helpers.aiohttp_client = homeassistant_helpers_aiohttp_client
homeassistant.helpers.update_coordinator = homeassistant_helpers_update_coordinator
homeassistant.helpers.entity_platform = homeassistant_helpers_entity_platform
homeassistant.components = homeassistant_components
homeassistant.components.device_tracker = homeassistant_components_device_tracker

# Mock constants
homeassistant_const.CONF_HOST = "host"
homeassistant_const.CONF_USERNAME = "username"
homeassistant_const.CONF_PASSWORD = "password"

class Platform:
    DEVICE_TRACKER = "device_tracker"
homeassistant_const.Platform = Platform

class ScannerEntity: pass
homeassistant_components_device_tracker.ScannerEntity = ScannerEntity
homeassistant_components_device_tracker.SourceType = MagicMock
homeassistant_components_device_tracker.SourceType.ROUTER = "router"

class DataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = []
    def __class_getitem__(cls, _): return cls
    async def async_config_entry_first_refresh(self): pass
    def async_add_listener(self, listener): return lambda: None

homeassistant_helpers_update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
homeassistant_helpers_update_coordinator.UpdateFailed = Exception

class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator
    def __class_getitem__(cls, _): return cls
homeassistant_helpers_update_coordinator.CoordinatorEntity = CoordinatorEntity

class ConfigFlow:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
homeassistant_config_entries.ConfigFlow = ConfigFlow

class ConfigEntry: pass
homeassistant_config_entries.ConfigEntry = ConfigEntry
homeassistant_config_entries.ConfigFlowResult = Any

class HomeAssistant: pass
homeassistant_core.HomeAssistant = HomeAssistant
homeassistant_core.callback = lambda x: x

homeassistant_helpers_aiohttp_client.async_get_clientsession = MagicMock()

homeassistant_data_entry_flow.ConfigFlowResult = Any

homeassistant_helpers_entity_platform.AddEntitiesCallback = Any

voluptuous.Schema = MagicMock
voluptuous.Required = MagicMock
