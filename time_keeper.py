# time_keeper.py - Central Time Management
# Dec 2025

import time
import rtc_module
import settings_manager
import netcomm
import persistent_logger

class TimeKeeper:
    _instance = None
    
    @classmethod
    def get_keeper(cls):
        if cls._instance is None:
            cls._instance = TimeKeeper()
        return cls._instance

    def __init__(self):
        if TimeKeeper._instance is not None:
            raise RuntimeError("TimeKeeper Singleton")
        TimeKeeper._instance = self
        
        self.rtc = rtc_module.get_rtc()
        self.settings = settings_manager.get_settings_manager()
        self.last_ntp_check = 0
        self.last_sync_attempt = 0
        self.SYNC_RETRY_COOLDOWN = 15 # Seconds to wait before retrying failed sync
        self.NTP_INTERVAL = 86400 # 24 hours
        
    def get_time(self):
        """
        Returns (h, m, s) corrected for timezone/DST, 
        or a string error message ("RTC ERR", "No NTP").
        Source of Truth: DS3231 (via rtc_module).
        """
        # 1. Check RTC Hardware
        if not self.rtc.is_working():
            return "RTC ERR"
            
        # 2. Get Raw Time (UTC) from RTC
        try:
            # rtc.get_time returns: (year, month, day, hour, min, sec, wday, doy)
            t_rtc = self.rtc.get_time()
        except OSError:
            return "RTC ERR"
            
        year = t_rtc[0]
        
        # 3. Validate Year
        if year < 2020:
             # Time is invalid.
             # Only attempt sync if cooldown passes
             now = time.ticks_ms()
             # Initial check: last_sync_attempt is 0
             if self.last_sync_attempt == 0 or time.ticks_diff(now, self.last_sync_attempt) > (self.SYNC_RETRY_COOLDOWN * 1000):
                self.last_sync_attempt = now
                self._attempt_sync()
                # Re-read
                try:
                    t_rtc = self.rtc.get_time()
                    year = t_rtc[0]
                except:
                    return "RTC ERR"
             
             if year < 2020:
                 return "No NTP"

        # 4. Check for Daily NTP Sync (if time is valid)
        # We cannot use time.time() for interval check if system time isn't set!
        # Use ticks_ms() for elapsed time? Or just re-sync if it's been a long while?
        # Actually, since we have the RTC time, we can use THAT to determine if we should sync.
        # But converting RTC to epoch for diffing is fine.
        
        try:
            # We assume t_rtc is UTC.
            now_epoch = time.mktime(t_rtc)
            if (now_epoch - self.last_ntp_check > self.NTP_INTERVAL) and (self.last_ntp_check > 0):
                 # Only check if connected
                 if netcomm.get_netcomm().is_connected():
                    self._attempt_sync()
            elif self.last_ntp_check == 0:
                 self.last_ntp_check = now_epoch # Initialize
        except:
            pass

        # 5. Apply Offsets (Timezone + DST)
        # We use mktime/localtime ONLY for math, not for source of truth.
        
        utc_seconds = time.mktime(t_rtc)
        
        # Add Timezone Offset (hours -> seconds)
        offset = self.settings.get("timezone_offset", -8)
        local_seconds = utc_seconds + (offset * 3600)
        
        # Check DST (Always US Rules)
        # We need to know if the *local standard time* falls in DST.
        if self._is_dst_us(local_seconds):
            local_seconds += 3600
        
        # Convert back to tuple
        local_t = time.localtime(local_seconds)
        # (y, m, d, h, m, s, wday, doy)
        
        return local_t[3], local_t[4], local_t[5]

    def _attempt_sync(self):
        """
        Attempts to sync system time from NTP, then sets RTC.
        """
        try:
            if netcomm.get_netcomm().is_connected():
                netcomm.get_netcomm().sync_time()
                # Update last check time based on NEW time
                try:
                    t_new = self.rtc.get_time()
                    self.last_ntp_check = time.mktime(t_new)
                    print(f"TimeKeeper: NTP Sync Successful. Time: {t_new}")
                except:
                    pass
                return True
        except Exception as e:
            persistent_logger.log(f"TimeKeeper Sync Logic Error: {e}")
            pass
        return False

    def _is_dst_us(self, t_seconds):
        """
        Check if time (epoch seconds) is in DST (US Rules).
        2nd Sunday in March to 1st Sunday in Nov.
        """
        t = time.localtime(t_seconds)
        year = t[0]
        month = t[1]
        day = t[2]
        hour = t[3]
        
        if month < 3 or month > 11:
            return False
        if month > 3 and month < 11:
            return True
            
        # March: Starts 2nd Sunday @ 2am
        if month == 3:
            # Calculate 2nd Sunday
            # 1st day of March is...
            # We can use mktime to find weekday of March 1st.
            # 0=Mon, 6=Sun
            wday_mar1 = time.localtime(time.mktime((year, 3, 1, 0, 0, 0, 0, 0)))[6]
            
            # Days until 1st Sunday
            # if wday=6 (Sun), invalid for "previous", it IS sunday.
            # dist to sunday: (6 - wday) % 7
            # If Mar 1 is Sun (6), dist=0. 1st Sun is 1. 2nd Sun is 8.
            # If Mar 1 is Mon (0), dist=6. 1st Sun is 7. 2nd Sun is 14.
            days_to_sun = (6 - wday_mar1) % 7
            first_sun = 1 + days_to_sun
            second_sun = first_sun + 7
            
            if day < second_sun: return False
            if day > second_sun: return True
            # On the day
            return hour >= 2
            
        # November: Ends 1st Sunday @ 2am
        if month == 11:
            wday_nov1 = time.localtime(time.mktime((year, 11, 1, 0, 0, 0, 0, 0)))[6]
            days_to_sun = (6 - wday_nov1) % 7
            first_sun = 1 + days_to_sun
            
            if day < first_sun: return True
            if day > first_sun: return False
            # On the day (switch back happens at 2am, effectively repeats 1am-2am)
            # Standard logic: before 2am is DST.
            return hour < 2
            
        return False

def get_time():
    """Proxy for backward compatibility if needed, but we should use the singleton."""
    return TimeKeeper.get_keeper().get_time()

def get_time_keeper():
    return TimeKeeper.get_keeper()
