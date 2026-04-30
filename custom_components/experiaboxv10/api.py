"""API for ExperiaBox v10."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from hashlib import sha256
import xml.etree.ElementTree as ET
from collections import namedtuple

from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

Device = namedtuple('Device', ['mac', 'name', 'ip'])

class ExperiaBoxV10Api:
    """API for ExperiaBox v10."""

    def __init__(self, session: ClientSession, host: str, username: str, password: str) -> None:
        """Initialize."""
        self._session = session
        self._host = host
        self._username = username
        self._password = password

    async def get_devices(self, track_wired_devices: bool = False) -> list[Device]:
        """Get connected devices."""
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
                    "action": "login"
                }
            else:
                token_text = await resp.text()
                match = re.findall(r'\d+', token_text)
                if not match:
                    _LOGGER.error("Could not find token digits in: %s", token_text)
                    raise Exception("Could not find token digits")
                
                login_payload = {
                    "Username": self._username,
                    "Password": sha256((self._password + match[0]).encode('utf-8')).hexdigest(),
                    "action": "login"
                }

        # 2. Login
        async with self._session.post(login_url, data=login_payload) as resp:
            await resp.text()

        # 3. Get data
        ts = round(datetime.now(timezone.utc).timestamp() * 1000)
        access_mode = "" if track_wired_devices else "AccessMode=WLAN&"
        data_url = f"http://{self._host}/common_page/home_AssociateDevs_lua.lua?{access_mode}_={ts}"
        async with self._session.get(data_url) as resp:
            data = await resp.text()

        # 4. Logout
        logout_payload = {
            "IF_LogOff": 1,
            "IF_LanguageSwitch": "",
            "IF_ModeSwitch": ""
        }
        async with self._session.post(login_url, data=logout_payload) as resp:
            await resp.text()

        return self._parse_xml(data)

    def _parse_xml(self, data: str) -> list[Device]:
        try:
            result_root = ET.fromstring(data)
        except ET.ParseError:
            _LOGGER.error("Failed to parse XML: %s", data)
            return []
            
        device_list = result_root.find('OBJ_ACCESSDEV_ID')

        if device_list is None:
            return []

        results = []
        for device in device_list:
            keys = device.findall('ParaName')
            values = device.findall('ParaValue')

            result = {}
            for index, key in enumerate(keys):
                value = values[index]

                if key.text in ['HostName', 'MACAddress', 'IPAddress']:
                    result[key.text] = value.text or ''

            if 'MACAddress' in result and result['MACAddress']:
                results.append(Device(result['MACAddress'].upper(), result.get('HostName', ''), result.get('IPAddress', '')))

        return results
