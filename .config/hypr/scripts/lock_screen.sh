#!/usr/bin/env bash

# ==============================================================================
# HYPRLOCK WRAPPER WITH INSTANT LOCK & UNLOCK SOUNDS
# ==============================================================================

# Play lock click sound instantly
paplay /usr/share/sounds/ocean/stereo/button-pressed.oga &

# Launch Hyprlock directly (returns immediately when user authenticates)
hyprlock

# Play unlock chime sound instantly as Hyprlock exits
paplay /usr/share/sounds/ocean/stereo/service-login.oga &
