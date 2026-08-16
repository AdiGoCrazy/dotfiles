#!/usr/bin/env bash

# Keep track of whether we've already warned the user
low_warned=false
crit_warned=false

while true; do
    # Read native power metrics
    BAT=/sys/class/power_supply/BAT0
    if [ -d "$BAT" ]; then
        capacity=$(cat "$BAT"/capacity)
        status=$(cat "$BAT"/status)

        if [ "$status" = "Discharging" ]; then
            if [ "$capacity" -le 10 ] && [ "$crit_warned" = false ]; then
                dunstify -u critical "🔋 Battery Critical!" "Plug in immediately! Remaining: ${capacity}%"
                crit_warned=true
                low_warned=true
            elif [ "$capacity" -le 20 ] && [ "$low_warned" = false ]; then
                dunstify -u normal "🔋 Battery Low" "Consider connecting your charger. Remaining: ${capacity}%"
                low_warned=true
            fi
        else
            # Reset trackers when charger is plugged back in
            low_warned=false
            crit_warned=false
        fi
    fi
    sleep 60  # Check every 60 seconds
done
