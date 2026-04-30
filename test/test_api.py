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

@pytest.mark.asyncio
async def test_get_devices_new_version(api, mock_session):
    """Test get_devices with modern firmware."""
    # Mock login page (initial cookies)
    mock_login_resp = AsyncMock()
    mock_login_resp.text.return_value = "login page"
    
    # Mock token page
    mock_token_resp = AsyncMock()
    mock_token_resp.status = 200
    mock_token_resp.text.return_value = "var token = '123456';"
    
    # Mock login post
    mock_post_resp = AsyncMock()
    mock_post_resp.text.return_value = "success"
    
    # Mock data page
    mock_data_resp = AsyncMock()
    mock_data_resp.text.return_value = """
    <root>
        <OBJ_ACCESSDEV_ID>
            <Instance>
                <ParaName>HostName</ParaName><ParaValue>Device1</ParaValue>
                <ParaName>MACAddress</ParaName><ParaValue>00:11:22:33:44:55</ParaValue>
                <ParaName>IPAddress</ParaName><ParaValue>192.168.2.1</ParaValue>
            </Instance>
        </OBJ_ACCESSDEV_ID>
    </root>
    """
    
    # Mock logout
    mock_logout_resp = AsyncMock()

    mock_session.get.side_effect = [
        AsyncMock(__aenter__=AsyncMock(return_value=mock_login_resp)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_token_resp)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_data_resp)),
    ]
    mock_session.post.side_effect = [
        AsyncMock(__aenter__=AsyncMock(return_value=mock_post_resp)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_logout_resp)),
    ]

    devices = await api.get_devices()

    assert len(devices) == 1
    assert devices[0].mac == "00:11:22:33:44:55"
    assert devices[0].name == "Device1"
    assert devices[0].ip == "192.168.2.1"

@pytest.mark.asyncio
async def test_get_devices_old_version(api, mock_session):
    """Test get_devices with older firmware (404 on token)."""
    # Mock login page
    mock_login_resp = AsyncMock()
    
    # Mock token page (404)
    mock_token_resp = AsyncMock()
    mock_token_resp.status = 404
    
    # Mock data page
    mock_data_resp = AsyncMock()
    mock_data_resp.text.return_value = """
    <root>
        <OBJ_ACCESSDEV_ID>
            <Instance>
                <ParaName>MACAddress</ParaName><ParaValue>AA:BB:CC:DD:EE:FF</ParaValue>
            </Instance>
        </OBJ_ACCESSDEV_ID>
    </root>
    """

    mock_session.get.side_effect = [
        AsyncMock(__aenter__=AsyncMock(return_value=mock_login_resp)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_token_resp)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_data_resp)),
    ]
    mock_session.post.return_value = AsyncMock(__aenter__=AsyncMock())

    devices = await api.get_devices()

    assert len(devices) == 1
    assert devices[0].mac == "AA:BB:CC:DD:EE:FF"
