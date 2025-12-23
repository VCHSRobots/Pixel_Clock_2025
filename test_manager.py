# test_manager.py - Centralized Test Configuration Logic
# Dec 2025

import json
import time

_config = None

def _load_config():
    global _config
    if _config is not None:
        return _config
    
    try:
        with open("test.json", "r") as f:
            _config = json.load(f)
    except:
        _config = {}
        
    return _config

def get_config():
    return _load_config()

def is_test_mode():
    return _load_config().get("TestMode", False)

def is_ntp_disabled():
    cfg = _load_config()
    # Logic: Must be in TestMode AND DisableNTP must be true
    return cfg.get("TestMode", False) and cfg.get("DisableNTP", False)

def apply_test_time(rtc, settings_mgr):
    """
    Applies the test time from configuration to the RTC if TestMode is active.
    Returns True if time was coerced, False otherwise.
    """
    cfg = _load_config()
    if not cfg.get("TestMode", False):
        return False
        
    t0 = cfg.get("time0", "12:00")
    d0 = cfg.get("date0", "2025-01-01")
    
    # We need to print, so return the year ? Or just do it.
    print("Startup: ** TEST MODE ACTIVE **")
    
    if ":" in t0 and "-" in d0:
        try:
            th, tm = map(int, t0.split(":"))
            ty, k_m, k_d = map(int, d0.split("-"))
            
            # We need to correct for Timezone and DST to set the RTC (which expects UTC)
            # relative to the user's desired "Local Equivalent" time.
            
            # Avoid top-level circular import
            import time_keeper 
            
            offset = settings_mgr.get("timezone_offset", -8)
            
            # Target Local Seconds
            target_tuple = (ty, k_m, k_d, th, tm, 0, 0, 0)
            target_seconds = time.mktime(target_tuple)
            
            # Compensate DST
            is_dst = time_keeper.is_dst_us(target_seconds)
            dst_adj = 3600 if is_dst else 0
            
            # UTC = Target - Offset - DST
            utc_seconds = target_seconds - (offset * 3600) - dst_adj
            utc_tuple = time.localtime(utc_seconds)
            
            rtc.set_time(utc_tuple)
            print(f"Startup: Test Time {d0} {t0} -> RTC UTC (Off={offset}, DST={is_dst})")
            
            # Return valid year to update main loop variable if needed
            return utc_tuple[0]
            
        except Exception as e:
            print(f"Startup: Error applying test time: {e}")
            
    return False
