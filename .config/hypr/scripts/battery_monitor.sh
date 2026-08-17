#!/usr/bin/env bash

# ==============================================================================
# BATTERY MONITORING DAEMON WITH AUDIO & VISUAL NOTIFICATIONS
# - Audio tunes on Charger Connected / Disconnected
# - Audio tunes + notifications for 30%, 15%, and 5% battery thresholds
# ==============================================================================

warn_30=false
warn_15=false
warn_5=false
prev_status=""

play_sound() {
    local sound_file="$1"
    local sound_id="$2"

    if [ -f "$sound_file" ]; then
        paplay "$sound_file" &>/dev/null || pw-play "$sound_file" &>/dev/null || true
    elif command -v canberra-gtk-play &>/dev/null; then
        canberra-gtk-play -i "$sound_id" &>/dev/null || true
    fi
}

while true; do
    BAT=$(find /sys/class/power_supply/ -maxdepth 1 -name "BAT*" | head -n 1)

    if [ -n "$BAT" ] && [ -f "$BAT/capacity" ] && [ -f "$BAT/status" ]; then
        capacity=$(cat "$BAT/capacity")
        status=$(cat "$BAT/status")

        # Initialize prev_status on startup
        if [ -z "$prev_status" ]; then
            prev_status="$status"
        fi

        # Detect Charger Plugging In
        if [ "$status" != "Discharging" ] && [ "$prev_status" = "Discharging" ]; then
            dunstify -u normal -r 9991 -i battery-charging "🔌 Charger Connected" "Battery is now charging (${capacity}%)."
            play_sound "/usr/share/sounds/ocean/stereo/power-plug.oga" "power-plug"
            warn_30=false
            warn_15=false
            warn_5=false
        fi

        # Detect Charger Unplugging
        if [ "$status" = "Discharging" ] && [ "$prev_status" != "Discharging" ]; then
            dunstify -u normal -r 9991 -i battery "🔋 Charger Unplugged" "Running on battery power (${capacity}%)."
            play_sound "/usr/share/sounds/ocean/stereo/power-unplug.oga" "power-unplug"
        fi

        prev_status="$status"

        # Check Discharging Thresholds
        if [ "$status" = "Discharging" ]; then
            if [ "$capacity" -le 5 ] && [ "$warn_5" = false ]; then
                dunstify -u critical -r 9991 -i battery-empty "⚠️ Battery Critical!" "Battery is at ${capacity}%. Plug in charger immediately!"
                play_sound "/usr/share/sounds/ocean/stereo/dialog-error-serious.oga" "dialog-error"
                warn_5=true
                warn_15=true
                warn_30=true
            elif [ "$capacity" -le 15 ] && [ "$warn_15" = false ]; then
                dunstify -u critical -r 9991 -i battery-caution "🪫 Battery Very Low" "Battery is at ${capacity}%. Consider plugging in your charger."
                play_sound "/usr/share/sounds/ocean/stereo/battery-caution.oga" "battery-caution"
                warn_15=true
                warn_30=true
            elif [ "$capacity" -le 30 ] && [ "$warn_30" = false ]; then
                dunstify -u normal -r 9991 -i battery-low "🔋 Battery Low" "Battery is down to ${capacity}%."
                play_sound "/usr/share/sounds/ocean/stereo/battery-low.oga" "battery-low"
                warn_30=true
            fi
        else
            warn_30=false
            warn_15=false
            warn_5=false
        fi

        # Reset specific markers if battery level rises back above thresholds
        if [ "$capacity" -gt 30 ]; then warn_30=false; fi
        if [ "$capacity" -gt 15 ]; then warn_15=false; fi
        if [ "$capacity" -gt 5 ];  then warn_5=false;  fi
    fi

    sleep 10  # Check battery state every 10 seconds for responsive audio
done
