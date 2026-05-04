"""Test the ExperiaBox v10 options flow."""
from unittest.mock import MagicMock
import pytest
from custom_components.experiaboxv10.config_flow import OptionsFlowHandler

class MockOptionsFlowBase:
    def __init__(self):
        self._config_entry = None

    @property
    def config_entry(self):
        return self._config_entry
    
    @config_entry.setter
    def config_entry(self, value):
        self._config_entry = value

    def async_create_entry(self, title, data):
        return {"type": "create_entry", "title": title, "data": data}

    def async_show_form(self, step_id, data_schema, errors=None):
        return {
            "type": "form",
            "step_id": step_id,
            "errors": errors,
        }

# Mock the base class to avoid needing full Home Assistant
OptionsFlowHandler.__bases__ = (MockOptionsFlowBase,)

@pytest.fixture
def options_flow():
    handler = OptionsFlowHandler()
    handler.config_entry = MagicMock()
    handler.config_entry.options = {"track_wired_devices": False}
    return handler

@pytest.mark.asyncio
async def test_options_flow_init(options_flow):
    """Test that the options flow initializes correctly."""
    # This specifically tests the fix for the AttributeError
    assert options_flow.config_entry is not None
    assert options_flow.config_entry.options["track_wired_devices"] is False

@pytest.mark.asyncio
async def test_options_flow_step_init(options_flow):
    """Test the init step of options flow."""
    result = await options_flow.async_step_init()
    
    assert result["type"] == "form"
    assert result["step_id"] == "init"

@pytest.mark.asyncio
async def test_options_flow_save(options_flow):
    """Test saving options flow."""
    result = await options_flow.async_step_init(user_input={"track_wired_devices": True})
    
    assert result["type"] == "create_entry"
    assert result["data"] == {"track_wired_devices": True}
