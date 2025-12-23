import time

def get_day_of_week(year, month, day):
    """
    Calculate day of week (0=Monday, 6=Sunday).
    Custom implementation to replace timehelp dependency.
    Zeller's congruence adaptation.
    """
    if month < 3:
        month += 12
        year -= 1
    return (day + 13 * (month + 1) // 5 + year + year // 4 - year // 100 + year // 400 + 5) % 7 

def test_dates():
    # Known dates
    # 2025-01-01 is Wednesday (2)
    # 2024-02-29 is Thursday (3)
    
    tests = [
        (2025, 1, 1),
        (2025, 12, 25),
        (2024, 2, 29),
        (2023, 12, 31) # Sunday (6)
    ]
    
    for y, m, d in tests:
        calc = get_day_of_week(y, m, d)
        
        # Use python std lib
        # wday is index 6 of struct_time
        # But we need to use datetime for easy checking or mktime
        # micro python might not have datetime, but full python does.
        # local test environment has full python.
        import datetime
        dt = datetime.date(y, m, d)
        std_dow = dt.weekday() # 0=Mon, 6=Sun
        
        print(f"{y}-{m}-{d}: Calc={calc}, Std={std_dow} -> {'PASS' if calc == std_dow else 'FAIL'}")

if __name__ == "__main__":
    test_dates()
