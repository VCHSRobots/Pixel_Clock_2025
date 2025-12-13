# time_keeper.py - Time keeping module
# Dec 2025

import time

def get_time():
    """
    Returns the current time as (hour, minute, second).
    Uses the system's local time.
    """
    t = time.localtime()
    # time.localtime() returns (no, year, month, day, hour, minute, second, ...)
    # Indices: 0:year, 1:month, 2:day, 3:hour, 4:minute, 5:second
    return t[3], t[4], t[5]
