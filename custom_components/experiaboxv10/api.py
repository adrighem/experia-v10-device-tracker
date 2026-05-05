"""API for ExperiaBox v10."""

from __future__ import annotations

import logging
from collections import namedtuple
from typing import Any

from aiohttp import ClientSession, ClientTimeout

_LOGGER = logging.getLogger(__name__)

Device = namedtuple("Device", ["mac", "name", "ip"])
RouterInfo = namedtuple(
    "RouterInfo",
    ["model", "hardware_version", "software_version", "serial_number", "uptime"],
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

    async def _get_context(self) -> tuple[str, str]:
        """Get context ID and cookie for the JSON API."""
        login_url = f"http://{self._host}/ws/NeMo/Intf/lan:getMIBs"
        login_payload = {
            "service": "sah.Device.Information",
            "method": "createContext",
            "parameters": {
                "applicationName": "webui",
                "username": self._username.lower(),
                "password": self._password,
            },
        }
        headers = {
            "Content-Type": "application/x-sah-ws-4-call+js",
            "Authorization": "X-Sah-Login",
        }

        _LOGGER.debug("Attempting to get context from %s", login_url)
        timeout = ClientTimeout(total=5)
        async with self._session.post(
            login_url, json=login_payload, headers=headers, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
            _LOGGER.debug("Login response: %s", data)
            
            if not isinstance(data, dict):
                raise Exception(f"Unexpected login response type: {type(data)}")
                
            data_field = data.get("data")
            if not isinstance(data_field, dict) or "contextID" not in data_field:
                raise Exception("Failed to get contextID from JSON API response")

            self._context_id = data_field["contextID"]
            cookie_header = resp.headers.get("set-cookie", "")
            self._cookie = cookie_header.split(";")[0] if cookie_header else ""
            
            _LOGGER.debug("Got context ID: %s", self._context_id)
            return self._context_id, self._cookie

    async def _request(
        self,
        service: str,
        method: str,
        parameters: dict | None = None,
        endpoint: str = "NeMo/Intf/lan:getMIBs",
    ) -> dict[str, Any]:
        """Make a request to the router API."""
        if not self._context_id or self._cookie is None:
            await self._get_context()

        url = f"http://{self._host}/ws/{endpoint}"
        headers = {
            "Content-Type": "application/x-sah-ws-4-call+json",
            "Authorization": f"X-Sah {self._context_id}",
            "X-Context": self._context_id,
            "Cookie": self._cookie,
        }
        payload = {
            "service": service,
            "method": method,
            "parameters": parameters or {},
        }

        _LOGGER.debug("Requesting %s.%s via %s", service, method, endpoint)
        try:
            async with self._session.post(url, json=payload, headers=headers) as resp:
                if resp.status in (401, 403):
                    _LOGGER.debug("Session expired, re-authenticating")
                    await self._get_context()
                    headers["Authorization"] = f"X-Sah {self._context_id}"
                    headers["X-Context"] = self._context_id
                    headers["Cookie"] = self._cookie
                    async with self._session.post(
                        url, json=payload, headers=headers
                    ) as resp2:
                        resp2.raise_for_status()
                        data = await resp2.json(content_type=None)
                        _LOGGER.debug("Response from %s.%s (after re-auth): %s", service, method, str(data)[:500])
                        return data if isinstance(data, dict) else {}

                resp.raise_for_status()
                data = await resp.json(content_type=None)
                _LOGGER.debug("Response from %s.%s: %s", service, method, str(data)[:500])
                return data if isinstance(data, dict) else {}
        except Exception:
            _LOGGER.debug("Request to %s.%s failed", service, method)
            self._context_id = None
            self._cookie = None
            raise

    async def get_devices(self, track_wired_devices: bool = False) -> list[Device]:
        """Get connected devices."""
        data = await self._request(
            "Devices", "get", {"expression": "not interface and not self and not voice"}
        )
        status = data.get("status")
        if not isinstance(status, list):
            return []

        results = {}
        for d in status:
            if not isinstance(d, dict):
                continue
            if not d.get("Active"):
                continue

            tags = str(d.get("Tags", "")).split()
            is_wired = "eth" in tags or "lan" in tags

            if not track_wired_devices and is_wired:
                continue

            mac = d.get("PhysAddress")
            if mac:
                results[mac.upper()] = Device(
                    mac.upper(), str(d.get("Name", "")), str(d.get("IPAddress", ""))
                )

        return list(results.values())

    async def get_router_info(self) -> RouterInfo:
        """Get router system information."""
        # Try both sah.Device.Information and Device.Information
        for service_name in ["sah.Device.Information", "Device.Information"]:
            try:
                data = await self._request(
                    service_name, "get", endpoint="Device/Information:get"
                )
                status = data.get("status")
                if isinstance(status, dict) and status.get("UpTime") is not None:
                    return RouterInfo(
                        model=str(status.get("ModelName", "Experia Box V10")),
                        hardware_version=str(status.get("HardwareVersion", "")),
                        software_version=str(status.get("SoftwareVersion", "")),
                        serial_number=str(status.get("SerialNumber", "")),
                        uptime=int(status.get("UpTime", 0) or 0),
                    )
            except Exception:
                continue
        
        return RouterInfo("Experia Box V10", "", "", "", 0)

    def _parse_mib_result(self, data: dict, mib_name: str) -> dict:
        """Extract MIB data from status dictionary or list."""
        status = data.get("status")
        if isinstance(status, list) and status:
            status = status[0]
        if not isinstance(status, dict):
            return {}
        
        mib_data = status.get(mib_name)
        if isinstance(mib_data, list) and mib_data:
            return mib_data[0]
        if isinstance(mib_data, dict):
            return mib_data
        return {}

    async def get_wan_info(self) -> WanInfo:
        """Get WAN connection information."""
        data = await self._request(
            "wan", "getMIBs", {"mibs": "wan"}, endpoint="NeMo/Intf/wan:getMIBs"
        )
        wan_mib = self._parse_mib_result(data, "wan")

        connected_status = str(wan_mib.get("ConnectionStatus", "")).lower()
        # Some routers return 'Up', 'Connected', 'Bound', etc.
        is_connected = connected_status in ("connected", "up", "bound", "connected")
        
        return WanInfo(
            external_ip=str(wan_mib.get("ExternalIPAddress", "")),
            connected=is_connected,
            link_status=str(wan_mib.get("LinkStatus", "Down")),
        )

    async def get_traffic_info(self) -> TrafficInfo:
        """Get WAN traffic statistics."""
        data = await self._request(
            "wan", "getMIBs", {"mibs": "statistics"}, endpoint="NeMo/Intf/wan:getMIBs"
        )
        stats_mib = self._parse_mib_result(data, "statistics")

        return TrafficInfo(
            bytes_sent=int(stats_mib.get("BytesSent", 0) or 0),
            bytes_received=int(stats_mib.get("BytesReceived", 0) or 0),
            packets_sent=int(stats_mib.get("PacketsSent", 0) or 0),
            packets_received=int(stats_mib.get("PacketsReceived", 0) or 0),
        )

    async def reboot(self) -> None:
        """Reboot the router."""
        await self._request(
            "sah.Device.Information", "reboot", endpoint="Device/Information:reboot"
        )

    async def get_guest_wifi_enabled(self) -> bool:
        """Get Guest Wi-Fi status."""
        data = await self._request("sah.Device.WiFi.Radio", "get")
        status = data.get("status")
        if not isinstance(status, list):
            return False

        for entry in status:
            if isinstance(entry, dict) and "Guest" in str(entry.get("SSID", "")):
                return entry.get("Enable", False)
        return False

    async def set_guest_wifi(self, enable: bool) -> None:
        """Enable or disable Guest Wi-Fi."""
        data = await self._request("sah.Device.WiFi.Radio", "get")
        status = data.get("status")
        if not isinstance(status, list):
            raise Exception("Guest Wi-Fi interface not found")

        for entry in status:
            if isinstance(entry, dict) and "Guest" in str(entry.get("SSID", "")):
                uid = entry.get("UID")
                if uid:
                    await self._request(
                        "sah.Device.WiFi.Radio", "set", {"uid": uid, "Enable": enable}
                    )
                    return
        raise Exception("Guest Wi-Fi interface not found")
