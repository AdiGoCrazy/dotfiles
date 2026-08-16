#!/usr/bin/env bash

case "$1" in
    vol_up)
        wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+
        volume=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print int($2*100)}')
        dunstify -a "Volume" -h int:value:"$volume" -h string:x-dunst-stack-tag:volume "🔊 Volume: ${volume}%"
        ;;
    vol_down)
        wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
        volume=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print int($2*100)}')
        dunstify -a "Volume" -h int:value:"$volume" -h string:x-dunst-stack-tag:volume "🔉 Volume: ${volume}%"
        ;;
    vol_mute)
        wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
        dunstify -a "Volume" -h string:x-dunst-stack-tag:volume "🔇 Mute Toggled"
        ;;
    bright_up)
        brightnessctl set +5%
        bright=$(brightnessctl i | grep -oP '\(\K[^)]+(?=\%)')
        dunstify -a "Brightness" -h int:value:"$bright" -h string:x-dunst-stack-tag:brightness "☀️ Brightness: ${bright}%"
        ;;
    bright_down)
        brightnessctl set 5%-
        bright=$(brightnessctl i | grep -oP '\(\K[^)]+(?=\%)')
        dunstify -a "Brightness" -h int:value:"$bright" -h string:x-dunst-stack-tag:brightness "🌙 Brightness: ${bright}%"
        ;;
esac
