
import network
import socket
import time
import json
import machine
import gc
import neodisplay
import dispman
import animations
import uasyncio as asyncio
import select
import struct

def dns_response(data, ip_addr):
    """
    Minimal DNS Responder.
    Constructs a DNS response packet pointing any query to 'ip_addr'.
    """
    try:
        # Extract Transaction ID (first 2 bytes)
        tid = data[:2]
        # Flags: QR=1, Opcode=0, AA=1, TC=0, RD=1, RA=0, Z=0, RCODE=0
        flags = b'\x81\x80'
        qdcount = b'\x00\x01'
        ancount = b'\x00\x01'
        nscount = b'\x00\x00'
        arcount = b'\x00\x00'
        
        i = 12
        while data[i] != 0:
            i += data[i] + 1
        question_end = i + 5
        question = data[12:question_end] # Copy question section
        
        name_pointer = b'\xc0\x0c' # Pointer to offset 12
        type_a = b'\x00\x01'
        class_in = b'\x00\x01'
        ttl = b'\x00\x00\x00\x3c'
        data_len = b'\x00\x04'
        parts = [int(p) for p in ip_addr.split('.')]
        ip_bytes = struct.pack('BBBB', *parts)

        return tid + flags + qdcount + ancount + nscount + arcount + question + name_pointer + type_a + class_in + ttl + data_len + ip_bytes
    except:
        return None

def perform_scan():
    """Scan for networks using STA interface."""
    print("SetupMode: Scanning for networks...")
    networks = []
    try:
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        time.sleep(1) # Give it a moment
        scanned = sta.scan() # list of (ssid, bssid, channel, rssi, authmode, hidden)
        sta.active(False)
        
        # Sort by RSSI (signal strength)
        scanned.sort(key=lambda x: x[3], reverse=True)
        
        seen = set()
        for s in scanned:
            ssid = s[0].decode('utf-8')
            if ssid and ssid not in seen:
                networks.append(ssid)
                seen.add(ssid)
        print(f"SetupMode: Found {len(networks)} networks")
    except Exception as e:
        print(f"SetupMode: Scan failed: {e}")
        try:
             # Ensure STA is off if it failed
             network.WLAN(network.STA_IF).active(False)
        except: pass
    return networks

async def run_setup():
    """
    Async Setup Mode with:
    - Captive Portal (DNS+HTTP)
    - Wi-Fi Scanning
    - Smooth Animations (via yield)
    """
    print("SetupMode: Entering Async Setup Mode...")
    
    # 1. Scanning (Blocking is fine here, it's startup)
    scan_options = perform_scan()
    options_html = ""
    for ssid in scan_options:
        options_html += f'<option value="{ssid}">{ssid}</option>'
    
    # 2. Init Hardware / Animation
    mgr = dispman.get_display_manager()
    
    # 3. Start Access Point
    AP_SSID = 'Clock Setup'
    AP_PASS = ''
    
    # Try setting country to avoid regulatory blocks on some FW
    try:
        import rp2
        rp2.country('US')
    except:
        pass

    # Ensure STA is off so it doesn't interfere
    try:
        network.WLAN(network.STA_IF).active(False)
    except:
        pass

    ap = network.WLAN(network.AP_IF)
    
    # Robust Initialization Sequence (Legacy Compatible)
    try:
        # Try "Active First" - standard for older MicroPython
        ap.active(True)
        
        # Wait for hardware to report active
        for _ in range(10):
            if ap.active(): break
            await asyncio.sleep(0.2)
            
        # Now apply config
        # Some older FWs throw error if channel is passed?
        # We try full config first
        ap.config(essid=AP_SSID, password=AP_PASS, channel=6, security=0)
    except Exception as e:
        print(f"SetupMode: Init Error {e}, retrying simplified...")
        try:
             # Fallback: maybe channel failed or active() failed
             ap.active(True)
             await asyncio.sleep(1)
             ap.config(essid=AP_SSID, password=AP_PASS, security=0) # No channel
        except Exception as e2:
             print(f"SetupMode: Retry failed {e2}")

    # Wait for AP
    print("SetupMode: Waiting for AP...")
    while not ap.active():
        await asyncio.sleep(0.5)
        
    ip = ap.ifconfig()[0]
    print(f"SetupMode: AP Active! IP: {ip}")
    
    # 4. Start Animation (Smooth!)
    # Scrolling message instructions
    msg = f"SETUP SSID:[{AP_SSID}] IP:{ip}"
    setup_anim = animations.ScrollingText(msg, color=neodisplay.MAGENTA, speed=0.05)
    mgr.play_immediate(setup_anim)

    # 5. Start Servers (Manual Sockets)
    # HTTP
    web_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    web_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    web_s.bind(('0.0.0.0', 80))
    web_s.listen(5)
    web_s.setblocking(False)
    
    # DNS
    dns_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dns_s.bind(('0.0.0.0', 53))
    dns_s.setblocking(False)
    
    print('SetupMode: HTTP (80) and DNS (53) listening.')
    
    old_stations = []
    
    # 6. Main Async Loop
    while True:
        # Crucial: Yield to allow animations and system tasks to run!
        await asyncio.sleep(0.02)
        
        # --- Connections ---
        # Polling sockets with 0 timeout (non-blocking)
        try:
            r, _, _ = select.select([web_s, dns_s], [], [], 0)
            
            # DNS
            if dns_s in r:
                try:
                    data, addr = dns_s.recvfrom(1024)
                    resp = dns_response(data, ip)
                    if resp:
                        dns_s.sendto(resp, addr)
                except:
                    pass

            # HTTP
            if web_s in r:
                conn, addr = web_s.accept()
                print('SetupMode: Conn', addr)
                conn.settimeout(2.0) # Short timeout for handling request
                
                try:
                    buffer = b""
                    while b"\r\n\r\n" not in buffer:
                        chunk = conn.recv(256)
                        if not chunk: break
                        buffer += chunk
                        if len(buffer) > 4096: break # Safety limit

                    req_str = buffer.decode()
                    
                    if "POST" in req_str and "Content-Length:" in req_str:
                        # Extract Content-Length
                        try:
                            cl_header = "Content-Length:"
                            idx = req_str.find(cl_header)
                            if idx != -1:
                                end_idx = req_str.find("\r\n", idx)
                                if end_idx == -1: end_idx = len(req_str)
                                cl_val = int(req_str[idx+len(cl_header):end_idx].strip())
                                
                                # Split what we have
                                header_part, body_part = req_str.split("\r\n\r\n", 1)
                                body_bytes = body_part.encode()
                                
                                # Read rest of body
                                while len(body_bytes) < cl_val:
                                    chunk = conn.recv(256)
                                    if not chunk: break
                                    body_bytes += chunk
                                
                                req_str = header_part + "\r\n\r\n" + body_bytes.decode()
                        except Exception as e:
                            print("Body Read Err:", e)
                            pass
                    
                    if "POST /configure" in req_str:
                        parts = req_str.split('\r\n\r\n')
                        if len(parts) > 1:
                             body = parts[1].strip()
                             ssid = ""
                             password = ""
                             name = "NeoDisplay Clock"
                             
                             for pair in body.split('&'):
                                 if '=' in pair:
                                     k, v = pair.split('=', 1)
                                     v = v.replace('+',' ').replace('%20',' ').replace('%21','!').replace('%23','#')
                                     if k == 'ssid': ssid = v
                                     if k == 'password': password = v
                                     if k == 'device_name': name = v
                            
                             if ssid:
                                 print(f"Saving {ssid}")
                                 save_credentials(ssid, password, name)
                                 conn.send(b"HTTP/1.0 200 OK\r\n\r\nSaved. Rebooting...")
                                 conn.close()
                                 
                                 # Feedback via Animation Manager
                                 # We can play 'SAVED' then reset
                                 saved_anim = animations.MessageDisplay("SAVED", color=neodisplay.GREEN)
                                 mgr.play_immediate(saved_anim)
                                 
                                 # Give time for animation/response
                                 await asyncio.sleep(3)
                                 machine.reset()
                                 continue
                    
                    # Serve Page
                    html = f"""HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body {{ font-family:sans-serif; background:#111; color:#eee; padding:20px; }}
 .c {{ max-width:400px; margin:auto; }}
 input, select {{ width:100%; padding:8px; margin:5px 0; }}
 button {{ width:100%; padding:10px; background:#0af; border:0; font-weight:bold; cursor:pointer; }}
</style>
<title>Setup</title>
</head>
<body>
  <div class="c">
    <h1 style='color:#0af; text-align:center'>Clock Setup</h1>
    <form action="/configure" method="post">
      <label>Name:</label>
      <input type="text" name="device_name" value="NeoDisplay Clock">
      
      <label>SSID:</label>
      <select name="ssid" id="ssid_select" onchange="checkManual()">
        {options_html}
        <option value="manual">Manual Entry...</option>
      </select>
      <input type="text" name="manual_ssid" id="manual_input" placeholder="Enter SSID" style="display:none">
      
      <label>Password:</label>
      <input type="password" name="password">
      
      <button>SAVE</button>
    </form>
    <script>
      function checkManual() {{
        var s = document.getElementById('ssid_select');
        var i = document.getElementById('manual_input');
        if(s.value === 'manual') {{
           i.style.display = 'block';
           i.name = 'ssid'; 
           s.name = 'ssid_select_ignore';
        }} else {{
           i.style.display = 'none';
           i.name = 'manual_ssid';
           s.name = 'ssid';
        }}
      }}
    </script>
  </div>
</body>
</html>
"""
                    conn.send(html[0:512].encode())
                    conn.send(html[512:].encode())
                    conn.close()
                    
                except Exception as e:
                    print("Web Err:", e)
                    conn.close()
                    
        except Exception as e:
            pass
            
        # Monitor Clients Log
        try:
            stations = ap.status('stations')
            if stations != old_stations:
                print(f"SetupMode: Stations: {len(stations)}")
                old_stations = stations
        except: pass

def save_credentials(ssid, password, name):
    data = {"ssid": ssid, "password": password, "name": name}
    try:
        with open("ssid.json", "w") as f:
            json.dump(data, f)
    except: pass
