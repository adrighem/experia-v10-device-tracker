"""Test the ExperiaBox v10 binary sensor platform."""
from unittest.mock import MagicMock, patch
import pytest

from custom_components.experiaboxv10.coordinator import (
    ExperiaBoxV10Coordinator,
    ExperiaBoxV10Data,
)
from custom_components.experiaboxv10.binary_sensor import (
    ExperiaBoxV10BinarySensor,
    BINARY_SENSOR_TYPES,
)
from custom_components.experiaboxv10.api import RouterInfo, WanInfo, TrafficInfo

@pytest.fixture
def hass():
    return MagicMock()

@pytest.fixture
def entry():
    mock_entry = MagicMock()
    mock_entry.data = {"host": "1.2.3.4", "username": "u", "password": "p"}
    mock_entry.options = {}
    return mock_entry

@pytest.fixture
def coordinator(hass, entry):
    with patch("custom_components.experiaboxv10.coordinator.async_get_clientsession"):
        return ExperiaBoxV10Coordinator(hass, entry)

def test_binary_sensor_properties(coordinator):
    """Test binary sensor entity properties."""
    mock_router_info = RouterInfo("H369A", "V1.0", "V10.C.26.04", "SN1", 3600)
    mock_wan_info = WanInfo("8.8.8.8", True, "Up")
    mock_traffic_info = TrafficInfo(1000, 2000, 10, 20)
    coordinator.data = ExperiaBoxV10Data([], mock_router_info, mock_wan_info, mock_traffic_info)
    
    description = BINARY_SENSOR_TYPES[0] # Connectivity
    sensor = ExperiaBoxV10BinarySensor(coordinator, description)
    
    assert sensor.unique_id == "SN1_connectivity"
    assert sensor.is_on is True
    assert sensor.entity_description.name == "Connectivity"
    
    # Test OFF state
    mock_wan_info_off = WanInfo("0.0.0.0", False, "Down")
    coordinator.data = ExperiaBoxV10Data([], mock_router_info, mock_wan_info_off, mock_traffic_info)
    assert sensor.is_on is False
