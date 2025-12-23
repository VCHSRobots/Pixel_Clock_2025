# Pixel Clock 2025

A highly customizable, web-connected NeoPixel matrix clock powered by a Raspberry Pi Pico W. This project features accurate timekeeping via NTP and RTC, a responsive Web UI for configuration, robust alarm scheduling, and smooth animations.

## Installation & Upgrading

### First-Time Installation
If you are building a new clock from scratch:
1.  **Flash MicroPython**: Install the latest MicroPython firmware for Raspberry Pi Pico W.
2.  **Upload Code**: Connect via USB and use **Thonny** (or another REPL-capable IDE) to upload all project files (`.py`, `.html`, `.js`, etc.) to the root directory of the Pico W.
3.  **Power On**: The clock will automatically enter **Setup Mode** on its first run (see below).

### Upgrading an Existing Clock
If you have an older clock or are updating the software:
1.  **Connect via USB**: Plug the Pico W into your computer.
2.  **Open Thonny**: Ensure you can access the files on the device.
3.  **Wipe Old Files**: It is highly recommended to **delete all existing files** on the device to ensure a clean text.
    - You can do this manually in the file explorer or via REPL.
4.  **Upload New Code**: Upload the new set of files.
5.  **Restart**: Reset the board. If `ssid.json` was deleted, it will enter Setup Mode.

## Setup & Configuration

### Startup Behavior
- **Setup Mode**: Automatically entered ONLY if `ssid.json` is missing **AND** the system time is invalid (e.g., fresh install or RTC battery failure).
- **Offline Mode**: If `ssid.json` is missing but the time is valid (RTC backup), the clock enters Offline Mode immediately.
- **Normal Operation**: Connects to the saved WiFi network found in `ssid.json`.

### Manual Setup Entry
If you need to reconfigure the WiFi without wiping files, you can force Setup Mode:
1.  **Button**: Hold the physical button for **>10 seconds**.
2.  **REPL**: Connect via USB/Thonny and run:
    ```python
    import admin as a
    a.reset()
    a.run()
    ```
    *(Note: Older clocks without buttons must use this REPL method).*

### The Setup Process
In **Setup Mode**, the clock functions as a WiFi Access Point.
1.  **Connect**: Use your phone or computer to connect to the clock's WiFi network (Open/No Password).
2.  **Configure**: You should be redirected to a configuration portal.
3.  **Select Network**: Choose your home WiFi SSID, enter the password, and give yor clock a custom Name (e.g., "Living Room").
4.  **Save**: The clock will reboot and connect to your network.

## Usage Guide

### Getting Started
Once connected to WiFi, the clock automatically synchronizes time via NTP.
- **Finding the IP Address**:
    - **With Button**: Press the button for ~1 second. The IP address will scroll on the display.
    - **No Button**: Cycle the power. The IP address scrolls on startup.
- **Offline Mode**: If WiFi is unavailable but the RTC battery is good, the clock operates normally using the backup time.

### Web Interface
Access the dashboard by entering the clock's IP address in your browser.
- **Status**: Live view of time, date, and logs.
- **Settings**: Change brightness, colors, and 12/24h mode.
- **alarms**: Manage daily/weekly alarms.
- **Animations**: Trigger demo modes.

### Physical Controls
- **Short Press**: Scroll Status (IP Address / Connection).
- **Long Press (>2s)**: Enter Brightness Mode. Hold again to cycle brightness; release to save.
- **Very Long Press (>10s)**: Factory Reset (Enters Setup Mode).

## Features

- **Precision Timekeeping**: Synchronizes with NTP servers over WiFi and maintains time with a DS3231 RTC module when offline.
- **Advanced Alarm System**: 
    - Supports Daily, Hourly, Weekly, and One-shot alarms.
    - JSON-based scheduling with "disabled spans" and specific "skip hours".
    - Different action types: Scrolling text, blinking display.
    - "Critical Time" mode that overrides display during alarms.
- **Customizable Display**:
    - 12/24 Hour logic.
    - Adjustable Colors for Digits, Colon, and Seconds.
    - Orientation support (Standard / Rotated 180°).
    - "Night Mode" capable (via brightness settings).

## Hardware Requirements

- **Raspberry Pi Pico W**: The brains of the operation.
- **NeoPixel Matrix**: Currently configured for 8x32 (Zig-Zag layout), generally WS2812B.
- **DS3231 RTC**: I2C Real Time Clock module for backup timekeeping.
- **Push Button**: Momentary switch for physical control (GPIO 17).
- **Power Supply**: Clean 5V power supply capable of driving the LED matrix (Amperage depends on matrix size).

### Wiring References (Default)
- **NeoPixels**: GPIO 16
- **Button**: GPIO 17
- **RTC (I2C)**: Auto-detected on standard behaviors (often GPIO 0/1 or 4/5).

## License

[MIT](LICENSE)
