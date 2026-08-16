#!/usr/bin/env bash

# Query local state metrics cleanly without sudo by checking the status daemon directly
if ! tailscale_status=$(tailscale status 2>/dev/null); then
    # Tailscale daemon is stopped or not running
    echo '{"text": "󰖂 Down", "alt": "disconnected", "tooltip": "Tailscale service is offline", "class": "disconnected"}'
    exit 0
fi

# Extract the connection status line securely
if echo "$tailscale_status" | grep -q "Tailscale is stopped"; then
    echo '{"text": "󰖂 Off", "alt": "disconnected", "tooltip": "Tailscale is logged in but stopped.\nClick to connect.", "class": "disconnected"}'
    exit 0
fi

# Capture local client information elements
local_ip=$(tailscale ip -4 | tr -d '[:space:]')
node_name=$(tailscale status --peers=false | awk '{print $2}')

# Format a multi-line hover layout showing active mesh peers
peers_list=$(echo "$tailscale_status" | grep -v "$local_ip" | head -n 10 | awk '{print "• " $2 " (" $1 ") [" $3 "]"}' | sed ':a;N;$!ba;s/\n/\\n/g')

if [ -z "$peers_list" ]; then
    tooltip_text="Node: ${node_name}\nIP: ${local_ip}\n\nNo active peer connections."
else
    tooltip_text="Node: ${node_name}\nIP: ${local_ip}\n\nConnected Peers:\\n${peers_list}"
fi

# Print valid machine-checked inline JSON back to Waybar's buffer
echo "{\"text\": \"󰖂 Up\", \"alt\": \"connected\", \"tooltip\": \"${tooltip_text}\", \"class\": \"connected\"}"
