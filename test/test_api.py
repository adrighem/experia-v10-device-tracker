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
    """Test get_devices with modern firmware (Lua API)."""
    # Mock JSON login failure
    mock_json_fail = AsyncMock()
    mock_json_fail.status = 404

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
        AsyncMock(__aenter__=AsyncMock(return_value=mock_json_fail)),
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
    mock_json_fail = AsyncMock()
    mock_json_fail.status = 404

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
    
    mock_post_resp = AsyncMock()
    mock_post_resp.status = 404
    mock_session.post.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_post_resp))

    devices = await api.get_devices()

    assert len(devices) == 1
    assert devices[0].mac == "AA:BB:CC:DD:EE:FF"

@pytest.mark.asyncio
async def test_get_devices_wired(api, mock_session):
    """Test get_devices with track_wired_devices=True."""
    mock_login_resp = AsyncMock()
    mock_token_resp = AsyncMock()
    mock_token_resp.status = 404
    mock_data_resp_wlan = AsyncMock()
    mock_data_resp_wlan.text.return_value = """
    <root>
        <OBJ_ACCESSDEV_ID>
            <Instance>
                <ParaName>MACAddress</ParaName><ParaValue>AA:BB:CC:DD:EE:FF</ParaValue>
            </Instance>
        </OBJ_ACCESSDEV_ID>
    </root>
    """
    mock_data_resp_lan = AsyncMock()
    mock_data_resp_lan.text.return_value = """
    <root>
        <OBJ_ACCESSDEV_ID>
            <Instance>
                <ParaName>MACAddress</ParaName><ParaValue>11:22:33:44:55:66</ParaValue>
            </Instance>
        </OBJ_ACCESSDEV_ID>
    </root>
    """

    mock_session.get.side_effect = [
        AsyncMock(__aenter__=AsyncMock(return_value=mock_login_resp)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_token_resp)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_data_resp_wlan)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_data_resp_lan)),
    ]
    
    mock_post_resp = AsyncMock()
    mock_post_resp.status = 404
    mock_session.post.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_post_resp))

    devices = await api.get_devices(track_wired_devices=True)
    
    # Check that both WLAN and LAN requests were made
    calls = mock_session.get.call_args_list
    assert any("AccessMode=WLAN" in call[0][0] for call in calls)
    assert any("AccessMode=LAN" in call[0][0] for call in calls)

    assert len(devices) == 2
    assert devices[0].mac == "AA:BB:CC:DD:EE:FF"
    assert devices[1].mac == "11:22:33:44:55:66"

@pytest.mark.asyncio
async def test_get_devices_json_api(api, mock_session):
    """Test get_devices with the new JSON API (KPN Box 12 firmware)."""
    mock_login_resp = AsyncMock()
    mock_login_resp.status = 200
    mock_login_resp.headers = {"set-cookie": "session=123; path=/"}
    mock_login_resp.json = AsyncMock(return_value={"data": {"contextID": "abc123def"}})

    mock_data_resp = AsyncMock()
    mock_data_resp.status = 200
    mock_data_resp.json = AsyncMock(return_value={
        "status": [
            {
                "Active": True,
                "Tags": "lan edev mac physical eth security ipv4 ipv6",
                "PhysAddress": "11:22:33:44:55:66",
                "Name": "Wired Device",
                "IPAddress": "192.168.2.100"
            },
            {
                "Active": True,
                "Tags": "wlan edev mac physical security ipv4 ipv6",
                "PhysAddress": "AA:BB:CC:DD:EE:FF",
                "Name": "Wireless Device",
                "IPAddress": "192.168.2.101"
            },
            {
                "Active": False,
                "Tags": "wlan edev mac physical security ipv4 ipv6",
                "PhysAddress": "00:00:00:00:00:00",
                "Name": "Offline Device",
                "IPAddress": "192.168.2.102"
            }
        ]
    })

    mock_session.post.side_effect = [
        AsyncMock(__aenter__=AsyncMock(return_value=mock_login_resp)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_data_resp)),
    ]

    devices = await api.get_devices(track_wired_devices=True)

    assert len(devices) == 2
    
    # Assert Wired device
    assert devices[0].mac == "11:22:33:44:55:66"
    assert devices[0].name == "Wired Device"
    assert devices[0].ip == "192.168.2.100"

    # Assert Wireless device
    assert devices[1].mac == "AA:BB:CC:DD:EE:FF"
    assert devices[1].name == "Wireless Device"
    assert devices[1].ip == "192.168.2.101"
