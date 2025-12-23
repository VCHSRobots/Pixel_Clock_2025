# web_server.py - Async Web Server for NeoDisplay Clock
# Dec 2025

import uasyncio as asyncio
import gc

MAX_BODY_SIZE = 4096

import json
import neodisplay
import animations
import time_display
import settings_manager
import persistent_logger
import dispman
import alarm_manager

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

class WebServer:
    def __init__(self, device_name="NeoDisplay Clock"):
        self.device_name = device_name
        self.dm = dispman.get_display_manager()
        self.td = time_display.get_time_display()
        self.sm = settings_manager.get_settings_manager()
        self.am = alarm_manager.get_alarm_manager()
        
    def _get_logs(self):
        try:
            return persistent_logger.get_logger().get_logs()
        except Exception as e:
            print(f"WebServer: Logic Error getting logs: {e}")
            return []

    async def start(self):
        # Start Server
        print("Web Server: Starting on port 80...")
        # backlog=5 ensures we can handle simultaneous connections in queue
        self.server = await asyncio.start_server(self.handle_client, "0.0.0.0", 80, backlog=5)
        
    async def handle_client(self, reader, writer):
        try:
            gc.collect()
            # Simple HTTP Request Parsing
            request_line = await reader.readline()
            if not request_line:
                #print("Web Server: Client disconnected.")
                writer.close()
                return

            #print("Web Server: Request: ", request_line.decode().strip())

            try:
                method, path, proto = request_line.decode().strip().split()
                
                # Log everything except high-frequency status polling
                if path != "/api/status":
                     addr = writer.get_extra_info('peername')
                     ip = addr[0] if addr else "Unknown"
                     print(f"WebServer: Request from {ip} : {method} {path}")
                    
            except ValueError:
                writer.close()
                return

            # Read Headers
            content_length = 0
            while True:
                line = await reader.readline()
                if not line or line == b'\r\n':
                    break
                line_str = line.decode().lower()
                if line_str.startswith('content-length:'):
                    try:
                        content_length = int(line_str.split(':')[1].strip())
                        if content_length > MAX_BODY_SIZE:
                            raise ValueError("Payload Too Large")
                    except:
                        pass
            
            # Read Body
            body = b""
            if content_length > 0:
                # Manual readexact implementation
                left = content_length
                while left > 0:
                    chunk = await reader.read(min(left, 1024))
                    if not chunk:
                        break
                    body += chunk
                    left -= len(chunk)
                
            # Routing
            if path == "/" or path == "/index.html":
                await self.serve_file(writer, "index.html", "text/html")
            elif path == "/script.js":
                await self.serve_file(writer, "script.js", "application/javascript")
            elif path == "/api/status":
                await self.serve_status(writer)
            elif path == "/api/settings" and method == "POST":
                await self.serve_settings(writer, body)
            elif path == "/api/animation" and method == "POST":
                await self.serve_animation(writer, body)
            elif path == "/api/alarms":
                await self.serve_alarms(writer, method, body)
            else:
                await self.serve_404(writer)
                
        except Exception as e:
            print("Request Error:", e)
        finally:
            gc.collect()
            try:
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def serve_file(self, writer, filename, content_type):
        try:
            writer.write("HTTP/1.0 200 OK\r\n")
            writer.write(f"Content-Type: {content_type}\r\n")
            writer.write("Connection: close\r\n")
            writer.write("\r\n")
            
            # Streaming implementation to avoid OOM on large files
            if filename == "index.html":
                # Text mode, line-by-line for replacement
                with open(filename, 'r') as f:
                    for line in f:
                        if "<title>" in line:
                             line = line.replace("<title>NeoDisplay Clock Control</title>", f"<title>{self.device_name}</title>")
                        if "<h1>" in line:
                             line = line.replace("<h1>NeoDisplay Clock</h1>", f"<h1>{self.device_name}</h1>")
                        writer.write(line)
                        await writer.drain()
            else:
                # Binary mode, chunked
                with open(filename, 'rb') as f:
                    while True:
                        chunk = f.read(1024)
                        if not chunk:
                            break
                        writer.write(chunk)
                        await writer.drain()
                        
        except OSError:
            await self.serve_404(writer)

    async def serve_status(self, writer):
        import time_keeper
        tk = time_keeper.get_time_keeper()
        full_dt = tk.get_full_dict()
        
        if "error" in full_dt:
            time_val = [0, 0, 0]
            err_msg = full_dt["error"]
            date_val = None
        else:
            time_val = [full_dt["hour"], full_dt["minute"], full_dt["second"]]
            err_msg = ""
            date_val = {
                "year": full_dt["year"],
                "month": full_dt["month"],
                "day": full_dt["day"],
                "wday": full_dt["wday"]
            }
        
        status = {
            "time": time_val,
            "date": date_val,
            "error": err_msg,
            "brightness": neodisplay.get_display().brightness(),
            "color": rgb_to_hex(self.td.color),
            "colon_color": rgb_to_hex(self.td.colon_color),
            "seconds_color": rgb_to_hex(self.td.seconds_color),
            "mode": self.td.mode,
            "twelve_hour": self.td.twelve_hour,
            "blink_mode": self.td.blink_mode,
            "rotation": getattr(neodisplay.get_display(), "_rotated", False),
            "timezone_offset": self.sm.get("timezone_offset", -8),
            "logs": self._get_logs()
        }
        
        payload = json.dumps(status)
        writer.write("HTTP/1.0 200 OK\r\n")
        writer.write("Content-Type: application/json\r\n")
        writer.write("Cache-Control: no-cache\r\n")
        writer.write("\r\n")
        writer.write(payload)

    async def serve_settings(self, writer, body):
        try:
            self.am.notify_web_activity()
            data = json.loads(body)
            updates = {}
            
            # Brightness
            if "brightness" in data:
                # brightness is global on display
                brightness = float(data["brightness"])
                neodisplay.get_display().brightness(brightness)
                updates["brightness"] = brightness
            
            # Colors
            if "color" in data:
                c = hex_to_rgb(data["color"])
                self.td.set_color(c)
                updates["digit_color"] = c
                
            if "colon_color" in data:
                c = hex_to_rgb(data["colon_color"])
                self.td.set_colon_color(c)
                updates["colon_color"] = c

            if "seconds_color" in data:
                c = hex_to_rgb(data["seconds_color"])
                self.td.set_seconds_color(c)
                updates["seconds_color"] = c
                
            # Mode
            if "mode" in data:
                m = int(data["mode"])
                self.td.set_mode(m)
                updates["mode"] = m
                
            if "twelve_hour" in data:
                th = bool(data["twelve_hour"])
                self.td.set_12hr(th)
                updates["12_hour_mode"] = th

            if "colon_blink_mode" in data:
                bm = int(data["colon_blink_mode"])
                self.td.set_blink_mode(bm)
                updates["colon_blink_mode"] = bm

            if "rotation" in data:
                rot = bool(data["rotation"])
                neodisplay.get_display().set_rotation(rot)
                updates["rotation"] = rot
                
            if "timezone_offset" in data:
                try:
                    updates["timezone_offset"] = int(data["timezone_offset"])
                except:
                    pass
            
            # Save all at once
            if updates:
                self.sm.update(updates)
                
            writer.write("HTTP/1.0 200 OK\r\n\r\n")
            writer.write('{"status":"ok"}')
        except Exception as e:
            print("Settings Error:", e)
            writer.write("HTTP/1.0 500 Internal Server Error\r\n\r\n")

    async def serve_animation(self, writer, body):
        try:
            self.am.notify_web_activity()
            data = json.loads(body)
            name = data.get("name", "")
            
            if name == "stop":
                self.dm.stop_foreground()
            elif name == "rainbow":
                anim = animations.Rainbow()
                self.dm.play_immediate(anim)
            elif name == "scroll":
                anim = animations.ScrollingText("Hello World", color=neodisplay.CYAN, loops=1)
                self.dm.play_immediate(anim)
            elif name == "scroll_custom":
                text = data.get("text", "Hello")
                anim = animations.ScrollingText(text, color=neodisplay.GREEN, loops=1)
                self.dm.play_immediate(anim)
            elif name == "bounce_red":
                anim = animations.BouncingBox(color=neodisplay.RED, change_color_on_bounce=False)
                self.dm.play_immediate(anim) # Is infinite by default? Yes. So it replaces TimeDisplay until stopped. 
                # If we want it to run for a bit, we'd need a wrapper or manual stop call. 
                # User asked to "issue requests for animations". Usually one expects it to play.
                # Since BouncingBox has no loop limit in its code, it will run forever until "Stop Animation" is clicked.
            elif name == "bounce_blue":
                anim = animations.BouncingBox(color=neodisplay.BLUE)
                self.dm.play_immediate(anim)
            
            writer.write("HTTP/1.0 200 OK\r\n\r\n")
            writer.write('{"status":"started"}')
        except Exception as e:
            print("Anim Error:", e)
            writer.write("HTTP/1.0 500 Internal Server Error\r\n\r\n")

    async def serve_alarms(self, writer, method, body):
        try:
            if method == "GET":
                alarms = self.am.get_alarms()
                payload = json.dumps(alarms)
                writer.write("HTTP/1.0 200 OK\r\n")
                writer.write("Content-Type: application/json\r\n")
                writer.write("Cache-Control: no-cache\r\n\r\n")
                writer.write(payload)
                
            elif method == "POST":
                data = json.loads(body)
                cmd = data.get("cmd", "") # add, update, delete
                
                success = False
                if cmd == "add":
                    self.am.add_alarm(data.get("alarm", {}))
                    success = True
                elif cmd == "update":
                    alarm = data.get("alarm", {})
                    # Ensure ID is preserved or passed from top level
                    aid = data.get("id") or alarm.get("id")
                    if aid:
                        self.am.update_alarm(aid, alarm)
                        success = True
                elif cmd == "delete":
                    self.am.delete_alarm(data.get("id"))
                    success = True
                    
                writer.write("HTTP/1.0 200 OK\r\n\r\n")
                writer.write(json.dumps({"status": "ok" if success else "error"}))
                
            else:
                writer.write("HTTP/1.0 405 Method Not Allowed\r\n\r\n")
        except ValueError as ve:
            print("Alarm Validation Error:", ve)
            writer.write("HTTP/1.0 400 Bad Request\r\n\r\n")
            writer.write(json.dumps({"status": "error", "message": str(ve)}))
        except Exception as e:
            print("Alarm API Error:", e)
            writer.write("HTTP/1.0 500 Internal Server Error\r\n\r\n")

    async def serve_404(self, writer):
        writer.write("HTTP/1.0 404 Not Found\r\n\r\n")
        writer.write("Not Found")
