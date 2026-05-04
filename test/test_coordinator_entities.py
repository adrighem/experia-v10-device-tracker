"""Test the ExperiaBox v10 Coordinator and Entities."""
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from datetime import timedelta

from custom_components.experiaboxv10.coordinator import (
    ExperiaBoxV10Coordinator,
    ExperiaBoxV10Data,
)
from custom_components.experiaboxv10.device_tracker import ExperiaBoxV10DeviceScannerEntity
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

def test_coordinator_init(coordinator):
    """Test coordinator initialization."""
    assert coordinator.name == "experiaboxv10"
    assert coordinator.update_interval == timedelta(seconds=30)

@pytest.mark.asyncio
async def test_coordinator_update_data(coordinator):
    """Test coordinator data update."""
    mock_devices = [Device("MAC1", "Name1", "1.1.1.1")]
    mock_router_info = RouterInfo("H369A", "V1.0", "V10.C.26.04", "SN1", 100)
    mock_wan_info = WanInfo("8.8.8.8", True, "Up")
    mock_traffic_info = TrafficInfo(1000, 2000, 10, 20)
    
    coordinator.api.get_devices = AsyncMock(return_value=mock_devices)
    coordinator.api.get_router_info = AsyncMock(return_value=mock_router_info)
    coordinator.api.get_wan_info = AsyncMock(return_value=mock_wan_info)
    coordinator.api.get_traffic_info = AsyncMock(return_value=mock_traffic_info)
    coordinator.api.get_guest_wifi_enabled = AsyncMock(return_value=True)
    
    data = await coordinator._async_update_data()
    assert data.devices == mock_devices
    assert data.router_info == mock_router_info
    assert data.wan_info == mock_wan_info
    assert data.traffic_info == mock_traffic_info
    assert data.guest_wifi_enabled is True

@pytest.mark.asyncio
async def test_coordinator_throughput(coordinator):
    """Test throughput calculation in coordinator."""
    mock_router_info = RouterInfo("H369A", "V1.0", "V10.C.26.04", "SN1", 100)
    mock_wan_info = WanInfo("8.8.8.8", True, "Up")
    
    # First update
    mock_traffic_1 = TrafficInfo(1000, 2000, 10, 20)
    coordinator.api.get_devices = AsyncMock(return_value=[])
    coordinator.api.get_router_info = AsyncMock(return_value=mock_router_info)
    coordinator.api.get_wan_info = AsyncMock(return_value=mock_wan_info)
    coordinator.api.get_traffic_info = AsyncMock(return_value=mock_traffic_1)
    coordinator.api.get_guest_wifi_enabled = AsyncMock(return_value=False)
    
    with patch("time.monotonic", return_value=100.0):
        data1 = await coordinator._async_update_data()
        assert data1.throughput_down == 0
        assert data1.throughput_up == 0
    
    # Second update after 10 seconds
    mock_traffic_2 = TrafficInfo(2000, 4000, 20, 40) # +1000 sent, +2000 received
    coordinator.api.get_traffic_info = AsyncMock(return_value=mock_traffic_2)
    
    with patch("time.monotonic", return_value=110.0):
        data2 = await coordinator._async_update_data()
        # (4000 - 2000) / 10 = 200 bytes/s
        assert data2.throughput_down == 200.0
        # (2000 - 1000) / 10 = 100 bytes/s
        assert data2.throughput_up == 100.0

@pytest.mark.asyncio
async def test_new_device_detection(coordinator):
    """Test new device detection logic."""
    mock_router_info = RouterInfo("H369A", "V1.0", "V10.C.26.04", "SN1", 100)
    mock_wan_info = WanInfo("8.8.8.8", True, "Up")
    mock_traffic = TrafficInfo(1000, 2000, 10, 20)
    
    # 1. First poll: known devices populated
    coordinator.api.get_devices = AsyncMock(return_value=[Device("MAC1", "Device1", "1.1.1.1")])
    coordinator.api.get_router_info = AsyncMock(return_value=mock_router_info)
    coordinator.api.get_wan_info = AsyncMock(return_value=mock_wan_info)
    coordinator.api.get_traffic_info = AsyncMock(return_value=mock_traffic)
    coordinator.api.get_guest_wifi_enabled = AsyncMock(return_value=False)
    
    with patch("time.monotonic", return_value=100.0):
        data1 = await coordinator._async_update_data()
        assert data1.new_device_detected is False
        assert data1.last_new_device is None
    
    # 2. Second poll: new device joins
    coordinator.api.get_devices = AsyncMock(return_value=[
        Device("MAC1", "Device1", "1.1.1.1"),
        Device("MAC2", "NewDevice", "1.1.1.2")
    ])
    
    with patch("time.monotonic", return_value=200.0):
        data2 = await coordinator._async_update_data()
        assert data2.new_device_detected is True
        assert data2.last_new_device == "NewDevice (MAC2)"
        
    # 3. Third poll: after 6 minutes (360s), alert should be OFF
    with patch("time.monotonic", return_value=600.0):
        data3 = await coordinator._async_update_data()
        assert data3.new_device_detected is False
        assert data3.last_new_device == "NewDevice (MAC2)" # Details remain

def test_entity_properties(coordinator):
    """Test device tracker entity properties."""
    mac = "00:11:22:33:44:55"
    mock_router_info = RouterInfo("H369A", "V1.0", "V10.C.26.04", "SN1", 100)
    mock_wan_info = WanInfo("8.8.8.8", True, "Up")
    mock_traffic_info = TrafficInfo(1000, 2000, 10, 20)
    coordinator.data = ExperiaBoxV10Data(
        [Device(mac, "Test Device", "192.168.1.10")],
        mock_router_info,
        mock_wan_info,
        mock_traffic_info,
        True
    )
    
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
    mock_router_info = RouterInfo("H369A", "V1.0", "V10.C.26.04", "SN1", 100)
    mock_wan_info = WanInfo("8.8.8.8", True, "Up")
    mock_traffic_info = TrafficInfo(1000, 2000, 10, 20)
    coordinator.data = ExperiaBoxV10Data([], mock_router_info, mock_wan_info, mock_traffic_info, True) # No devices
    
    entity = ExperiaBoxV10DeviceScannerEntity(coordinator, mac)
    
    assert entity.is_connected is False
    assert entity.name == mac # Fallback to MAC if not in data
    assert entity.extra_state_attributes == {}
