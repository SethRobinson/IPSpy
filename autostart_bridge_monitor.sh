#!/bin/bash
# Autostart script for bridge monitor

# Check if we're on a real terminal (not SSH)
if [ -n "$SSH_CONNECTION" ]; then
    echo "SSH session detected, not starting bridge monitor"
    exit 0
fi

#disable it for now
#exit 
#sleep 2

# Check if already running
if pgrep -f "bridge_monitor.py" > /dev/null; then
    echo "Bridge monitor already running"
    exit 0
fi

# Clear the screen
clear

echo "=========================================="
echo "CM4 Bridge Monitor - Auto Start"
echo "=========================================="
echo "Starting in 5 seconds..."
echo "Press Ctrl+C to cancel"
echo ""

# Give user chance to cancel
#sleep 1

# Start the bridge monitor
cd /home/pi
sudo ./simple_start.sh

# If monitor exits, give user time to see any error messages
echo ""
echo "Bridge monitor stopped. Press Enter to continue..."
read -r 
