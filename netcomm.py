# netcomm.py - Network Communication Manager
# Dec 2025

import network
import uasyncio as asyncio
import config
import settings_manager
import ntptime

class NetworkManager:
    _instance = None
    
    @classmethod
    def get_manager(cls):
        if cls._instance is None:
            cls._instance = NetworkManager()
        return cls._instance

    def __init__(self):
        if NetworkManager._instance is not None:
            raise RuntimeError("NetworkManager Singleton")
        NetworkManager._instance = self
        
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        # Attempt power management config
        try:
            self.wlan.config(pm = 0xa11140)
        except:
            pass
            
        self._monitor_task = None
        self.ssid = ""
        self.password = ""
        self._load_credentials()

    def _load_credentials(self):
        settings = settings_manager.get_settings_manager()
        self.ssid = settings.get("ssid", "")
        self.password = settings.get("password", "")
        
        if not self.ssid:
            self.ssid = config.SSID
            self.password = config.PASSWORD

    def start(self):
        """Start the background connection monitor."""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._maintain_connection())

    async def _maintain_connection(self):
        """Background loop to maintain connection."""
        CHECK_INTERVAL = 4 * 3600 # 4 hours
        RETRY_INTERVAL = 30 # seconds
        
        while True:
            # Check SSID Validity
            if not self.ssid or self.ssid.strip() == "":
                # Invalid SSID, just wait
                # We could periodically re-load settings to see if user set it?
                # For now just sleep long
                self._load_credentials()
                if not self.ssid:
                    await asyncio.sleep(60) 
                    continue

            if self.is_connected():
                # All good, sleep for a long time
                await asyncio.sleep(CHECK_INTERVAL)
            else:
                # Disconnected, attempt connect
                print(f"NetComm: Attempting connection to {self.ssid}...")
                success = await self._attempt_connection()
                if success:
                    print(f"NetComm: Connected. IP: {self.get_ip()}")
                else:
                    print("NetComm: Connection failed/timed out. Retrying...")
                    await asyncio.sleep(RETRY_INTERVAL)
            
            # Additional small sleep to prevent tight loop if something weird happens (though branches handle it)
            await asyncio.sleep(1)

    async def _attempt_connection(self):
        if not self.ssid: return False
        
        try:
            self.wlan.connect(self.ssid, self.password)
            
            # Wait for connection
            max_wait = 20
            while max_wait > 0:
                if self.wlan.status() < 0 or self.wlan.status() >= 3:
                    break
                max_wait -= 1
                await asyncio.sleep(1)
                
            if self.wlan.status() != 3:
                return False
                
            return True
        except Exception as e:
            print("NetComm Error:", e)
            return False

    def is_connected(self):
        return self.wlan.isconnected() and self.wlan.status() == 3

    def get_ip(self):
        if self.is_connected():
            return self.wlan.ifconfig()[0]
        return "0.0.0.0"

    def get_status_str(self):
        # Update credentials just in case
        self._load_credentials()
        if not self.ssid:
            return "No SSID Configured"
            
        if self.is_connected():
            return f"IP: {self.get_ip()}"
        return f"Connecting: {self.ssid}"

    def sync_time(self):
        """Standard NTP Sync"""
        if self.is_connected():
            try:
                ntptime.set_rtc_time()
            except:
                pass

def get_netcomm():
    return NetworkManager.get_manager()
