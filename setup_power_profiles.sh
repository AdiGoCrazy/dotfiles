#!/usr/bin/env bash
set -e

echo "=== Setting up ACPI Power Profiles Service & Permissions ==="

if command -v pacman &>/dev/null; then
    echo "1. Installing power-profiles-daemon..."
    sudo pacman -S --needed --noconfirm power-profiles-daemon || true
    sudo systemctl enable --now power-profiles-daemon || true
fi

echo "2. Setting up udev rule for direct ACPI platform_profile access..."
echo 'ACTION=="add|change", SUBSYSTEM=="acpi", KERNEL=="platform_profile", ATTR{platform_profile}=="*", MODE="0666"' | sudo tee /etc/udev/rules.d/99-platform-profile.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

echo "=== SUCCESS! Power profiles daemon & permissions configured. ==="
