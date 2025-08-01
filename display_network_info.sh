#!/bin/bash
# Display concise network and bridge status for CM4-DUAL-ETH-MINI

BRIDGE=br0

# Show bridge summary
if command -v brctl &>/dev/null; then
    echo "==== Bridge Summary (brctl show) ===="
    sudo brctl show
elif command -v bridge &>/dev/null; then
    echo "==== Bridge Summary (bridge link) ===="
    sudo bridge link
else
    echo "[WARN] No bridge utilities found."
fi

echo
for IFACE in $BRIDGE eth0 eth1; do
    echo "==== Interface: $IFACE ===="
    # MAC address
    if [ -f /sys/class/net/$IFACE/address ]; then
        echo -n "MAC Address: "; cat /sys/class/net/$IFACE/address
    fi
    # IP addresses (IPv4 and IPv6)
    ip -brief addr show $IFACE | awk '{for(i=3;i<=NF;i++) print $i}' | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}|([a-fA-F0-9:]+:+)+[a-fA-F0-9]+/[0-9]{1,3}' | while read ip; do
        echo "IP Address: $ip"
    done
    # Carrier state
    if [ -f /sys/class/net/$IFACE/carrier ]; then
        echo -n "Carrier: "; cat /sys/class/net/$IFACE/carrier
    fi
    # Operational state
    if [ -f /sys/class/net/$IFACE/operstate ]; then
        echo -n "Operational state: "; cat /sys/class/net/$IFACE/operstate
    fi
    # Bridge membership
    if [ -d /sys/class/net/$IFACE/brif ]; then
        echo -n "Bridge members: "
        ls /sys/class/net/$IFACE/brif | xargs
    fi
    if command -v bridge &>/dev/null; then
        bridge fdb show dev $IFACE 2>/dev/null | grep -v "self" | awk '{print "FDB: "$1, $2, $3, $4}'
    fi
    echo "-----------------------------"
done 