"""Test the ExperiaBox v10 button platform."""
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

from custom_components.experiaboxv10.coordinator import (
    ExperiaBoxV10Coordinator,
    ExperiaBoxV10Data,
)
from custom_components.experiaboxv10.button import ExperiaBoxV10Button, BUTTON_TYPES
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

@pytest.mark.asyncio
async def test_button_press(coordinator):
    """Test button press action."""
    mock_router_info = RouterInfo("H369A", "V1.0", "V10.C.26.04", "SN1", 3600)
    coordinator.data = ExperiaBoxV10Data([], mock_router_info, None, None)
    
    button = ExperiaBoxV10Button(coordinator, BUTTON_TYPES[0])
    
    coordinator.api.reboot = AsyncMock()
    await button.async_press()
    
    coordinator.api.reboot.assert_called_once()
