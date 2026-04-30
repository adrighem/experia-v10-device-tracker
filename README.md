# Experia V10 Device Tracker for Home Assistant

This module is a device tracker for Home Assistant. It allows customers of KPN and Telfort to
enable presence detection with their ZTE H369A (Experia V10) box in Home Assistant.

**Note:** This is a modernized fork of the original [experia-v10-device-tracker](https://github.com/kadima-tech/experia-v10-device-tracker).
It has been refactored to follow the latest Home Assistant integration standards, including UI-based configuration (Config Flow) and asynchronous data fetching.

## Features

- **UI-based Configuration:** No more editing `configuration.yaml`. Setup everything via the Home Assistant Integrations UI.
- **Asynchronous:** Uses `aiohttp` for non-blocking communication with the router.
- **Modern Entity Model:** Each tracked device is now a proper `device_tracker` entity in Home Assistant.
- **Auto-Discovery:** New devices are automatically added to Home Assistant as they are discovered by the router.

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant.
2. Click on "Integrations".
3. Click on the three dots in the top right corner and select "Custom repositories".
4. Add this repository URL: `https://github.com/kadima-tech/experia-v10-device-tracker` and category "Integration".
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
