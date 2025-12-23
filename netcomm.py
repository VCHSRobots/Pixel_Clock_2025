# netcomm.py - Network Communication Manager
# Dec 2025

import network
import uasyncio as asyncio
import settings_manager
import ntptime
import persistent_logger

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
        self.device_name = "NeoDisplay Clock"
        self._load_credentials()
        # Hostname setting moved to async task to prevent blocking startup

    def _load_credentials(self):
        # New Logic: Load from ssid.json
        import json
        self.ssid = ""
        self.password = ""
        try:
            with open("ssid.json", "r") as f:
                data = json.load(f)
                self.ssid = data.get("ssid", "")
                self.password = data.get("password", "")
                self.device_name = data.get("name", "NeoDisplay Clock")
        except:
            # File doesn't exist or error
            pass
        
    def has_credentials(self):
        """Returns True if a valid SSID is configured."""
        return bool(self.ssid and self.ssid.strip())

    def start(self):
        """Start the background connection monitor if credentials exist."""
        if not self.has_credentials():
            print("NetComm: No credentials. Network Monitor not started.")
            return

        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._maintain_connection())

    async def _maintain_connection(self):
        """Background loop to maintain connection."""
        # Hostname setting disabled for stability
        # safe_name = "".join(c if c.isalnum() else "-" for c in self.device_name).strip("-")
        # if not safe_name: safe_name = "NeoDisplay-Clock"
        
        # print(f"NetComm: Setting hostname to '{safe_name}' (Async)")

        # # Attempt to set hostname using multiple methods
        # import network
        # try:
        #     network.hostname(safe_name)
        # except:
        #     pass
            
        # try:
        #     self.wlan.config(dhcp_hostname=safe_name)
        # except:
        #     pass

        # try:
        #     self.wlan.config(hostname=safe_name)
        # except:
        #     pass

        CHECK_INTERVAL = 30 # Check every 30 seconds instead of hours
        RETRY_INTERVAL = 30 # seconds
        
        while True:
            try:
                # Check SSID Validity
                if not self.ssid or self.ssid.strip() == "":
                    # Invalid SSID, just wait
                    self._load_credentials()
                    if not self.ssid:
                        await asyncio.sleep(60) 
                        continue
    
                if self.is_connected():
                    # All good, sleep for a bit
                    await asyncio.sleep(CHECK_INTERVAL)
                else:
                    # Disconnected, attempt connect
                    persistent_logger.log(f"NetComm: Connection lost/check failed. Reconnecting to {self.ssid}...")
                    print(f"NetComm: Attempting connection to {self.ssid}...")
                    success = await self._attempt_connection()
                    if success:
                        msg = f"NetComm: Connected. IP: {self.get_ip()}"
                        print(msg)
                        persistent_logger.log(msg)
                    else:
                        print("NetComm: Connection failed/timed out. Retrying...")
                        await asyncio.sleep(RETRY_INTERVAL)
                
                # Additional small sleep to prevent tight loop if something weird happens
                await asyncio.sleep(1)
            except Exception as e:
                err = f"NetComm Error in Loop: {e}"
                print(err)
                persistent_logger.log(err)
                await asyncio.sleep(30) # Wait a bit before retrying loop

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
        # Optimized: Do NOT reload credentials here.
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
