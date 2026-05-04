"""Test the ExperiaBox v10 switch platform."""
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

from custom_components.experiaboxv10.coordinator import (
    ExperiaBoxV10Coordinator,
    ExperiaBoxV10Data,
)
from custom_components.experiaboxv10.switch import ExperiaBoxV10Switch, SWITCH_TYPES
from custom_components.experiaboxv10.api import RouterInfo

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

@pytest.mark.asyncio
async def test_switch_toggle(coordinator):
    """Test switch toggle actions."""
    mock_router_info = RouterInfo("H369A", "V1.0", "V10.C.26.04", "SN1", 3600)
    coordinator.data = ExperiaBoxV10Data([], mock_router_info, None, None, True)
    
    switch = ExperiaBoxV10Switch(coordinator, SWITCH_TYPES[0])
    
    assert switch.is_on is True
    
    coordinator.api.set_guest_wifi = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    
    await switch.async_turn_off()
    coordinator.api.set_guest_wifi.assert_called_once_with(False)
    coordinator.async_request_refresh.assert_called_once()
    
    coordinator.api.set_guest_wifi.reset_mock()
    await switch.async_turn_on()
    coordinator.api.set_guest_wifi.assert_called_once_with(True)
