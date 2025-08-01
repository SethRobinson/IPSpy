#!/bin/bash
# Simple launcher for bridge monitor

if [ "$(id -u)" -ne 0 ]; then
    echo "[ERROR] This script must be run with sudo. Aborting."
    exit 1
fi

# Use the virtual environment Python directly with sudo
if [ -f "/home/pi/oled-venv/bin/python3" ]; then
    exec sudo /home/pi/oled-venv/bin/python3 /home/pi/bridge_monitor.py "$@"
else
    # Fallback to system Python if venv doesn't exist
    exec sudo python3 /home/pi/bridge_monitor.py "$@"
fi 