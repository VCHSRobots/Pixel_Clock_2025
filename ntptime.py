try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct

import time
import rtc_module
import persistent_logger    

# Determine Epoch (1970 or 2000)
# Standard NTP is 1900.
# If time.gmtime(0)[0] is 2000, we need delta 1900->2000.
# If time.gmtime(0)[0] is 1970, we need delta 1900->1970.
try:
    if time.gmtime(0)[0] == 2000:
        NTP_DELTA = 3155673600
    else:
        NTP_DELTA = 2208988800
except:
    # Fallback to 2000 epoch (Standard MicroPython)
    NTP_DELTA = 3155673600

# The host to fetch the time from
host = "pool.ntp.org"

def get_ntp_time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(2) # Increased timeout
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
        # print("NTP response len:", len(msg))
    except Exception as e:
        print("NTP Socket Error:", e)
        s.close()
        return 0 # Return 0 on error
    finally:
        s.close()
        
    if len(msg) < 48:
        print("NTP Error: Short response")
        return 0
        
    val = struct.unpack("!I", msg[40:44])[0]
    # LEAP indicator check?
    # print(f"NTP Raw: {val}")
    
    # Sanity check: NTP time must be > 2024 (approx 3.9e9)
    # 2024 in NTP ~ 3913056000
    if val < 3000000000:
        print("NTP Error: Value too low/invalid")
        return 0
        
    return val - NTP_DELTA

def set_rtc_time():
    t = get_ntp_time()
    # Set the internal RTC
    # machine.RTC().datetime() takes: (year, month, day, weekday, hour, minute, second, subseconds)
    # time.localtime(t) returns: (year, month, day, hour, minute, second, weekday, yearday)
    
    # We must be careful with the conversion
    tm = time.localtime(t)
    
    # MicroPython RTC.datetime format: (year, month, day, weekday, hour, minute, second, subseconds)
    # weekday is 0-6 for Mon-Sun? 
    # tm[6] is weekday.
    
    # machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
    # USER REQUEST: Do not use internal RTC. Update External DS3231 ONLY.
    
    try:
        rtc = rtc_module.get_rtc()
        if rtc and rtc.is_working():
            # tm is (year, month, day, hour, minute, second, weekday, yearday)
            rtc.set_time(tm)
            print("ntptime: Updated External RTC with: ", tm)
            persistent_logger.log(f"NTP Sync Success: {tm[0]}-{tm[1]:02d}-{tm[2]:02d}")
    except Exception as e:
        print("ntptime: Failed to update External RTC:", e)
        persistent_logger.log(f"NTP Sync Error: {e}")
    
    # We do NOT return anything or set system time. 
    # System time might drift or be wrong, but we rely on rtc_module.get_time() for truth.
