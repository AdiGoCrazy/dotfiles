#!/usr/bin/env bash

# ==============================================================================
# BATTERY MONITORING DAEMON WITH INSTANT AUDIO & VISUAL NOTIFICATIONS
# - AC online detection (/sys/class/power_supply/AC*/online) for instant plug/unplug tunes
# - Audio tunes + notifications for 30%, 15%, and 5% battery thresholds
# - Single instance enforcement via lockfile
# ==============================================================================

LOCKFILE="/tmp/battery_monitor.lock"
if [ -e "$LOCKFILE" ] && kill -0 "$(cat "$LOCKFILE")" 2>/dev/null; then
    exit 0
fi
echo "$$" > "$LOCKFILE"
trap 'rm -f "$LOCKFILE"; exit' EXIT INT TERM

warn_30=false
warn_15=false
warn_5=false
prev_ac=""

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
    # Locate AC Power Supply (e.g. ACAD, AC, ADP1)
    AC=$(find /sys/class/power_supply/ -maxdepth 1 \( -name "AC*" -o -name "ADP*" -o -name "MAINS*" \) | head -n 1)
    # Locate System Battery (e.g. BAT1, BAT0)
    BAT=$(find /sys/class/power_supply/ -maxdepth 1 -name "BAT*" | head -n 1)

    ac_online=1
    if [ -n "$AC" ] && [ -f "$AC/online" ]; then
        ac_online=$(cat "$AC/online")
    fi

    if [ -n "$BAT" ] && [ -f "$BAT/capacity" ]; then
        capacity=$(cat "$BAT/capacity")
        bat_status=$(cat "$BAT/status" 2>/dev/null || echo "Unknown")

        # Initialize prev_ac state on first loop iteration
        if [ -z "$prev_ac" ]; then
            prev_ac="$ac_online"
        fi

        # Detect Charger Plugged In (AC online state changed 0 -> 1)
        if [ "$ac_online" -eq 1 ] && [ "$prev_ac" -eq 0 ]; then
            dunstify -u normal -r 9991 -i battery-charging "🔌 Charger Connected" "Battery is now charging (${capacity}%)."
            play_sound "/usr/share/sounds/ocean/stereo/power-plug.oga" "power-plug"
            warn_30=false
            warn_15=false
            warn_5=false
        fi

        # Detect Charger Unplugged (AC online state changed 1 -> 0)
        if [ "$ac_online" -eq 0 ] && [ "$prev_ac" -eq 1 ]; then
            dunstify -u normal -r 9991 -i battery "🔋 Charger Unplugged" "Running on battery power (${capacity}%)."
            play_sound "/usr/share/sounds/ocean/stereo/power-unplug.oga" "power-unplug"
        fi

        prev_ac="$ac_online"

        # Low Battery Thresholds (when unplugged or discharging)
        if [ "$ac_online" -eq 0 ] || [ "$bat_status" = "Discharging" ]; then
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

        # Reset threshold flags if capacity rises back above markers
        if [ "$capacity" -gt 30 ]; then warn_30=false; fi
        if [ "$capacity" -gt 15 ]; then warn_15=false; fi
        if [ "$capacity" -gt 5 ];  then warn_5=false;  fi
    fi

    sleep 2  # Fast 2-second polling interval for instant plug/unplug feedback
done
