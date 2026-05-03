"""API for ExperiaBox v10."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from hashlib import sha256
import xml.etree.ElementTree as ET
from collections import namedtuple

from aiohttp import ClientSession, ClientTimeout

_LOGGER = logging.getLogger(__name__)

Device = namedtuple("Device", ["mac", "name", "ip"])


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

    async def get_devices(self, track_wired_devices: bool = False) -> list[Device]:
        """Get connected devices."""
        # Try new KPN WebUI JSON API first (e.g. for V10 with firmware V10.C.26+)
        new_api_url = f"http://{self._host}/ws/NeMo/Intf/lan:getMIBs"
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

        try:
            timeout = ClientTimeout(total=5)
            async with self._session.post(
                new_api_url, json=login_payload, headers=headers, timeout=timeout
            ) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if "data" in data and "contextID" in data["data"]:
                        context_id = data["data"]["contextID"]
                        cookie = resp.headers.get("set-cookie", "").split(";")[0]
                        return await self._get_devices_json(
                            context_id, cookie, track_wired_devices
                        )
        except Exception as e:
            _LOGGER.debug(
                "Failed to connect to JSON API: %s, falling back to Lua API", e
            )

        # Fallback to old Lua API
        return await self._get_devices_lua(track_wired_devices)

    async def _get_devices_json(
        self, context_id: str, cookie: str, track_wired_devices: bool
    ) -> list[Device]:
        url = f"http://{self._host}/ws/NeMo/Intf/lan:getMIBs"
        headers = {
            "Content-Type": "application/x-sah-ws-4-call+json",
            "Authorization": f"X-Sah {context_id}",
            "X-Context": context_id,
            "Cookie": cookie,
        }
        payload = {
            "service": "Devices",
            "method": "get",
            "parameters": {"expression": "not interface and not self and not voice"},
        }
        async with self._session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json(content_type=None)
            status = data.get("status", [])

        results = {}
        for d in status:
            if not d.get("Active"):
                continue

            tags = d.get("Tags", "")
            is_wired = "eth" in tags or "lan" in tags

            if not track_wired_devices and is_wired:
                continue

            mac = d.get("PhysAddress")
            if mac:
                results[mac.upper()] = Device(
                    mac.upper(), d.get("Name", ""), d.get("IPAddress", "")
                )

        return list(results.values())

    async def _get_devices_lua(self, track_wired_devices: bool) -> list[Device]:
        login_url = f"http://{self._host}"
        token_url = f"http://{self._host}/function_module/login_module/login_page/logintoken_lua.lua"

        # 1. Get initial cookies and token
        async with self._session.get(login_url) as resp:
            await resp.text()

        async with self._session.get(token_url) as resp:
            if resp.status == 404:
                # Old version support
                login_payload = {
                    "Username": self._username,
                    "Password": self._password,
                    "Frm_Logintoken": "",
                    "action": "login",
                }
            else:
                token_text = await resp.text()
                match = re.findall(r"\d+", token_text)
                if not match:
                    _LOGGER.error("Could not find token digits in: %s", token_text)
                    raise Exception("Could not find token digits")

                login_payload = {
                    "Username": self._username,
                    "Password": sha256(
                        (self._password + match[0]).encode("utf-8")
                    ).hexdigest(),
                    "action": "login",
                }

        # 2. Login
        async with self._session.post(login_url, data=login_payload) as resp:
            await resp.text()

        # 3. Get data
        all_data = []

        # Get WLAN devices
        ts = round(datetime.now(timezone.utc).timestamp() * 1000)
        data_url = f"http://{self._host}/common_page/home_AssociateDevs_lua.lua?AccessMode=WLAN&_={ts}"
        async with self._session.get(data_url) as resp:
            data = await resp.text()
            if "500 Internal Server Error" not in data:
                all_data.append(data)

        # Get LAN devices if requested
        if track_wired_devices:
            ts = round(datetime.now(timezone.utc).timestamp() * 1000)
            data_url_lan = f"http://{self._host}/common_page/home_AssociateDevs_lua.lua?AccessMode=LAN&_={ts}"
            async with self._session.get(data_url_lan) as resp:
                data = await resp.text()
                if "500 Internal Server Error" not in data:
                    all_data.append(data)

        # 4. Logout
        logout_payload = {"IF_LogOff": 1, "IF_LanguageSwitch": "", "IF_ModeSwitch": ""}
        async with self._session.post(login_url, data=logout_payload) as resp:
            await resp.text()

        results = {}
        for data in all_data:
            for device in self._parse_xml(data):
                results[device.mac] = device

        return list(results.values())

    def _parse_xml(self, data: str) -> list[Device]:
        try:
            result_root = ET.fromstring(data)
        except ET.ParseError:
            _LOGGER.error("Failed to parse XML: %s", data)
            return []

        device_list = result_root.find("OBJ_ACCESSDEV_ID")

        if device_list is None:
            return []

        results = []
        for device in device_list:
            keys = device.findall("ParaName")
            values = device.findall("ParaValue")

            result = {}
            for index, key in enumerate(keys):
                value = values[index]

                if key.text in ["HostName", "MACAddress", "IPAddress"]:
                    result[key.text] = value.text or ""

            if "MACAddress" in result and result["MACAddress"]:
                results.append(
                    Device(
                        result["MACAddress"].upper(),
                        result.get("HostName", ""),
                        result.get("IPAddress", ""),
                    )
                )

        return results
