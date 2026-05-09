# KPN Experia Box v10 Integration

## Core Mandates
- **GitHub Actions:** Always check GitHub Actions on every commit to ensure all tests and linting execute successfully. Never leave the master branch in a failing state.

## Development Workflow

### Complete Deployment Protocol
When deploying bug fixes or features to the live Home Assistant instance, adhere to this robust protocol to ensure the changes are correctly pulled, loaded, and verified:
1.  **Commit and Push:** Commit your verified local changes and push them to the `master` branch.
    ```bash
    git add . && git commit -m "feat/fix: description" && git push
    ```
2.  **Pull via HACS:** Instruct the live Home Assistant instance to pull the latest `master` via the HACS MCP tool using the specific repository ID.
    `ha_hacs_download(repository_id="1225692090", version="master")`
3.  **Restart Home Assistant:** Restart the core to force it to load the newly downloaded python files.
    `ha_restart(confirm=True)`
4.  **Wait for Boot:** Wait for the Home Assistant web interface to become responsive.
    ```bash
    for i in {1..30}; do curl -s http://192.168.42.2:8123 | grep "Home Assistant" && break; sleep 2; done
    ```
5.  **Allow Integration Setup:** Pause for an additional 10-15 seconds to give the integration time to authenticate with the router and perform its initial data poll.
6.  **Verify State:** Query the live states of critical entities (e.g., `sensor.h369a_active_clients`, `sensor.h369a_uptime`) using the HA MCP tools to ensure the new code is executing correctly and not throwing exceptions or reporting as `unavailable`.

### Test-Driven Development (TDD) Process
To maintain the high quality and test coverage of this integration, we strictly adhere to a Test-Driven Development workflow when adding new features or fixing bugs:
1.  **Write the Test First:** Before making any changes to the component's codebase (`custom_components/experiaboxv10/*.py`), create a test case in the `test/` directory that explicitly tests the desired behavior or reproduces the bug.
2.  **Verify Failure:** Run the test suite and verify that the newly added test fails as expected. This confirms the test is valid and the feature/fix does not yet exist.
3.  **Implement the Minimum Code:** Write the simplest possible code in the component to make the test pass. Focus purely on satisfying the test requirements.
4.  **Verify Success:** Run the entire test suite (`PYTHONPATH=. uv run --with aiohttp --with voluptuous pytest`). All tests, including the new one, must pass.
5.  **Refactor (Optional):** Once tests pass, review the code for clarity, duplication, and architectural elegance (e.g., extracting fat methods, using declarative configurations). Ensure tests still pass after refactoring.

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
