# IP Spy

A network diagnostic tool that transforms a Raspberry Pi CM4-DUAL-ETH-MINI into a transparent network bridge that identifies the IP address of any device plugged into it. (as long as they are requesting an ip via DHCP)

[![IP Spy Demo](https://img.youtube.com/vi/0MbKMwA7UCU/maxresdefault.jpg)](https://www.youtube.com/watch?v=0MbKMwA7UCU)

*Click the image above to watch the demo video*

## What It Does

IP Spy answers the simple question: **"What IP address did this device just get?"**

When you plug any device (phone, computer, IoT device, etc.) inbetween a device and the router it will:
- Transparently bridge the device to your network
- Monitor DHCP and ARP traffic in real-time
- Display the MAC and IP of the device on the OLED display

## Hardware Required

- **Raspberry Pi CM4-DUAL-ETH-MINI** with dual ethernet ports, or a normal Pi with an extra ethernet port plugged in with USB
- MicroSD card with Raspberry Pi OS
- Network cables


## Network Setup

```
Test Device → [eth0] → [br0 Bridge] → [eth1] → Main Network Router
```

The CM4 creates a **Linux bridge (`br0`)** that transparently connects `eth0` and `eth1`, allowing traffic to pass through while monitoring device connections.

## Quick Setup

### 1. Install Dependencies
```bash
sudo apt update && sudo apt install -y python3-pip python3-scapy bridge-utils
pip3 install -r requirements.txt
```

### 2. Enable Bridge Service
```bash
# Enable the bridge service for boot persistence
sudo systemctl enable network-bridge.service
sudo systemctl start network-bridge.service
```

### 3. Start Monitoring
```bash
# Start the bridge monitor
sudo python3 bridge_monitor.py

# In another terminal, watch for IP assignments
tail -f device_ip.txt
```

### 4. Test It
1. Connect your router/network to `eth1`
2. Connect a test device to `eth0` (actually, you can reverse the plugs, it doesn't matter)
3. Power on the test device
4. Watch the IP assignment appear!  (either as a message from the shell or the OLED display if you've set that up)

## Bridge Configuration

The bridge is automatically configured by the `network-bridge.service` systemd service, which:

- Creates the `br0` bridge interface
- Adds `eth0` and `eth1` to the bridge
- Brings all interfaces up
- Persists across reboots

### Manual Bridge Setup (if needed)
```bash
sudo ./setup-bridge.sh
```

### Check Bridge Status
```bash
brctl show br0
ip addr show br0
```

## Troubleshooting

### Bridge Not Working
```bash
# Check service status
sudo systemctl status network-bridge.service

# Restart bridge
sudo systemctl restart network-bridge.service
```
### Slow boot with no network

Disable "Wait for Network at Boot" with raspi-config or reduce the timeout.  We don't really need things plugged in when the Pi boots to work, so I set the timeout very low on the Pi.

### No IP Assignments Detected
```bash
# Check uplink connectivity
ping 192.168.1.1

# Verify bridge is passing traffic
sudo tcpdump -i br0 -c 10
```

### Permission Errors
```bash
# Run monitoring scripts with sudo
sudo python3 bridge_monitor.py
```

## Files Overview

- `bridge_monitor.py` - Main monitoring script
- `setup-bridge.sh` - Bridge configuration script
- `network-bridge.service` - Systemd service for boot persistence
- `oled-loading.service` - Systemd service to show "Loading..." on OLED display early in boot sequence
- `oled_show_loading.py` - Script that displays loading message on OLED
- `requirements.txt` - Python dependencies
- `simple_start.sh` - A thing to run it with the virtual env oled-venv, but I mean, you don't have to use one, or you could do it with conda or whatever, it's not that important

### OLED Loading Service

The `oled-loading.service` can be enabled to display a "Loading..." message on the OLED display very early in the Raspberry Pi boot sequence. This is useful for providing visual feedback that the system is starting up.

**To enable the OLED loading service:**
```bash
sudo systemctl enable oled-loading.service
sudo systemctl start oled-loading.service
```

**To disable it:**
```bash
sudo systemctl disable oled-loading.service
```

The service runs early in the boot process (after local filesystem is mounted) and will silently exit if the OLED display is not connected or if there are any issues, ensuring it doesn't interfere with the boot process.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

**Created by Seth A. Robinson**

- **Website**: [rtsoft.com](https://rtsoft.com)
- **YouTube**: [@RobinsonTechnologies](https://youtube.com/@RobinsonTechnologies)
- **Twitter/X**: [@rtsoft](https://twitter.com/rtsoft)
- **Bluesky**: [@rtsoft.com](https://bsky.app/profile/rtsoft.com)
- **Mastodon**: [@rtsoft@mastodon.gamedev.place](https://mastodon.gamedev.place/@rtsoft)

*This project was developed with assistance from AI tools for code generation and documentation.*

