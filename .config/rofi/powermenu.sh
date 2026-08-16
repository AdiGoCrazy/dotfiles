#!/usr/bin/env bash

# Options to display
options="🔒 Lock\n󰈆 Logout\n󰜉 Reboot\n⏻ Shutdown"

# Call rofi directly using standard command line flag theme injections
chosen=$(echo -e "$options" | rofi -dmenu \
    -i \
    -p "System" \
    -font "JetBrainsMono Nerd Font 13" \
    -width 10 \
    -lines 4 \
    -color-window "#0a0a1a, #ffffff0d, #0a0a1a" \
    -color-normal "#00000000, #e0def4, #00000000, #eb1c5233, #ffffff")

# Process the choice securely via systemd backend tools
case "$chosen" in
    *Lock)
        hyprlock
        ;;
    *Logout)
        loginctl terminate-user $USER
        ;;
    *Reboot)
        systemctl reboot
        ;;
    *Shutdown)
        systemctl poweroff
        ;;
esac