"""API for ExperiaBox v10."""

from __future__ import annotations

from collections import namedtuple
import logging
from typing import Any
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

Device = namedtuple("Device", ["mac", "name", "ip", "active"])
RouterInfo = namedtuple(
    "RouterInfo", ["model", "hardware_version", "software_version", "serial_number", "uptime"]
)
WanInfo = namedtuple("WanInfo", ["external_ip", "connected", "link_status"])
TrafficInfo = namedtuple(
    "TrafficInfo", ["bytes_sent", "bytes_received", "packets_sent", "packets_received"]
)


class ExperiaBoxV10Api:
    """API for ExperiaBox v10."""

    def __init__(
        self, session: ClientSession, host: str, username: str, password: str
    ) -> None:
        """Initialize."""
        self._session = session
        self._host = host
        self._username = username
        self._password = password
        self._context_id: str | None = None
        self._cookie: str | None = None
        self._user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    async def _get_context(self) -> tuple[str, str]:
        """Get context ID and cookie for the JSON API."""
        # Standard SAH API uses /ws for everything
        login_url = f"http://{self._host}/ws"
        payload = {
            "service": "ssw.Server.Context",
            "method": "createContext",
            "parameters": {
                "applicationName": "webui",
                "username": self._username,
                "password": self._password,
            },
        }
        async with self._session.post(login_url, json=payload) as resp:
            data = await resp.json(content_type=None)
            try:
                # The response could have "data" or "status" depending on firmware versions
                if "data" in data and "contextID" in data["data"]:
                    self._context_id = data["data"]["contextID"]
                elif "status" in data and isinstance(data["status"], dict) and "contextID" in data["status"]:
                    self._context_id = data["status"]["contextID"]
                else:
                    _LOGGER.error("Failed to parse contextID. Raw response: %s", data)
                    raise KeyError("contextID not found in response")
                    
                self._cookie = resp.headers.get("Set-Cookie")
                return self._context_id, self._cookie
            except KeyError as err:
                _LOGGER.error("Context key error: %s, raw response: %s", err, data)
                raise

    async def _request(
        self,
        service: str,
        method: str,
        parameters: dict | None = None,
        endpoint: str = "ws/NeMo/Intf/lan:getMIBs",
    ) -> dict[str, Any]:
        """Make a request to the router API."""
        if not self._context_id or self._cookie is None:
            await self._get_context()

        # Only override default if it's the standard gateway and we know these services need root /ws
        if endpoint == "ws/NeMo/Intf/lan:getMIBs" and service in ("sah.Device.Information", "DeviceInfo", "sah.Device.WiFi.Radio"):
            endpoint = "ws"

        url = f"http://{self._host}/{endpoint}"
        headers = {
            "Content-Type": "application/x-sah-ws-4-call+json",
            "Authorization": f"X-Sah {self._context_id}",
            "X-Context": self._context_id,
            "Cookie": self._cookie,
            "User-Agent": self._user_agent,
        }
        payload = {
            "service": service,
            "method": method,
            "parameters": parameters or {},
        }
        async with self._session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 401:
                # Session expired, re-authenticate
                self._context_id = None
                self._cookie = None
                return await self._request(service, method, parameters, endpoint)
            return await resp.json(content_type=None)

    def _parse_devices(self, status_list: list[dict], track_wired_devices: bool, results: dict[str, Device], parent_is_wifi: bool = False) -> None:
        """Parse a list of device objects and update the results dictionary."""
        for d in status_list:
            if not isinstance(d, dict):
                continue
            
            mac = d.get("PhysAddress")
            if not mac:
                continue

            active = bool(d.get("Active", False))
            tags = str(d.get("Tags", "")).lower().split()
            inf = str(d.get("InterfaceName", d.get("Layer2Interface", ""))).lower()
            
            is_wifi = parent_is_wifi or "wifi" in tags or "ssw_sta" in tags or "wl0" in inf or "wl1" in inf
            is_wired = not is_wifi and ("eth" in tags or "lan" in tags or "eth" in inf)

            if not track_wired_devices and is_wired:
                continue

            results[mac.upper()] = Device(
                mac.upper(),
                str(d.get("Name", d.get("Key", mac))),
                str(d.get("IPAddress", "")),
                active
            )

    def _parse_topology(self, nodes: list[dict], track_wired_devices: bool, results: dict[str, Device], parent_is_wifi: bool = False) -> None:
        """Recursively parse the topology tree and update the results dictionary."""
        for node in nodes:
            tags = str(node.get("Tags", "")).lower().split()
            inf = str(node.get("InterfaceName", node.get("Layer2Interface", ""))).lower()
            is_wifi = parent_is_wifi or "wifi" in tags or "ssw_sta" in tags or "wl0" in inf or "wl1" in inf
            
            mac = node.get("PhysAddress")
            if mac:
                is_wired = not is_wifi and ("eth" in tags or "lan" in tags or "eth" in inf)
                if not track_wired_devices and is_wired:
                    continue
                results[mac.upper()] = Device(
                    mac.upper(),
                    str(node.get("Name", node.get("Key", mac))),
                    str(node.get("IPAddress", "")),
                    bool(node.get("Active", False))
                )
            
            children = node.get("Children")
            if isinstance(children, list):
                self._parse_topology(children, track_wired_devices, results, parent_is_wifi=is_wifi)

    async def get_devices(self, track_wired_devices: bool = False) -> list[Device]:
        """Get connected devices."""
        results: dict[str, Device] = {}

        # 1. Try generic Devices:get on privileged gateway (proven in trace)
        try:
            # First get the inactive ones
            data = await self._request(
                "Devices", "get", 
                {"expression": "not interface and not self and not voice and .Active==false", "flags": "full_links"},
                endpoint="ws/NeMo/Intf/lan:getMIBs"
            )
            status = data.get("status")
            if isinstance(status, list):
                self._parse_devices(status, track_wired_devices, results)
                
            # Then get the active ones
            data_active = await self._request(
                "Devices", "get", 
                {"expression": "not interface and not self and not voice and .Active==true", "flags": "full_links"},
                endpoint="ws/NeMo/Intf/lan:getMIBs"
            )
            status_active = data_active.get("status")
            if isinstance(status_active, list):
                self._parse_devices(status_active, track_wired_devices, results)
        except Exception as err:
            _LOGGER.debug("Failed to get devices via targeted queries: %s", err)

        # 2. Try topology traversal as fallback
        if not results:
            for network in ("lan", "guest"):
                try:
                    data = await self._request(
                        f"Devices.Device.{network}", "topology",
                        {"expression": "not logical", "flags": "no_recurse|no_actions"},
                        endpoint="ws/NeMo/Intf/lan:getMIBs"
                    )
                    status = data.get("status")
                    if isinstance(status, list):
                        self._parse_topology(status, track_wired_devices, results)
                except Exception:
                    pass

        # Final check to see if we found anything
        if not results:
            _LOGGER.debug("No devices discovered on %s", self._host)

        return list(results.values())

    async def get_router_info(self) -> RouterInfo:
        """Get router system information."""
        # Try DeviceInfo first
        data = await self._request("DeviceInfo", "get", endpoint="ws")
        status = data.get("status")
        if not isinstance(status, dict) or not status:
            # Fallback to Devices:get self
            data = await self._request("Devices", "get", {"expression": "self && wan && hgw"}, endpoint="ws/NeMo/Intf/lan:getMIBs")
            status = data.get("status")
            if isinstance(status, list) and status:
                status = status[0]

        if not isinstance(status, dict):
            status = {}

        uptime = int(status.get("UpTime", 0) or 0)
        
        # If uptime is still 0, try to get it from Time service (common in new firmware)
        if uptime == 0:
            try:
                time_data = await self._request("Time", "getTime")
                nmc_data = await self._request("NMC", "get")
                uptime = int(nmc_data.get("status", {}).get("UpTime", 0) or 0)
            except Exception:
                pass

        return RouterInfo(
            model=str(status.get("ModelName", status.get("ProductClass", "Experia Box V10"))),
            hardware_version=str(status.get("HardwareVersion", "")),
            software_version=str(status.get("SoftwareVersion", "")),
            serial_number=str(status.get("SerialNumber", "")),
            uptime=uptime,
        )

    def _parse_mib_result(self, data: dict, mib_names: list[str]) -> dict:
        """Extract MIB data from status dictionary or list."""
        status = data.get("status")
        if isinstance(status, list) and status:
            status = status[0]
        if not isinstance(status, dict):
            # Check if it's in 'data'
            status = data.get("data")
            if isinstance(status, list) and status:
                status = status[0]
            if not isinstance(status, dict):
                return {}
        
        for name in mib_names:
            mib_data = status.get(name)
            if isinstance(mib_data, list) and mib_data:
                mib_data = mib_data[0]
            if isinstance(mib_data, dict):
                return mib_data
            
        return status

    async def get_wan_info(self) -> WanInfo:
        """Get WAN connection information."""
        # Use the confirmed NMC:getWANStatus method
        data = await self._request("NMC", "getWANStatus")
        status = data.get("status", False)
        val = data.get("data", {})
        
        if status and isinstance(val, dict):
            return WanInfo(
                external_ip=str(val.get("IPAddress", "")),
                connected=str(val.get("LinkState", "")).lower() == "up",
                link_status=str(val.get("LinkState", "Down")),
            )

        return WanInfo("", False, "Down")

    async def get_traffic_info(self) -> TrafficInfo:
        """Get traffic information."""
        # Use the confirmed NeMo.Intf.eth0:getNetDevStats method
        # Stats require root /ws endpoint
        data = await self._request("NeMo.Intf.eth0", "getNetDevStats", endpoint="ws")
        status = data.get("status") or {}

        return TrafficInfo(
            bytes_sent=int(status.get("TxBytes", 0) or 0),
            bytes_received=int(status.get("RxBytes", 0) or 0),
            packets_sent=int(status.get("TxPackets", 0) or 0),
            packets_received=int(status.get("RxPackets", 0) or 0),
        )

    async def reboot(self) -> None:
        """Reboot the router."""
        await self._request("sah.Device.Information", "reboot", endpoint="ws")

    async def get_guest_wifi_enabled(self) -> bool:
        """Get Guest Wi-Fi status."""
        data = await self._request("sah.Device.WiFi.Radio", "get", endpoint="ws")
        status = data.get("status")
        if not isinstance(status, list):
            return False

        for entry in status:
            if isinstance(entry, dict) and "Guest" in str(entry.get("SSID", "")):
                return entry.get("Enable", False)
        return False

    async def set_guest_wifi(self, enable: bool) -> None:
        """Enable or disable Guest Wi-Fi."""
        data = await self._request("sah.Device.WiFi.Radio", "get", endpoint="ws")
        status = data.get("status")
        if not isinstance(status, list):
            raise Exception("Guest Wi-Fi interface not found")

        for entry in status:
            if isinstance(entry, dict) and "Guest" in str(entry.get("SSID", "")):
                uid = entry.get("UID")
                if uid:
                    await self._request(
                        "sah.Device.WiFi.Radio", "set", {"uid": uid, "Enable": enable}, endpoint="ws"
                    )
                    return
        raise Exception("Guest Wi-Fi interface not found")
