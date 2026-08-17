#!/usr/bin/env bash

# ==============================================================================
# HYPRLOCK WRAPPER WITH INSTANT LOCK & UNLOCK SOUNDS
# ==============================================================================

# Play lock click sound instantly on trigger
paplay /usr/share/sounds/ocean/stereo/button-pressed.oga &

# Launch Hyprlock (blocks until user authenticates and unlocks)
uwsm app -- hyprlock

# Play unlock chime sound immediately upon successful unlock
paplay /usr/share/sounds/ocean/stereo/service-login.oga &
