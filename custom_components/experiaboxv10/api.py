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

        timeout = ClientTimeout(total=5)
        async with self._session.post(
            login_url, json=login_payload, headers=headers, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
            if not isinstance(data, dict) or "data" not in data or "contextID" not in data["data"]:
                _LOGGER.debug("Unexpected login response: %s", data)
                raise Exception("Failed to get contextID from JSON API")

            self._context_id = data["data"]["contextID"]
            self._cookie = resp.headers.get("set-cookie", "").split(";")[0]
            return self._context_id, self._cookie

    async def _request(self, service: str, method: str, parameters: dict | None = None) -> dict[str, Any]:
        """Make a request to the router API."""
        if not self._context_id or not self._cookie:
            await self._get_context()

        url = f"http://{self._host}/ws/NeMo/Intf/lan:getMIBs"
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

        try:
            async with self._session.post(url, json=payload, headers=headers) as resp:
                if resp.status in (401, 403):
                    # Session might have expired, try to re-auth once
                    await self._get_context()
                    headers["Authorization"] = f"X-Sah {self._context_id}"
                    headers["X-Context"] = self._context_id
                    headers["Cookie"] = self._cookie
                    async with self._session.post(url, json=payload, headers=headers) as resp2:
                        resp2.raise_for_status()
                        data = await resp2.json(content_type=None)
                        return data if isinstance(data, dict) else {}
                
                resp.raise_for_status()
                data = await resp.json(content_type=None)
                return data if isinstance(data, dict) else {}
        except Exception:
            # Clear context on error so next attempt tries re-auth
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

            tags = d.get("Tags", "").split()
            is_wired = "eth" in tags or "lan" in tags

            if not track_wired_devices and is_wired:
                continue

            mac = d.get("PhysAddress")
            if mac:
                results[mac.upper()] = Device(
                    mac.upper(), d.get("Name", ""), d.get("IPAddress", "")
                )

        return list(results.values())

    async def get_router_info(self) -> RouterInfo:
        """Get router system information."""
        data = await self._request("sah.Device.Information", "get")
        status = data.get("status")
        if not isinstance(status, dict):
            status = {}

        return RouterInfo(
            model=status.get("ModelName", "Experia Box V10"),
            hardware_version=status.get("HardwareVersion", ""),
            software_version=status.get("SoftwareVersion", ""),
            serial_number=status.get("SerialNumber", ""),
            uptime=status.get("UpTime", 0),
        )

    async def get_wan_info(self) -> WanInfo:
        """Get WAN connection information."""
        data = await self._request("sah.Device.WAN", "get")
        status = data.get("status")
        if not isinstance(status, dict):
            status = {}

        return WanInfo(
            external_ip=status.get("ExternalIPAddress", ""),
            connected=str(status.get("ConnectionStatus", "")).lower() == "connected",
            link_status=status.get("LinkStatus", "Down"),
        )

    async def get_traffic_info(self) -> TrafficInfo:
        """Get WAN traffic statistics."""
        data = await self._request("sah.Device.WAN", "getStatistics")
        status = data.get("status")
        if not isinstance(status, dict):
            status = {}

        return TrafficInfo(
            bytes_sent=int(status.get("BytesSent", 0)),
            bytes_received=int(status.get("BytesReceived", 0)),
            packets_sent=int(status.get("PacketsSent", 0)),
            packets_received=int(status.get("PacketsReceived", 0)),
        )

    async def reboot(self) -> None:
        """Reboot the router."""
        await self._request("sah.Device.Information", "reboot")

    async def get_guest_wifi_enabled(self) -> bool:
        """Get Guest Wi-Fi status."""
        data = await self._request("sah.Device.WiFi.Radio", "get")
        status = data.get("status")
        if not isinstance(status, list):
            return False
            
        for entry in status:
            if isinstance(entry, dict) and "Guest" in entry.get("SSID", ""):
                return entry.get("Enable", False)
        return False

    async def set_guest_wifi(self, enable: bool) -> None:
        """Enable or disable Guest Wi-Fi."""
        data = await self._request("sah.Device.WiFi.Radio", "get")
        status = data.get("status")
        if not isinstance(status, list):
            raise Exception("Guest Wi-Fi interface not found")

        for entry in status:
            if isinstance(entry, dict) and "Guest" in entry.get("SSID", ""):
                uid = entry.get("UID")
                if uid:
                    await self._request(
                        "sah.Device.WiFi.Radio", "set", {"uid": uid, "Enable": enable}
                    )
                    return
        raise Exception("Guest Wi-Fi interface not found")
