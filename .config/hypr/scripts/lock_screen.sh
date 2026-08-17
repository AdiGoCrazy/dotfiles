#!/usr/bin/env bash

# ==============================================================================
# HYPRLOCK WRAPPER WITH INSTANT LOCK SOUND
# ==============================================================================

# Play lock click sound instantly on trigger
paplay /usr/share/sounds/ocean/stereo/button-pressed.oga &

# Launch Hyprlock (Instant unlock sound is handled directly inside hyprlock.conf on_unlock_cmd)
uwsm app -- hyprlock
