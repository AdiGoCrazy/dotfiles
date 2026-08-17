#!/usr/bin/env bash

# ==============================================================================
# BATTERY MONITORING DAEMON
# Notifies user at 30%, 15%, and 5% discharging thresholds via dunstify.
# ==============================================================================

warn_30=false
warn_15=false
warn_5=false

while true; do
    # Locate system battery dynamically
    BAT=$(find /sys/class/power_supply/ -maxdepth 1 -name "BAT*" | head -n 1)

    if [ -n "$BAT" ] && [ -f "$BAT/capacity" ] && [ -f "$BAT/status" ]; then
        capacity=$(cat "$BAT/capacity")
        status=$(cat "$BAT/status")

        if [ "$status" = "Discharging" ]; then
            if [ "$capacity" -le 5 ] && [ "$warn_5" = false ]; then
                dunstify -u critical -r 9991 -i battery-empty "⚠️ Battery Critical!" "Battery is at ${capacity}%. Plug in charger immediately!"
                warn_5=true
                warn_15=true
                warn_30=true
            elif [ "$capacity" -le 15 ] && [ "$warn_15" = false ]; then
                dunstify -u critical -r 9991 -i battery-caution "🪫 Battery Very Low" "Battery is at ${capacity}%. Consider plugging in your charger."
                warn_15=true
                warn_30=true
            elif [ "$capacity" -le 30 ] && [ "$warn_30" = false ]; then
                dunstify -u normal -r 9991 -i battery-low "🔋 Battery Low" "Battery is down to ${capacity}%."
                warn_30=true
            fi
        else
            # Reset all warnings when charging or plugged in
            warn_30=false
            warn_15=false
            warn_5=false
        fi

        # Reset threshold flags if capacity rises back above marker
        if [ "$capacity" -gt 30 ]; then warn_30=false; fi
        if [ "$capacity" -gt 15 ]; then warn_15=false; fi
        if [ "$capacity" -gt 5 ];  then warn_5=false;  fi
    fi

    sleep 30  # Check battery state every 30 seconds
done
