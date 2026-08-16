#!/bin/bash

# Configuration: Target name for the floating window instance
INSTANCE="waybar_calendar_panel"

# If the window is already active, close it down cleanly
if pgrep -f "kitty --class $INSTANCE" > /dev/null; then
    pkill -f "kitty --class $INSTANCE"
    exit 0
fi

# Launch an interactive terminal view mapped directly to the custom class 
# Using a clear continuous view loop with an immediate prompt listener
kitty --class "$INSTANCE" -e sh -c "
    clear
    echo -e '\033[1;34m📅 System Master Agenda\033[0m'
    echo '----------------------------------------'
    khal calendar
    echo ''
    echo '----------------------------------------'
    echo 'Press [Enter] or click away to close...'
    read
"