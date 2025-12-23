import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import MagicMock

# Mock Modules
sys.modules['neodisplay'] = MagicMock()
sys.modules['dispman'] = MagicMock()
sys.modules['time_display'] = MagicMock()
sys.modules['animations'] = MagicMock()
sys.modules['time'] = MagicMock()

import alarm_manager

class TestAlarmManager(unittest.TestCase):
    def setUp(self):
        # Reset Singleton
        alarm_manager.AlarmManager._instance = None
        self.am = alarm_manager.get_alarm_manager()
        # Mock dependencies in AM
        self.am.save_alarms = MagicMock() # Don't write file
        
        # Setup TimeDisplay mock
        self.td_mock = MagicMock()
        self.td_mock.color = (255, 255, 255)
        self.td_mock.colon_color = (255, 0, 0)
        self.td_mock.seconds_color = (0, 0, 255)
        self.td_mock.mode = 0
        self.td_mock.blink_mode = 0
        self.td_mock.global_blink_rate = 0
        
        # Setup Neodisplay
        self.nd_mock = MagicMock()
        self.nd_mock.brightness.return_value = 0.5
        
        import time_display
        time_display.get_time_display = MagicMock(return_value=self.td_mock)
        
        import neodisplay
        neodisplay.get_display = MagicMock(return_value=self.nd_mock)
        
    def test_add_alarm(self):
        alarm = {
            "name": "Test",
            "type": "repetitive",
            "schedule": {"time": "08:00", "frequency": "daily", "days": [0,1,2]},
            "action": {"type": "scroll", "duration_sec": 60, "payload": {"text": "HELLO"}}
        }
        self.am.add_alarm(alarm)
        alarms = self.am.get_alarms()
        self.assertEqual(len(alarms), 1)
        self.assertEqual(alarms[0]["name"], "Test")
        self.assertTrue(alarms[0]["enabled"])
        
    def test_check_alarm_trigger(self):
        # Add Alarm
        alarm = {
            "enabled": True,
            "name": "Test Trigger",
            "type": "repetitive",
            "schedule": {"time": "12:00", "frequency": "daily", "days": [0]}, # Monday
            "action": {"type": "blink_display", "duration_sec": 10}
        }
        self.am.add_alarm(alarm)
        
        # Test Match
        # Monday (0), 12:00:00, 2025-01-06
        dt = {"wday": 0, "hour": 12, "minute": 0, "second": 0, "year": 2025, "month": 1, "day": 6}
        
        # Should Trigger
        self.am.check_alarms(dt)
        if not self.am.critical_active:
             print("Test Trigger: Critical Active is False. Alarms:", self.am.alarms)
        self.assertTrue(self.am.critical_active)
        
    def test_check_alarm_no_trigger_wrong_day(self):
        alarm = {
            "enabled": True,
            "type": "repetitive",
            "schedule": {"time": "12:00", "frequency": "daily", "days": [0]}, # Monday
            "action": {}
        }
        self.am.add_alarm(alarm)
        
        # Tuesday (1), 12:00:00, 2025-01-07
        dt = {"wday": 1, "hour": 12, "minute": 0, "second": 0, "year": 2025, "month": 1, "day": 7}
        
        self.am.check_alarms(dt)
        self.assertFalse(self.am.critical_active)
        
    def test_web_priority(self):
        # Trigger critical time
        self.am.start_critical_time = MagicMock() # Mock the start method itself to just set flag? 
        # Actually better to let it run but we mocked dependencies so it's safe.
        # But allow us to set the flag manually if needed or call real method.
        # Let's call real method logic by not mocking it on instance, but ensure we have an alarm to pass.
        # Or just manually set state for this test.
        self.am.critical_active = True
        
        # Notify Web Activity
        self.am.notify_web_activity()
        
        # Should stop critical time
        self.assertFalse(self.am.critical_active)

if __name__ == '__main__':
    unittest.main()
