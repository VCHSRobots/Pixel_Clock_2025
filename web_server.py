# web_server.py - Async Web Server for NeoDisplay Clock
# Dec 2025

import uasyncio as asyncio
import network
import json
import socket
import neodisplay
import config
import animations
from time_display import TimeDisplay, HH_MM, HH_MM_SS

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

class WebServer:
    def __init__(self, display_manager, time_display, settings_manager):
        self.dm = display_manager
        self.td = time_display
        self.sm = settings_manager
        
    async def start(self):
        # Connect to WiFi
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        # Power management for responsiveness
        try:
            wlan.config(pm = 0xa11140) 
        except:
            pass # Not all firmwares support this

        print(f"Web Server: Connecting to {config.SSID}...")
        wlan.connect(config.SSID, config.PASSWORD)
        
        max_wait = 20
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('Waiting for connection...')
            await asyncio.sleep(1)
            
        if wlan.status() != 3:
             print("Web Server: Network connection failed.")
        else:
             print("Web Server: Connected. IP =", wlan.ifconfig()[0])
             
        # Start Server
        print("Web Server: Starting on port 80...")
        # backlog=5 ensures we can handle simultaneous connections in queue
        self.server = await asyncio.start_server(self.handle_client, "0.0.0.0", 80, backlog=5)
        
    async def handle_client(self, reader, writer):
        try:
            # Simple HTTP Request Parsing
            request_line = await reader.readline()
            if not request_line:
                #print("Web Server: Client disconnected.")
                writer.close()
                return

            #print("Web Server: Request: ", request_line.decode().strip())

            try:
                method, path, proto = request_line.decode().strip().split()
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
            else:
                await self.serve_404(writer)
                
        except Exception as e:
            print("Request Error:", e)
        finally:
            try:
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def serve_file(self, writer, filename, content_type):
        try:
            with open(filename, 'r') as f:
                content = f.read()
            writer.write("HTTP/1.0 200 OK\r\n")
            writer.write(f"Content-Type: {content_type}\r\n")
            writer.write("Connection: close\r\n")
            writer.write("\r\n")
            writer.write(content)
        except OSError:
            await self.serve_404(writer)

    async def serve_status(self, writer):
        import time_keeper
        h, m, s = time_keeper.get_time()
        
        status = {
            "time": [h, m, s],
            "brightness": neodisplay.get_display().brightness(),
            "color": rgb_to_hex(self.td.color),
            "colon_color": rgb_to_hex(self.td.colon_color),
            "seconds_color": rgb_to_hex(self.td.seconds_color),
            "mode": self.td.mode,
            "twelve_hour": self.td.twelve_hour
        }
        
        payload = json.dumps(status)
        writer.write("HTTP/1.0 200 OK\r\n")
        writer.write("Content-Type: application/json\r\n")
        writer.write("Cache-Control: no-cache\r\n")
        writer.write("\r\n")
        writer.write(payload)

    async def serve_settings(self, writer, body):
        try:
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

    async def serve_404(self, writer):
        writer.write("HTTP/1.0 404 Not Found\r\n\r\n")
        writer.write("Not Found")
