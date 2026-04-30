"""Test the ExperiaBox v10 Coordinator and Entities."""
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from datetime import timedelta

from custom_components.experiaboxv10.coordinator import ExperiaBoxV10Coordinator
from custom_components.experiaboxv10.device_tracker import ExperiaBoxV10DeviceScannerEntity
from custom_components.experiaboxv10.api import Device

@pytest.fixture
def hass():
    return MagicMock()

@pytest.fixture
def entry():
    mock_entry = MagicMock()
    mock_entry.data = {"host": "1.2.3.4", "username": "u", "password": "p"}
    return mock_entry

@pytest.fixture
def coordinator(hass, entry):
    with patch("custom_components.experiaboxv10.coordinator.async_get_clientsession"):
        return ExperiaBoxV10Coordinator(hass, entry)

def test_coordinator_init(coordinator):
    """Test coordinator initialization."""
    assert coordinator.name == "experiaboxv10"
    assert coordinator.update_interval == timedelta(seconds=30)

@pytest.mark.asyncio
async def test_coordinator_update_data(coordinator):
    """Test coordinator data update."""
    mock_devices = [Device("MAC1", "Name1", "1.1.1.1")]
    coordinator.api.get_devices = AsyncMock(return_value=mock_devices)
    
    data = await coordinator._async_update_data()
    assert data == mock_devices

def test_entity_properties(coordinator):
    """Test device tracker entity properties."""
    mac = "00:11:22:33:44:55"
    coordinator.data = [Device(mac, "Test Device", "192.168.1.10")]
    
    entity = ExperiaBoxV10DeviceScannerEntity(coordinator, mac)
    
    assert entity.unique_id == mac
    assert entity.mac_address == mac
    assert entity.name == "Test Device"
    assert entity.is_connected is True
    assert entity.source_type == "router"
    assert entity.extra_state_attributes == {"ip": "192.168.1.10"}

def test_entity_disconnected(coordinator):
    """Test entity behavior when device is disconnected."""
    mac = "00:11:22:33:44:55"
    coordinator.data = [] # No devices
    
    entity = ExperiaBoxV10DeviceScannerEntity(coordinator, mac)
    
    assert entity.is_connected is False
    assert entity.name == mac # Fallback to MAC if not in data
    assert entity.extra_state_attributes == {}
