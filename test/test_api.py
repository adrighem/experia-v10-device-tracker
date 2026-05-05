"""Test the ExperiaBox v10 API."""
from unittest.mock import MagicMock, AsyncMock
import pytest
from custom_components.experiaboxv10.api import ExperiaBoxV10Api

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def api(mock_session):
    return ExperiaBoxV10Api(mock_session, "192.168.2.254", "admin", "password")

def create_mock_response(status=200, json_data=None, headers=None):
    """Create a mock response object."""
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.headers = headers or {}
    mock_resp.json = AsyncMock(return_value=json_data or {})
    mock_resp.raise_for_status = MagicMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)
    return mock_resp

@pytest.mark.asyncio
async def test_get_devices(api, mock_session):
    """Test get_devices with fallback."""
    mock_login_resp = create_mock_response(
        status=200,
        json_data={"data": {"contextID": "abc"}}
    )

    mock_data_resp = create_mock_response(
        status=200,
        json_data={
            "status": [
                {
                    "Active": True,
                    "Tags": "lan eth",
                    "PhysAddress": "11:22:33:44:55:66",
                    "Name": "Wired",
                    "IPAddress": "192.168.2.100"
                }
            ]
        }
    )

    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]

    devices = await api.get_devices(track_wired_devices=True)
    assert len(devices) == 1
    assert devices[0].mac == "11:22:33:44:55:66"

@pytest.mark.asyncio
async def test_get_router_info_universal(api, mock_session):
    """Test get_router_info with universal approach."""
    mock_login_resp = create_mock_response(status=200, json_data={"status": {"contextID": "abc"}})
    mock_data_resp = create_mock_response(
        status=200,
        json_data={
            "status": {
                "ModelName": "H369A",
                "UpTime": 12345
            }
        }
    )
    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]
    info = await api.get_router_info()
    assert info.model == "H369A"
    assert info.uptime == 12345

@pytest.mark.asyncio
async def test_get_wan_info_information_fallback(api, mock_session):
    """Test get_wan_info using Device.Information fallback."""
    mock_login_resp = create_mock_response(status=200, json_data={"data": {"contextID": "abc"}})
    # First request is to sah.Device.Information
    mock_info_resp = create_mock_response(
        status=200,
        json_data={
            "status": {
                "ExternalIPAddress": "1.2.3.4",
                "DeviceStatus": "Up"
            }
        }
    )
    mock_session.post.side_effect = [mock_login_resp, mock_info_resp]
    info = await api.get_wan_info()
    assert info.external_ip == "1.2.3.4"
    assert info.connected is True

@pytest.mark.asyncio
async def test_get_traffic_info_nested_data(api, mock_session):
    """Test get_traffic_info with nested 'data' key."""
    mock_login_resp = create_mock_response(status=200, json_data={"data": {"contextID": "abc"}})
    mock_data_resp = create_mock_response(
        status=200,
        json_data={
            "data": {
                "statistics": {
                    "BytesSent": 500,
                    "BytesReceived": 600
                }
            }
        }
    )
    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]
    info = await api.get_traffic_info()
    assert info.bytes_sent == 500
    assert info.bytes_received == 600
