# ExperiaBox v10 Integration

## Development Workflow

### Testing and Reproduction
To ensure robust dependency management and avoid environment conflicts, use `uv` for running tests and reproduction scripts.

**Run tests:**
```bash
PYTHONPATH=. uv run --with aiohttp --with voluptuous pytest
```

**Run reproduction scripts:**
```bash
uv run --with aiohttp --with voluptuous <script_name>.py
```

## Legacy Support Cleanup
- **Status:** Completed.
- **Changes:**
    - Removed legacy LUA/XML API logic and fallback mechanism from `api.py`.
    - Simplified `api.py` by removing unused imports (`re`, `datetime`, `sha256`, `xml.etree.ElementTree`).
    - Fixed a bug in wired device detection where "wlan" tags were incorrectly matched as "lan".
    - Updated `test/test_api.py` to focus on the modern JSON API and fixed mock issues.
    - Verified all tests pass using `uv`.

## Router Device Support
- **Status:** Completed.
- **Changes:**
    - Expanded `ExperiaBoxV10Api` to fetch router metadata (Model, Version, Serial, Uptime) via the JSON API.
    - Updated `ExperiaBoxV10Coordinator` to fetch and store both device trackers and router info using a new `ExperiaBoxV10Data` class.
    - Implemented `device_info` in all entities to group them under a single "Experia Box V10" device.
    - Added a new `sensor` platform providing a Router Uptime entity.
    - Updated `__init__.py` to load the new `sensor` platform.
    - Enhanced test mocks in `conftest.py` and added `test/test_sensor.py`.
    - Verified all 15 tests pass.

## Phase 1: Network Health
- **Status:** Completed.
- **Changes:**
    - Expanded `ExperiaBoxV10Api` with `get_wan_info` to fetch external IP, connectivity status, and WAN link status.
    - Updated `ExperiaBoxV10Coordinator` to fetch and store WAN info.
    - Implemented `binary_sensor` platform with a Connectivity entity.
    - Expanded `sensor` platform with External IP and WAN Link Status entities.
    - Updated `__init__.py` to load the `binary_sensor` platform.
    - Added tests for the new API method, coordinator updates, and new entities.
    - Verified all 17 tests pass.

## Phase 2: Traffic & Performance
- **Status:** Completed.
- **Changes:**
    - Expanded `ExperiaBoxV10Api` with `get_traffic_info` to fetch byte and packet counters via `sah.Device.WAN.getStatistics`.
    - Updated `ExperiaBoxV10Coordinator` to calculate real-time throughput (Download/Upload speeds) based on byte counter deltas.
    - Added sensors for Data Received/Sent (bytes), Download/Upload Speed (B/s), and Active Client Count.
    - Updated test suite to verify throughput calculation and new traffic sensors.
    - Verified all 19 tests pass.

## Architectural Refactor
- **Status:** Completed.
- **Changes:**
    - **API Layer:** Consolidated repetitive request logic into a private `_request` method in `api.py`. Added session caching and re-authentication handling to improve performance and reliability.
    - **Entity Base:** Created `entity.py` with `ExperiaBoxV10Entity` base class. This centralizes `device_info` logic, ensuring consistency across all platforms and reducing code duplication by ~30% in entity files.
    - **Coordinator Optimization:** Updated `ExperiaBoxV10Coordinator` to use `asyncio.gather` for parallel data fetching, reducing poll duration.
    - **Cleanup:** Improved imports and removed redundant properties across `device_tracker.py`, `sensor.py`, and `binary_sensor.py`.
    - **Verification:** All 19 tests pass successfully after refactoring.

## Phase 3: Router Management
- **Status:** Completed.
- **Changes:**
    - Expanded `ExperiaBoxV10Api` with `reboot`, `get_guest_wifi_enabled`, and `set_guest_wifi` methods.
    - Updated `ExperiaBoxV10Coordinator` to track Guest Wi-Fi status in the shared data object.
    - Implemented `button` platform with a **Reboot** entity.
    - Implemented `switch` platform with a **Guest Wi-Fi** toggle entity.
    - Refactored all entity platforms to use the common `ExperiaBoxV10Entity` base class.
    - Added tests for button and switch platforms and updated existing tests to verify Guest Wi-Fi state management.
    - Verified all 21 tests pass.

## Phase 4: Security Alerts
- **Status:** Completed.
- **Changes:**
    - Updated `ExperiaBoxV10Coordinator` to track known MAC addresses and detect new devices.
    - Implemented **New Device Detected** `binary_sensor` which stays active for 5 minutes after a new device is found.
    - Implemented **Last New Device** `sensor` displaying the name and MAC of the most recently joined device.
    - Added logic to prevent false alerts on the first poll after integration startup.
    - Updated tests to verify the detection logic and sensor states.
    - Verified all 22 tests pass.

## Known Issues

### Config Flow 500 Error
- **Status:** Resolved.
- **Symptom:** "500 Internal Server Error" when opening the configuration flow.
- **Root Cause:** `OptionsFlowHandler.__init__` was passing `config_entry` to `super().__init__`, which is no longer supported in modern Home Assistant versions.
- **Resolution:** Removed the redundant `__init__` method from `OptionsFlowHandler`. The `config_entry` is handled by the base class.
