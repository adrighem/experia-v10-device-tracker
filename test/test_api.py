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
    """Test get_devices using the new topology method."""
    mock_login_resp = create_mock_response(status=200, json_data={"data": {"contextID": "abc"}})
    mock_topology_resp = create_mock_response(
        status=200,
        json_data={
            "status": [
                {
                    "Key": "lan",
                    "Children": [
                        {
                            "Key": "ETH0",
                            "Tags": "lan eth",
                            "Children": [
                                {
                                    "PhysAddress": "11:22:33:44:55:66",
                                    "Name": "PC",
                                    "Active": True,
                                    "Tags": "edev lan eth"
                                }
                            ]
                        },
                        {
                            "Key": "vap2g0priv",
                            "Tags": "wifi",
                            "Children": [
                                {
                                    "PhysAddress": "AA:BB:CC:DD:EE:FF",
                                    "Name": "Phone",
                                    "Active": True,
                                    "Tags": "edev wifi"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )
    # Mocking guest topology as empty
    mock_empty_resp = create_mock_response(status=200, json_data={"status": []})
    
    def mock_post(url, **kwargs):
        print("MOCK POST CALLED:", url)
        if "login" in url or "ws" in url and "ssw" in str(kwargs.get("json")):
            return mock_login_resp
        if "topology" in str(kwargs.get("json")) and "lan" in str(kwargs.get("json")):
            return mock_topology_resp
        return mock_empty_resp

    mock_session.post.side_effect = mock_post
    devices = await api.get_devices(track_wired_devices=True)

    print("DEVICES FOUND:", devices)
    assert len(devices) == 2
    assert any(d.name == "Phone" for d in devices)
    assert any(d.name == "PC" for d in devices)

@pytest.mark.asyncio
async def test_get_router_info_universal(api, mock_session):
    """Test get_router_info with universal approach."""
    mock_login_resp = create_mock_response(status=200, json_data={"data": {"contextID": "abc"}})
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
async def test_get_wan_info_nmc(api, mock_session):
    """Test get_wan_info using the new NMC:getWANStatus method."""
    mock_login_resp = create_mock_response(status=200, json_data={"data": {"contextID": "abc"}})
    mock_info_resp = create_mock_response(
        status=200,
        json_data={
            "status": True,
            "data": {
                "IPAddress": "1.2.3.4",
                "LinkState": "up"
            }
        }
    )
    mock_session.post.side_effect = [mock_login_resp, mock_info_resp]
    info = await api.get_wan_info()
    assert info.external_ip == "1.2.3.4"
    assert info.connected is True

@pytest.mark.asyncio
async def test_get_traffic_info(api, mock_session):
    """Test get_traffic_info using the new NeMo.Intf.eth0 method."""
    mock_login_resp = create_mock_response(status=200, json_data={"data": {"contextID": "abc"}})
    mock_data_resp = create_mock_response(
        status=200,
        json_data={
            "status": {
                "TxBytes": 1000,
                "RxBytes": 2000,
                "TxPackets": 100,
                "RxPackets": 200
            }
        }
    )
    mock_session.post.side_effect = [mock_login_resp, mock_data_resp]
    info = await api.get_traffic_info()
    assert info.bytes_sent == 1000
    assert info.bytes_received == 2000
