import json
import rtc_module

MAX_LOGS = 10
LOG_FILE = "system_log.json"

class PersistentLogger:
    _instance = None
    
    @classmethod
    def get_logger(cls):
        if cls._instance is None:
            cls._instance = PersistentLogger()
        return cls._instance

    def __init__(self):
        self.logs = []
        self._load()

    def log(self, message):
        timestamp = "INVALID TIME"
        try:
            # Safe access to RTC to prevent recursion/init errors
            import rtc_module 
            # We don't use get_rtc() here to avoid triggering creation if not ready?
            # Actually get_rtc() is safe if instance exists.
            rtc = rtc_module.RealTimeClock.inst() 
            
            # Check if RTC object exists AND is fully initialized (has rtc_present attr)
            if rtc and getattr(rtc, 'rtc_present', False):
                 t = rtc.get_time()
                 if t[0] >= 2020:
                     timestamp = "{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[1], t[2], t[3], t[4], t[5])
        except Exception:
            pass
            
        entry = f"[{timestamp}] {message}"
        
        self.logs.append(entry)
        while len(self.logs) > MAX_LOGS:
            self.logs.pop(0)
            
        print(f"Log: {entry}") 
        self._save()

    def get_logs(self):
        return self.logs

    def _save(self):
        try:
            # Flush to disk immediately
            with open(LOG_FILE, "w") as f:
                json.dump(self.logs, f)
                f.flush()
        except Exception as e:
            print("Logger Error (Save):", e)
            print("Ensure filesystem is writable.")

    def _load(self):
        try:
            with open(LOG_FILE, "r") as f:
                self.logs = json.load(f)
            print(f"PersistentLogger: Loaded {len(self.logs)} logs.")
        except Exception as e:
            print(f"PersistentLogger: Load failed (starting empty): {e}")
            self.logs = []

def log(message):
    PersistentLogger.get_logger().log(message)

def get_logger():
    return PersistentLogger.get_logger()
