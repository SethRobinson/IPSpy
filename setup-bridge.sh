#!/bin/bash
# Setup network bridge for device monitoring

# Create bridge if it doesn't exist
if ! brctl show | grep -q "^br0"; then
    brctl addbr br0
fi

# Bring down interfaces
ip link set eth0 down
ip link set eth1 down

# Add interfaces to bridge if not already added
if ! brctl show br0 | grep -q "eth0"; then
    brctl addif br0 eth0
fi

if ! brctl show br0 | grep -q "eth1"; then
    brctl addif br0 eth1
fi

# Bring everything up
ip link set eth0 up
ip link set eth1 up
ip link set br0 up

# Request IP for bridge via DHCP with 15 second timeout
timeout 15 dhclient -v br0 2>/dev/null || true

echo "Bridge br0 configured successfully" 