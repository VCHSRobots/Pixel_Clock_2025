# alarm_manager.py - Manages Alarms and Critical Times
# Dec 2025

import json
import time
import os

class AlarmManager:
    _instance = None
    
    @classmethod
    def get_alarm_manager(cls):
        if cls._instance is None:
            cls._instance = AlarmManager()
        return cls._instance

    MAX_ALARMS = 20
    MAX_TEXT_LEN = 250

    def __init__(self):
        if AlarmManager._instance is not None:
            raise RuntimeError("AlarmManager Singleton")
        AlarmManager._instance = self
        
        self.alarms = []
        self.filename = "alarms.json"
        self._load_alarms()
        
        # Critical Time State
        self.critical_active = False
        self.critical_alarm_id = None
        self.critical_end_time = 0 # Epoch seconds
        self.original_state = {} 
        
    def _load_alarms(self):
        try:
            with open(self.filename, 'r') as f:
                self.alarms = json.load(f)
        except:
            self.alarms = []
            
    def save_alarms(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.alarms, f)
        except Exception as e:
            print(f"AlarmManager: Error saving alarms: {e}")

    def get_alarms(self):
        return self.alarms 
        
    def _validate_alarm(self, alarm):
        # Validate Text Length
        action = alarm.get("action", {})
        payload = action.get("payload", {})
        text = payload.get("text", "")
        if len(text) > self.MAX_TEXT_LEN:
            raise ValueError(f"Text too long (Max {self.MAX_TEXT_LEN})")
        return True

    def add_alarm(self, alarm):
        if len(self.alarms) >= self.MAX_ALARMS:
            raise ValueError(f"Max alarms reached ({self.MAX_ALARMS})")
            
        self._validate_alarm(alarm)
        
        if "id" not in alarm:
            alarm["id"] = str(int(time.time() * 1000))
        if "enabled" not in alarm:
            alarm["enabled"] = True
        self.alarms.append(alarm)
        self.save_alarms()
        return alarm["id"]

    def update_alarm(self, alarm_id, alarm_data):
        self._validate_alarm(alarm_data)
        
        for i, a in enumerate(self.alarms):
            if a.get("id") == alarm_id:
                self.alarms[i] = alarm_data
                self.save_alarms()
                return True
        return False
        
    def delete_alarm(self, alarm_id):
        initial_len = len(self.alarms)
        self.alarms = [a for a in self.alarms if a.get("id") != alarm_id]
        if len(self.alarms) < initial_len:
            self.save_alarms()
            return True
        return False

    def notify_web_activity(self):
        """
        Called when Web UI interferes (settings change, manual anim).
        Terminates active critical time immediately.
        """
        if self.critical_active:
            print("AlarmManager: Web Activity detected -> Terminating Critical Time")
            self.stop_critical_time()

    def stop_critical_time(self):
        if not self.critical_active:
            return
            
        print("AlarmManager: Stopping Critical Time")
        self.critical_active = False
        self.critical_alarm_id = None
        self._restore_state()
        
    def _restore_state(self):
        """
        Restores display settings if they were hijacked.
        """
        if not self.original_state:
            return
            
        import time_display
        td = time_display.get_time_display()
        
        # Restore Logic
        if "blink_mode" in self.original_state:
            td.set_blink_mode(self.original_state["blink_mode"])
            
        if "color" in self.original_state:
            td.set_color(self.original_state["color"])
            
        if "colon_color" in self.original_state:
            td.set_colon_color(self.original_state["colon_color"])
            
        if "seconds_color" in self.original_state:
            td.set_seconds_color(self.original_state["seconds_color"])
            
        if "mode" in self.original_state:
            td.set_mode(self.original_state["mode"])
            
        if "global_blink_rate" in self.original_state:
            td.set_global_blink(self.original_state["global_blink_rate"])
            
        if "brightness" in self.original_state and self.original_state["brightness"] >= 0:
            import neodisplay
            neodisplay.get_display().brightness(self.original_state["brightness"])
        
        # Stop any foreground animation if we started one
        import dispman
        dm = dispman.get_display_manager()
        dm.stop_foreground()
        
        print("AlarmManager: State Restored")
        self.original_state = {}
        
    def update(self):
        if self.critical_active:
            import time
            if time.time() > self.critical_end_time:
                print("AlarmManager: Alarm Duration Expired")
                self.stop_critical_time()

    def _parse_color(self, hex_str):
        if not hex_str or not hex_str.startswith("#"):
            return (255, 255, 255)
        hex_str = hex_str.lstrip('#')
        try:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        except:
            return (255, 255, 255)

    def start_critical_time(self, alarm):
        import time
        import neodisplay
        import dispman
        import animations
        import time_display
        
        # 1. Capture State
        if not self.critical_active:
            td = time_display.get_time_display()
            disp = neodisplay.get_display()
            val_gbr = getattr(td, "global_blink_rate", 0)
            self.original_state = {
                "blink_mode": td.blink_mode,
                "color": td.color,
                "colon_color": td.colon_color,
                "seconds_color": td.seconds_color,
                "mode": td.mode,
                "global_blink_rate": val_gbr,
                "brightness": disp.brightness()
            }
            
        self.critical_active = True
        self.critical_alarm_id = alarm.get("id")
        
        action = alarm.get("action", {})
        payload = action.get("payload", {})
        atype = action.get("type", "scroll")
        
        # Duration Logic
        duration_type = action.get("duration_type", "seconds")
        # Reuse 'duration_sec' field for loop count to simplify schema, 
        # or use specific field. Let's use 'duration_sec' as 'duration_value'.
        duration_val = int(action.get("duration_sec", 60))
        
        if duration_type == "loops" and atype == "scroll":
             self.critical_end_time = time.time() + 3600 # Safety timeout
        else:
             self.critical_end_time = time.time() + duration_val
        
        # Apply Overrides
        td = time_display.get_time_display()
        
        # Color Override
        p_color = payload.get("color")
        if p_color:
            c = self._parse_color(p_color)
            td.set_color(c)
            td.set_colon_color(c)
            td.set_seconds_color(c)
            
        # Brightness Override
        brite = float(payload.get("brightness", 1.0))
        neodisplay.get_display().brightness(brite)
        
        # Animations
        dm = dispman.get_display_manager()
        
        if atype == "scroll":
            text = payload.get("text", "ALARM")
            color = self._parse_color(payload.get("color", "#ff0000"))
            anim = animations.ScrollingText(text, color=color, speed=0.1) 
            
            if duration_type == "loops":
                anim.loops = duration_val
                
                def on_done():
                    print("AlarmManager: Loop Done -> Stopping")
                    self.stop_critical_time()
                    
                dm.play_immediate(anim, on_complete=on_done)
            else:
                anim.loops = 9999
                dm.play_immediate(anim)
            
        elif atype == "blink_display":
            td.set_global_blink(2)
            dm.stop_foreground()

    def check_alarms(self, full_dt):
        """
        Checks if any alarm triggers at full_dt (dict result from time_keeper).
        Returns True if a NEW critical time was started, False otherwise.
        """
        if "error" in full_dt:
            return False
            
        current_time_str = "{:02d}:{:02d}".format(full_dt["hour"], full_dt["minute"])
        current_wday = full_dt["wday"]
        current_date_str = "{:04d}-{:02d}-{:02d}".format(full_dt["year"], full_dt["month"], full_dt["day"])
        
        matched_alarm = None
        
        for alarm in self.alarms:
            if not alarm.get("enabled", True):
                continue
                
            if self._is_alarm_match(alarm, full_dt, current_wday, current_date_str):
                matched_alarm = alarm
                break 
        
        if matched_alarm:
            # Simple debounce: unique key per minute per alarm
            trigger_key = f"{matched_alarm.get('id')}:{current_date_str}:{current_time_str}"
            if hasattr(self, "last_trigger_key") and self.last_trigger_key == trigger_key:
                return False
                
            print(f"AlarmManager: Triggering Alarm '{matched_alarm.get('name')}'")
            self.last_trigger_key = trigger_key
            self.start_critical_time(matched_alarm)
            return True
            
        return False

    def _is_alarm_match(self, alarm, full_dt, wday, date_str):
        sched = alarm.get("schedule", {})
        atype = alarm.get("type", "repetitive")
        freq = sched.get("frequency", "daily")
        
        hh = full_dt["hour"]
        mm = full_dt["minute"]
        
        target_time = sched.get("time", "00:00")
        try:
            th, tm = map(int, target_time.split(":"))
        except:
            return False
            
        # Span Check
        disabled_spans = sched.get("disabled_spans", [])
        for span in disabled_spans:
            s = span.get("start")
            e = span.get("end")
            if s and e and (s <= date_str <= e):
                return False

        # ONE SHOT
        if atype == "oneshot":
            if sched.get("date") == date_str and th == hh and tm == mm:
                return True
            return False
            
        # REPETITIVE
        if freq == "hourly":
            if tm != mm:
                return False
            if hh in sched.get("skip_hours", []):
                return False
            days = sched.get("days", [])
            if days and wday not in days:
                return False
            return True
            
        # Daily/Weekly
        if th != hh or tm != mm:
            return False
            
        days = sched.get("days", [])
        if days and wday not in days:
            return False
            
        return True

def get_alarm_manager():
    return AlarmManager.get_alarm_manager()
