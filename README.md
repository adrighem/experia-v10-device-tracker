# KPN Experia Box v10 Integration for Home Assistant

This is a comprehensive Home Assistant integration for the ZTE H369A (Experia Box v10) router, primarily used for [KPN Internet](https://www.kpn.com/internet) connections in the Netherlands (also used by Telfort). It goes beyond simple device tracking to provide full router management, network health monitoring, and real-time traffic statistics.

**Note:** This is a modernized and significantly expanded fork of the original [experia-v10-device-tracker](https://github.com/kadima-tech/experia-v10-device-tracker). It follows the latest Home Assistant standards, including UI-based configuration (Config Flow) and efficient asynchronous data fetching.

## Features

- **Comprehensive Device Tracking:** Monitor presence of all LAN and WLAN connected devices.
- **Network Health & Diagnostics:**
  - External IP Address tracking.
  - WAN Connectivity status.
  - WAN Link Status (Up/Down).
  - Router Uptime.
- **Real-time Traffic Statistics:**
  - Total Data Received/Sent (byte-level accuracy).
  - Live Download/Upload Speeds (throughput calculation).
  - Active Client Count.
- **Router Management:**
  - Remote Reboot functionality.
  - Guest Wi-Fi toggle control.
- **Security Alerts:**
  - Automatic detection of new devices joining the network.
  - "Last New Device" sensor with MAC and name information.
- **Modern Architecture:**
  - **UI-based Configuration:** Setup via the Home Assistant Integrations UI.
  - **Asynchronous:** Built on `aiohttp` for non-blocking communication.
  - **Organized Entities:** All entities are logically grouped under a single "H369A" device.

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant.
2. Click on "Integrations".
3. Click on the three dots in the top right corner and select "Custom repositories".
4. Add this repository URL: `https://github.com/adrighem/kpn-experia-v10-integration` and category "Integration".
5. Find "ExperiaBox v10" and click "Download".
6. Restart Home Assistant.

### Manual

1. Download the latest release.
2. Copy the `custom_components/experiaboxv10` folder to your `/config/custom_components/` directory.
3. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings** -> **Devices & Services**.
2. Click **Add Integration**.
3. Search for **ExperiaBox v10**.
4. Enter your router's IP address, username, and password.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

* **Sjaak Meulen** - *Initial implementation* - [sjaakiejj](https://github.com/sjaakiejj)
* [Mark van den Berg](https://community.home-assistant.io/t/device-tracker-for-arcadyan-vgv7519-router-experia-box-v8/29362) - *Original Experia Box V8 script*
