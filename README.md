# KPN Experia Box v10 Integration

<p align="center">
  <img src="custom_components/experiaboxv10/brand/icon.png" width="150" alt="KPN Experia Box v10 Logo">
</p>

*Because your ISP-provided router doesn't have to be a black box.*

This integration wrangles your ZTE H369A (Experia Box v10) into Home Assistant. It speaks both the old language and the shiny new "KPN Software" (V10.C.26.02.06+) dialect, giving you full visibility and control over your home network.

**Note:** This is a modernized and significantly expanded fork of the original [experia-v10-device-tracker](https://github.com/kadima-tech/experia-v10-device-tracker).

## 🚀 What it does

*   **Who's home?** Tracks all connected devices (wired and wireless) using robust network topology traversal. No more guessing.
*   **Speed & Greed:** Monitors real-time download/upload speeds and total data consumption.
*   **Vitals:** Keeps an eye on your External IP, WAN link status, active client count, and router uptime.
*   **Intruder Alert:** Triggers a diagnostic sensor when a wild new device appears on your network.
*   **The Big Buttons:** Reboot the router or toggle Guest Wi-Fi directly from your dashboard.

## 📦 Installation

Grab it via [HACS](https://hacs.xyz/):

1. HACS > Integrations > 3 dots (top right) > Custom repositories.
2. Add `https://github.com/adrighem/kpn-experia-v10-integration` as an **Integration**.
3. Download "ExperiaBox v10".
4. Restart Home Assistant.

## ⚙️ Configuration

Forget YAML. This is the future.

1. Go to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **ExperiaBox v10**.
3. Punch in your router's IP, username (usually `admin`), and password.
4. Enjoy the data.
