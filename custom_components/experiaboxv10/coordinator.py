"""DataUpdateCoordinator for ExperiaBox v10."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

import time
from .const import DOMAIN, CONF_TRACK_WIRED_DEVICES
from .api import ExperiaBoxV10Api, Device, RouterInfo, WanInfo, TrafficInfo

_LOGGER = logging.getLogger(__name__)


class ExperiaBoxV10Data:
    """Class to hold ExperiaBox v10 data."""

    def __init__(
        self,
        devices: list[Device],
        router_info: RouterInfo,
        wan_info: WanInfo,
        traffic_info: TrafficInfo,
        guest_wifi_enabled: bool = False,
        new_device_detected: bool = False,
        last_new_device: str | None = None,
        throughput_down: float = 0,
        throughput_up: float = 0,
    ) -> None:
        """Initialize."""
        self.devices = devices
        self.router_info = router_info
        self.wan_info = wan_info
        self.traffic_info = traffic_info
        self.guest_wifi_enabled = guest_wifi_enabled
        self.new_device_detected = new_device_detected
        self.last_new_device = last_new_device
        self.throughput_down = throughput_down
        self.throughput_up = throughput_up


class ExperiaBoxV10Coordinator(DataUpdateCoordinator[ExperiaBoxV10Data]):
    """Class to manage fetching ExperiaBox v10 data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.api = ExperiaBoxV10Api(
            async_get_clientsession(hass),
            entry.data[CONF_HOST],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        self.track_wired_devices = (entry.options or {}).get(CONF_TRACK_WIRED_DEVICES, False)
        self._last_traffic_info: TrafficInfo | None = None
        self._last_traffic_time: float | None = None
        self._known_macs: set[str] | None = None
        self._last_new_device_time: float | None = None
        self._last_new_device_info: str | None = None

    def _calculate_throughput(self, current_time: float, current_traffic: TrafficInfo) -> tuple[float, float]:
        """Calculate download and upload throughput."""
        throughput_down = 0.0
        throughput_up = 0.0

        if self._last_traffic_info and self._last_traffic_time:
            time_delta = current_time - self._last_traffic_time
            if time_delta > 0:
                bytes_down_delta = (
                    current_traffic.bytes_received - self._last_traffic_info.bytes_received
                )
                bytes_up_delta = (
                    current_traffic.bytes_sent - self._last_traffic_info.bytes_sent
                )

                if bytes_down_delta >= 0 and bytes_up_delta >= 0:
                    throughput_down = bytes_down_delta / time_delta
                    throughput_up = bytes_up_delta / time_delta

        self._last_traffic_info = current_traffic
        self._last_traffic_time = current_time
        return throughput_down, throughput_up

    def _detect_new_devices(self, current_time: float, devices: list[Device]) -> bool:
        """Track devices and detect newly connected ones."""
        current_macs = {device.mac for device in devices}
        if self._known_macs is None:
            # First run, just populate known devices
            self._known_macs = current_macs
            return False
            
        new_macs = current_macs - self._known_macs
        if new_macs:
            self._known_macs.update(new_macs)
            # Find first new device to show in sensor
            for device in devices:
                if device.mac in new_macs:
                    self._last_new_device_info = f"{device.name or device.mac} ({device.mac})"
                    self._last_new_device_time = current_time
                    break

        if self._last_new_device_time:
            # Alert stays active for 5 minutes
            return current_time - self._last_new_device_time < 300
            
        return False

    async def _async_update_data(self) -> ExperiaBoxV10Data:
        """Update data via library."""
        try:
            _LOGGER.debug("Fetching data from ExperiaBox v10")
            results = await asyncio.gather(
                self.api.get_devices(self.track_wired_devices),
                self.api.get_router_info(),
                self.api.get_wan_info(),
                self.api.get_traffic_info(),
                self.api.get_guest_wifi_enabled(),
                return_exceptions=True,
            )
            
            # Check for critical failures on first run
            if self.data is None:
                for res in results:
                    if isinstance(res, Exception):
                        raise res
                        
            # Unpack results with fallback to previous data on partial failures
            devices = results[0] if not isinstance(results[0], Exception) else getattr(self.data, "devices", [])
            router_info = results[1] if not isinstance(results[1], Exception) else getattr(self.data, "router_info", None)
            wan_info = results[2] if not isinstance(results[2], Exception) else getattr(self.data, "wan_info", None)
            traffic_info = results[3] if not isinstance(results[3], Exception) else getattr(self.data, "traffic_info", None)
            guest_wifi_enabled = results[4] if not isinstance(results[4], Exception) else getattr(self.data, "guest_wifi_enabled", False)

            # Log warnings for any partial failures
            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    _LOGGER.warning("Partial update failure for endpoint index %d: %s", idx, res)

            _LOGGER.debug("Successfully fetched data from ExperiaBox v10")

            current_time = time.monotonic()
            throughput_down, throughput_up = self._calculate_throughput(current_time, traffic_info) if traffic_info else (0.0, 0.0)
            new_device_detected = self._detect_new_devices(current_time, devices) if devices else False

            return ExperiaBoxV10Data(
                devices,
                router_info,
                wan_info,
                traffic_info,
                guest_wifi_enabled,
                new_device_detected,
                self._last_new_device_info,
                throughput_down,
                throughput_up,
            )
        except Exception as exception:
            _LOGGER.exception("Error communicating with ExperiaBox v10")
            raise UpdateFailed(
                f"Error communicating with ExperiaBox: {exception}"
            ) from exception
