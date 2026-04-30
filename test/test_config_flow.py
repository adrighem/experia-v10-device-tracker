"""Test the ExperiaBox v10 config flow."""
from unittest.mock import MagicMock, patch
import pytest
from custom_components.experiaboxv10.config_flow import ConfigFlow as ExperiaConfigFlow

class MockConfigFlowBase:
    def __init__(self):
        self.context = {}
        self.hass = MagicMock()

    async def async_set_unique_id(self, unique_id):
        pass

    def _abort_if_unique_id_configured(self):
        pass

    def async_create_entry(self, title, data, options=None):
        return {"type": "create_entry", "title": title, "data": data, "options": options}

    def async_show_form(self, step_id, data_schema, errors=None):
        return {
            "type": "form",
            "step_id": step_id,
            "errors": errors,
        }

ExperiaConfigFlow.__bases__ = (MockConfigFlowBase,)

@pytest.fixture
def flow():
    f = ExperiaConfigFlow()
    f.hass = MagicMock()
    return f

@pytest.mark.asyncio
async def test_show_form(flow):
    """Test that the form is served with no input."""
    result = await flow.async_step_user()

    assert result["type"] == "form"
    assert result["step_id"] == "user"

@pytest.mark.asyncio
async def test_successful_flow(flow):
    """Test a successful config flow."""
    user_input = {
        "host": "192.168.2.254",
        "username": "admin",
        "password": "password",
        "track_wired_devices": True,
    }

    with patch(
        "custom_components.experiaboxv10.config_flow.validate_input",
        return_value={"title": "ExperiaBox v10 (192.168.2.254)"},
    ):
        result = await flow.async_step_user(user_input)

    assert result["type"] == "create_entry"
    assert result["title"] == "ExperiaBox v10 (192.168.2.254)"
    assert result["data"] == {
        "host": "192.168.2.254",
        "username": "admin",
        "password": "password",
    }
    assert result["options"] == {"track_wired_devices": True}

@pytest.mark.asyncio
async def test_failed_flow(flow):
    """Test a failed config flow (cannot connect)."""
    user_input = {
        "host": "invalid_host",
        "username": "admin",
        "password": "password",
    }

    with patch(
        "custom_components.experiaboxv10.config_flow.validate_input",
        side_effect=Exception("Connection error"),
    ):
        result = await flow.async_step_user(user_input)

    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}
