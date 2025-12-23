# Pixel Clock 2025

A highly customizable, web-connected NeoPixel matrix clock powered by a Raspberry Pi Pico W. This project features accurate timekeeping via NTP and RTC, a responsive Web UI for configuration, robust alarm scheduling, and smooth animations.

> [!IMPORTANT]
> **Setup Mode** will be automatically entered for a new clock. For an existing clock, setup mode can be entered by a long button press (>10s), or by gaining access to the REPL and issuing these commands:
> ```python
> import admin as a
> a.reset()
> a.run()
> ```
> Older clocks can also be reset using these same commands with `admin`.
>
> In **Setup Mode**, the clock creates its own WiFi Access Point. Connect to this network (no password required) using your phone or computer. You will be automatically redirected to a configuration page where you can select your local WiFi network, enter the password, and give your clock a custom name.

## Features

- **Precision Timekeeping**: Synchronizes with NTP servers over WiFi and maintains time with a DS3231 RTC module when offline.
- **Web Interface**: responsive web dashboard to:
    - View live status (Time, Date, IP).
    - Configure display settings (Brightness, Colors, Orientation).
    - Manage alarms.
    - Trigger animations.
- **Advanced Alarm System**: 
    - Supports Daily, Hourly, Weekly, and One-shot alarms.
    - JSON-based scheduling with "disabled spans" and specific "skip hours".
    - Different action types: Scrolling text, blinking display.
    - "Critical Time" mode that overrides display during alarms.
- **Physical Controls**: Multi-function button for:
    - **Short Press**: Scroll Status (IP Address / Connection State).
    - **Long Press (>2s)**: Enter Brightness Adjustment Mode (hold again to cycle brightness).
    - **Very Long Press (>10s)**: Factory Reset (clears WiFi credentials and reboots).
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

## Installation

1. **Flash MicroPython**: Install the latest MicroPython firmware for Raspberry Pi Pico W.
2. **Upload Code**: Copy all `.py`, `.html`, and `.js` files to the root of the Pico W.
3. **First Run**:
    - When powered on for the first time (or after a reset), the clock will enter **Setup Mode** if no `ssid.json` is found.
    - The clock will likely display messages or indicators if not connected.
    - Connect to the AP (if implemented) or manually create `ssid.json` with WiFi credentials.

### `ssid.json` Format
```json
{
    "ssid": "YOUR_WIFI_SSID",
    "password": "YOUR_WIFI_PASSWORD",
    "name": "Living Room Clock"
}
```

### Getting Started
Once the clock connects to the internet, it will automatically synchronize the time. You can then modify the clock's settings through the web interface.

**Finding the IP Address**: On power-up, or when you press the button for about 1 second, the clock will scroll its assigned IP address. Enter this IP into your browser to access the configuration page. From there, you can modify all settings (except the device name).

> [!NOTE]
> Older clocks do not have a button. To see the IP address scroll on these devices, simply cycle the power.

## Usage

### Web Interface
Navigate to the clock's IP address in a browser.
- **Status Panel**: Shows current time and system logs.
- **Settings**: Adjust colors, blinking, and brightness. Changes are persisted to `settings.json`.
- **Animations**: Manually trigger rainbow, scrolling text, or bouncing box demos.
- **Alarms**: View and manage the list of active alarms.

### Button Controls
- **Click**: Scrolls connection status. Red = Offline, Blue = IP Address.
- **Hold (2-10s)**: "Adj BRT" appears. Release, then hold again to cycle brightness up/down. Release to save.
- **Hold (10s+)**: "RESET" appears. Clears WiFi settings and reboots. Use with caution.

## API Documentation

The Web Server exposes a REST-like API for integration.

### `GET /api/status`
Returns full system status.
```json
{
    "time": [14, 30, 05],
    "date": {"year": 2025, ...},
    "brightness": 0.5,
    "rotation": false,
    ...
}
```

### `POST /api/settings`
Update configuration. Partial updates allowed.
**Payload:**
```json
{
    "brightness": 0.8,
    "color": "#FF0000",
    "twelve_hour": true,
    "rotation": true
}
```

### `POST /api/animation`
Trigger immediate feedback animations.
**Payload:**
```json
{
    "name": "scroll_custom",
    "text": "Hello User"
}
```
Supported names: `stop`, `rainbow`, `scroll`, `scroll_custom`, `bounce_red`, `bounce_blue`.

### `GET /api/alarms`
Retrieve list of alarms.

### `POST /api/alarms`
Manage alarms.
**Payload:**
```json
{
    "cmd": "add",
    "alarm": {
        "name": "Wake Up",
        "schedule": { "time": "07:00", "days": [1,2,3,4,5] },
        "action": { "type": "scroll", "payload": { "text": "WAKE UP!" } }
    }
}
```
**Commands**: `add`, `update`, `delete`.

## Alarm Schedule Schema

The alarm system is powerful. Example of a repeating weekday alarm:
```json
{
    "enabled": true,
    "schedule": {
        "frequency": "daily", 
        "time": "08:30",
        "days": [1, 2, 3, 4, 5] 
    },
    "action": {
        "type": "scroll",
        "duration_sec": 300,
        "payload": {
            "text": "Morning Meeting",
            "color": "#00FF00"
        }
    }
}
```
*(Note: `days` 0=Monday, 6=Sunday)*

## License

[MIT](LICENSE)
