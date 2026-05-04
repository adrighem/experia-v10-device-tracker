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
    # raise_for_status is a regular method, not a coroutine
    mock_resp.raise_for_status = MagicMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)
    return mock_resp

@pytest.mark.asyncio
async def test_get_devices(api, mock_session):
    """Test get_devices with the JSON API."""
    mock_login_resp = create_mock_response(
        status=200,
        json_data={"data": {"contextID": "abc123def"}},
        headers={"set-cookie": "session=123; path=/"}
    )

    mock_data_resp = create_mock_response(
        status=200,
        json_data={
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
                }
            ]
        }
    )

    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]

    devices = await api.get_devices(track_wired_devices=True)

    assert len(devices) == 2
    assert devices[0].mac == "11:22:33:44:55:66"
    assert devices[1].mac == "AA:BB:CC:DD:EE:FF"

@pytest.mark.asyncio
async def test_get_devices_no_wired(api, mock_session):
    """Test get_devices without tracking wired devices."""
    mock_login_resp = create_mock_response(
        status=200,
        json_data={"data": {"contextID": "abc123def"}},
        headers={"set-cookie": "session=123; path=/"}
    )

    mock_data_resp = create_mock_response(
        status=200,
        json_data={
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
                }
            ]
        }
    )

    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]

    devices = await api.get_devices(track_wired_devices=False)

    assert len(devices) == 1
    assert devices[0].mac == "AA:BB:CC:DD:EE:FF"

@pytest.mark.asyncio
async def test_get_router_info(api, mock_session):
    """Test get_router_info with the JSON API."""
    mock_login_resp = create_mock_response(
        status=200,
        json_data={"data": {"contextID": "abc123def"}},
        headers={"set-cookie": "session=123; path=/"}
    )

    mock_data_resp = create_mock_response(
        status=200,
        json_data={
            "status": {
                "ModelName": "H369A",
                "HardwareVersion": "V1.0",
                "SoftwareVersion": "V10.C.26.04",
                "SerialNumber": "TEST-SERIAL",
                "UpTime": 3600
            }
        }
    )

    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]

    info = await api.get_router_info()

    assert info.model == "H369A"
    assert info.hardware_version == "V1.0"
    assert info.software_version == "V10.C.26.04"
    assert info.serial_number == "TEST-SERIAL"
    assert info.uptime == 3600

@pytest.mark.asyncio
async def test_get_wan_info(api, mock_session):
    """Test get_wan_info with the JSON API."""
    mock_login_resp = create_mock_response(
        status=200,
        json_data={"data": {"contextID": "abc123def"}},
        headers={"set-cookie": "session=123; path=/"}
    )

    mock_data_resp = create_mock_response(
        status=200,
        json_data={
            "status": {
                "ExternalIPAddress": "8.8.8.8",
                "ConnectionStatus": "Connected",
                "LinkStatus": "Up"
            }
        }
    )

    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]

    info = await api.get_wan_info()

    assert info.external_ip == "8.8.8.8"
    assert info.connected is True
    assert info.link_status == "Up"

@pytest.mark.asyncio
async def test_get_traffic_info(api, mock_session):
    """Test get_traffic_info with the JSON API."""
    mock_login_resp = create_mock_response(
        status=200,
        json_data={"data": {"contextID": "abc123def"}},
        headers={"set-cookie": "session=123; path=/"}
    )

    mock_data_resp = create_mock_response(
        status=200,
        json_data={
            "status": {
                "BytesSent": "1000",
                "BytesReceived": "2000",
                "PacketsSent": "10",
                "PacketsReceived": "20"
            }
        }
    )

    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]

    info = await api.get_traffic_info()

    assert info.bytes_sent == 1000
    assert info.bytes_received == 2000
    assert info.packets_sent == 10
    assert info.packets_received == 20

@pytest.mark.asyncio
async def test_login_failure(api, mock_session):
    """Test get_devices with login failure."""
    mock_login_resp = create_mock_response(status=401)
    mock_login_resp.raise_for_status.side_effect = Exception("Unauthorized")

    mock_session.post.return_value = mock_login_resp

    with pytest.raises(Exception, match="Unauthorized"):
        await api.get_devices()

@pytest.mark.asyncio
async def test_get_router_info_null_status(api, mock_session):
    """Test get_router_info with null status response."""
    mock_login_resp = create_mock_response(
        status=200,
        json_data={"data": {"contextID": "abc"}},
    )
    mock_data_resp = create_mock_response(
        status=200,
        json_data={"status": None}
    )
    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]

    info = await api.get_router_info()
    assert info.model == "Experia Box V10"
    assert info.uptime == 0

@pytest.mark.asyncio
async def test_get_devices_null_status(api, mock_session):
    """Test get_devices with null status response."""
    mock_login_resp = create_mock_response(
        status=200,
        json_data={"data": {"contextID": "abc"}},
    )
    mock_data_resp = create_mock_response(
        status=200,
        json_data={"status": None}
    )
    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]

    devices = await api.get_devices()
    assert devices == []
