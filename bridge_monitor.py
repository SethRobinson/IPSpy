#!/usr/bin/env python3
"""
Bridge-based IP Monitor for CM4-DUAL-ETH-MINI (aka: IP Spy)
Monitors DHCP traffic on br0 bridge to detect device IP assignments.
Only prints when a new MAC is seen or a MAC gets a new IP.
Can be imported as a Python module.

Usage:
    python3 bridge_monitor.py          # Monitor bridge only (wired devices)
    python3 bridge_monitor.py --wifi   # Monitor bridge for all DHCP (wired + wireless devices)
"""

import datetime
import signal
import sys
import argparse
import os
import time
# import threading # REMOVE THIS LINE
from scapy.all import AsyncSniffer, DHCP, BOOTP
import netifaces

# Set this to True to enable OLED display, False to disable all OLED code
ENABLE_OLED = True

# Set this to True to always enable WiFi support (same as --wifi)
FORCE_WIFI_SUPPORT = True


try:
    import board
    import adafruit_ssd1306
    from PIL import Image, ImageDraw, ImageFont
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False

# Configuration
BRIDGE_INTERFACE = "br0"
LOG_FILE = "/home/pi/device_ip.txt"
ASSIGNMENTS_LOG_FILE = "/home/pi/ip_assignments.log"

# Track seen MAC/IP pairs in this session
seen_assignments = {}
# Track recent packets to avoid duplicates
recent_packets = {}

# OLED globals
oled = None
oled_image = None
oled_draw = None
oled_font = None
oled_lines = []
OLED_MAX_LINES = 5  # Number of lines to show on OLED
OLED_WIDTH = 128
OLED_HEIGHT = 64
# OLED_LOCK = threading.Lock() # REMOVE THIS LINE
OLED_CHAR_WIDTH = 21  # Approximate characters per line

# Global sniffer instances
sniffer = None
sniffer_wifi = None

def get_bridge_ip():
    """Get the IP address of the bridge interface (br0). Returns None if not assigned."""
    try:
        addrs = netifaces.ifaddresses(BRIDGE_INTERFACE)
        if netifaces.AF_INET in addrs:
            return addrs[netifaces.AF_INET][0]['addr']
    except Exception:
        pass
    return None

def OLEDInit():
    global oled, oled_image, oled_draw, oled_font, oled_lines
    if not ENABLE_OLED:
        return
    if not OLED_AVAILABLE:
        print("[OLED] Libraries not available")
        return
    try:
        print("[OLED] Starting initialization...")
        i2c = board.I2C()
        oled = adafruit_ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
        oled.fill(0)
        oled.show()
        oled_image = Image.new("1", (oled.width, oled.height))
        oled_draw = ImageDraw.Draw(oled_image)
        oled_font = ImageFont.load_default()
        # Directly display the startup lines on the OLED
        startup_lines = []
         # Get bridge IP and add as 4th line
        bridge_ip = get_bridge_ip()
        if bridge_ip:
            ip_line = f"My IP: {bridge_ip}"
        else:
            ip_line = "My IP: DISCONNECTED"
        startup_lines.append(ip_line)
        
        # Split multi-line string into separate lines
        multi_line_msg = "Seth's IP Spy\nReboot a device to\nsee Mac & IP address"
        for line in multi_line_msg.split("\n"):
            startup_lines.append(line)
        
        oled_draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
        for idx, line in enumerate(startup_lines):
            oled_draw.text((0, idx * 12), line, font=oled_font, fill=255)
        oled.image(oled_image)
        oled.show()
        oled_lines = startup_lines.copy()  # Preserve startup lines for scrolling
        print("[OLED] Initialization successful!")
    except Exception as e:
        print(f"[OLED] Initialization failed: {e}")
        oled = None

def OLEDDeInit():
    global oled, oled_image, oled_draw, oled_font, oled_lines
    if not ENABLE_OLED:
        return
    if oled:
        try:
            # Use MultiPrint to show goodbye message in the scrolling display
            MultiPrint("Goodbye!", important=False)
            time.sleep(2)  # Give user time to see it
            oled.fill(0)
            oled.show()
        except Exception:
            pass
        oled = None

def _oled_update():
    global oled, oled_image, oled_draw, oled_font, oled_lines
    if not ENABLE_OLED:
        return
    if not oled:
        return
    try:
        oled_draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
        for idx, line in enumerate(oled_lines[-OLED_MAX_LINES:]):
            oled_draw.text((0, idx * 12), line, font=oled_font, fill=255)
        oled.image(oled_image)
        oled.show()
        # Debug: print what's on screen
        if any("DHCP" in line for line in oled_lines):
            print(f"[OLED DEBUG] Display updated with lines: {oled_lines[-OLED_MAX_LINES:]}")
    except Exception as e:
        print(f"[OLED] Error in _oled_update: {e}")
        import traceback
        traceback.print_exc()

# Remove format_oled_message function entirely

def MultiPrint(msg, important=False):
    global oled_lines, oled
    # Print to console
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    if important:
        print(f"\n{'='*50}")
        print(f"[{timestamp}] {msg}")
        print(f"{'='*50}")
    else:
        print(f"[{timestamp}] {msg}")

    # Print to OLED only for user-facing events
    if ENABLE_OLED and oled:
        try:
            new_lines = []
            # Only format and display DHCP assignment messages
            if "DHCP ASSIGNMENT" in msg:
                import re
                match = re.match(r"DHCP ASSIGNMENT \(([^)]+)\): ([0-9a-f:]+) → ([0-9.]+)", msg)
                if match:
                    interface, mac, ip = match.groups()
                    if interface.startswith("br") or interface.startswith("eth"):
                        label = f"LAN: {ip}"
                    elif interface.startswith("wl"):
                        label = f"WIFI: {ip}"
                    else:
                        label = f"{interface.upper()}: {ip}"
                    new_lines = [label, f"MAC: {mac.strip()}"]
                else:
                    # Split on newlines if present
                    for line in msg.split("\n"):
                        new_lines.append(line[:OLED_CHAR_WIDTH])
            else:
                # For any other user-facing message, split on newlines and add each line
                lines = msg.split("\n")
                new_lines = [line[:OLED_CHAR_WIDTH] for line in lines[:2]]
            # Append new lines to the buffer
            oled_lines.extend(new_lines)
            # Keep only the most recent OLED_MAX_LINES lines
            if len(oled_lines) > OLED_MAX_LINES:
                oled_lines = oled_lines[-OLED_MAX_LINES:]
            _oled_update()
        except Exception as e:
            print(f"[OLED] Error updating display: {e}")
            import traceback
            traceback.print_exc()
    else:
        if "DHCP ASSIGNMENT" in msg:
            print("[OLED DEBUG] OLED not available for DHCP message")

def format_mac(mac_bytes):
    """Format MAC address bytes to readable string"""
    return ":".join(f"{b:02x}" for b in mac_bytes[:6])

def get_packet_signature(packet):
    """Create a unique signature for a packet to detect duplicates"""
    if DHCP in packet and packet[DHCP].options[0][1] == 5:  # DHCP ACK
        client_mac = format_mac(packet[BOOTP].chaddr)
        assigned_ip = packet[BOOTP].yiaddr
        return f"{client_mac}_{assigned_ip}"
    return None

def dhcp_ack_callback(packet, interface):
    """Process DHCP ACK packets to detect IP assignments"""
    if DHCP in packet and packet[DHCP].options[0][1] == 5:  # DHCP ACK
        client_mac = packet[BOOTP].chaddr
        assigned_ip = packet[BOOTP].yiaddr
        if assigned_ip != "0.0.0.0":
            formatted_mac = format_mac(client_mac)
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Create packet signature for deduplication
            packet_sig = get_packet_signature(packet)
            current_time = datetime.datetime.now()
            
            # Update recent packets
            recent_packets[packet_sig] = current_time
            
            # Always print to OLED/console, even if duplicate
            MultiPrint(f"DHCP ASSIGNMENT ({interface}): {formatted_mac} → {assigned_ip}", important=True)
            # Only update session record and log if new MAC or IP changed
            if (formatted_mac not in seen_assignments) or (seen_assignments[formatted_mac] != assigned_ip):
                seen_assignments[formatted_mac] = assigned_ip
                # Log to file
                try:
                    with open(LOG_FILE, "a") as f:
                        f.write(f"{timestamp},{formatted_mac},{assigned_ip},DHCP,{interface}\n")
                    with open(ASSIGNMENTS_LOG_FILE, "a") as f:
                        f.write(f"{timestamp},{formatted_mac},{assigned_ip},DHCP,{interface}\n")
                except Exception as e:
                    MultiPrint(f"Error writing to log: {e}")

def packet_handler(packet):
    """Packet handler for bridge interface"""
    try:
        if DHCP in packet:
            dhcp_ack_callback(packet, BRIDGE_INTERFACE)
    except Exception as e:
        MultiPrint(f"ERROR processing packet: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global sniffer
    if sniffer and sniffer.running:
        sniffer.stop()

def PrintWithTime(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def main():
    global sniffer, sniffer_wifi
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Monitor DHCP assignments on bridge interface')
    parser.add_argument('--wifi', action='store_true', help='Monitor bridge for all DHCP traffic (wired + wireless)')
    args = parser.parse_args()

    # Override with FORCE_WIFI_SUPPORT if set
    if FORCE_WIFI_SUPPORT:
        args.wifi = True

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Check if we have permission to capture packets
    if os.geteuid() != 0:
        print("ERROR: Root privileges required for packet capture!")
        print("Please run with sudo or as root user.")
        return 1

    if ENABLE_OLED:
        OLEDInit()

    # Print startup info to console only
    print("\n" + "="*49)
    PrintWithTime("Starting Bridge IP Monitor...")
    print("="*50)
    if args.wifi:
        PrintWithTime(f"Monitoring interface: {BRIDGE_INTERFACE} (wired + wireless DHCP)")
        PrintWithTime("Plug in a device to eth0 or connect via WiFi to see its assigned IP address.")
        PrintWithTime("Note: Will detect DHCP assignments from all subnets (192.168.0.x, 192.168.1.x, etc.)")
        PrintWithTime("Monitoring interface: wlan0 (WiFi DHCP)")
    else:
        PrintWithTime(f"Monitoring interface: {BRIDGE_INTERFACE} (wired only)")
        PrintWithTime("Plug in a device to eth0 to see its assigned IP address.")
    PrintWithTime("Press Ctrl+C to stop.\n")

    # Show startup info on OLED (hardcoded here, not in OLEDInit, and not with MultiPrint)
    # In main(), remove duplicate OLED startup lines display (handled in OLEDInit)

    PrintWithTime(f"Starting packet capture on {BRIDGE_INTERFACE}...\n")
    if args.wifi:
        PrintWithTime(f"Starting packet capture on wlan0...\n")

    try:
        # Create AsyncSniffer instance for br0
        sniffer = AsyncSniffer(
            iface=BRIDGE_INTERFACE,
            filter="udp and (port 67 or 68)",
            prn=packet_handler,
            store=0
        )
        # Create AsyncSniffer instance for wlan0 if wifi enabled
        if args.wifi:
            try:
                sniffer_wifi = AsyncSniffer(
                    iface="wlan0",
                    filter="udp and (port 67 or 68)",
                    prn=packet_handler,
                    store=0
                )
            except Exception as e:
                PrintWithTime(f"Warning: Could not start sniffer on wlan0: {e}")
                sniffer_wifi = None
        # Start sniffing
        sniffer.start()
        if args.wifi and sniffer_wifi:
            try:
                sniffer_wifi.start()
            except Exception as e:
                PrintWithTime(f"Warning: Could not start wlan0 sniffer: {e}")
                sniffer_wifi = None
        # Wait for interrupt
        sniffer.join()
        if args.wifi and sniffer_wifi:
            try:
                sniffer_wifi.join()
            except Exception as e:
                PrintWithTime(f"Warning: wlan0 sniffer join failed: {e}")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error starting monitor: {e}")
        return 1
    finally:
        print("Stopping bridge monitor...")
        if sniffer and sniffer.running:
            sniffer.stop()
        if sniffer_wifi and sniffer_wifi.running:
            sniffer_wifi.stop()
        if ENABLE_OLED:
            OLEDDeInit()

    return 0

if __name__ == "__main__":
    sys.exit(main()) 