import json
import os

class SettingsManager:
    DEFAULT_SETTINGS = {
        "brightness": 0.25,
        "mode": 0, # HH_MM
        "12_hour_mode": False,
        "seconds_color": (0, 0, 255),  # Default blue
        "digit_color": (255, 255, 255), # Default white
        "colon_color": (255, 255, 255),  # Default white
        "ssid": "",
        "password": "",
        "timezone_offset": -8 # Default PST
    }
    
    FILE_NAME = "settings.json"
    _instance = None

    @classmethod
    def inst(cls):
        """Returns the singleton instance of the settings manager."""
        return cls._instance

    def __init__(self):
        if SettingsManager._instance is not None:
            raise RuntimeError("SettingsManager already initialized")
        SettingsManager._instance = self
        
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        """Load settings from the file system."""
        try:
            # check if file exists
            try:
                os.stat(self.FILE_NAME)
            except OSError:
                # File doesn't exist, save defaults
                self.save()
                return

            with open(self.FILE_NAME, "r") as f:
                loaded = json.load(f)
                # update current settings with loaded ones, preserving defaults for missing keys
                self.settings.update(loaded)
                print(f"SettingsManager: Loaded settings: {self.settings}")
        except (OSError, ValueError) as e:
            print(f"Error loading settings: {e}")
            # If load fails, we stick to current (default) settings
            
    def save(self):
        """Save current settings to the file system."""
        try:
            with open(self.FILE_NAME, "w") as f:
                json.dump(self.settings, f)
        except OSError as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Set a setting value and save to disk."""
        self.settings[key] = value
        self.save()

    def update(self, new_settings):
        """Update multiple settings and save once."""
        self.settings.update(new_settings)
        print(f"SettingsManager: Settings updated: {new_settings}")
        self.save()

def get_settings_manager():
    """Get the singleton instance of the settings manager. Create it if it doesn't exist."""
    s = SettingsManager.inst()
    if s is None:
        try:
            s = SettingsManager()
        except RuntimeError:
            s = SettingsManager.inst()
    return s
