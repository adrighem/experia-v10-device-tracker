"""Test the ExperiaBox v10 sensor platform."""
from unittest.mock import MagicMock, patch
import pytest

from custom_components.experiaboxv10.coordinator import (
    ExperiaBoxV10Coordinator,
    ExperiaBoxV10Data,
)
from custom_components.experiaboxv10.sensor import ExperiaBoxV10Sensor, SENSOR_TYPES
from custom_components.experiaboxv10.api import Device, RouterInfo, WanInfo, TrafficInfo

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

def test_sensor_properties(coordinator):
    """Test sensor entity properties."""
    mock_router_info = RouterInfo("H369A", "V1.0", "V10.C.26.04", "SN1", 3600)
    mock_wan_info = WanInfo("8.8.8.8", True, "Up")
    mock_traffic_info = TrafficInfo(1000, 2000, 10, 20)
    coordinator.data = ExperiaBoxV10Data(
        devices=[Device("M1", "D1", "1.1.1.1")],
        router_info=mock_router_info,
        wan_info=mock_wan_info,
        traffic_info=mock_traffic_info,
        guest_wifi_enabled=True,
        throughput_down=200.0,
        throughput_up=100.0
    )
    
    # Test Uptime
    uptime_sensor = ExperiaBoxV10Sensor(coordinator, SENSOR_TYPES[0])
    assert uptime_sensor.native_value == 3600
    
    # Test External IP
    ip_sensor = ExperiaBoxV10Sensor(coordinator, SENSOR_TYPES[1])
    assert ip_sensor.native_value == "8.8.8.8"
    
    # Test Data Received
    received_sensor = ExperiaBoxV10Sensor(coordinator, SENSOR_TYPES[3])
    assert received_sensor.native_value == 2000
    
    # Test Download Speed
    down_sensor = ExperiaBoxV10Sensor(coordinator, SENSOR_TYPES[5])
    assert down_sensor.native_value == 200.0
    
    # Test Client Count
    client_sensor = ExperiaBoxV10Sensor(coordinator, SENSOR_TYPES[7])
    assert client_sensor.native_value == 1
