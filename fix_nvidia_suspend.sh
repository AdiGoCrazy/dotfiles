#!/usr/bin/env bash
set -e

echo "=== Applying NVIDIA Laptop Lid Suspend Fix ==="

echo "1. Writing /etc/modprobe.d/nvidia-power.conf..."
echo "options nvidia NVreg_PreserveVideoMemoryAllocations=1 NVreg_TemporaryFilePath=/var/tmp" | sudo tee /etc/modprobe.d/nvidia-power.conf

echo "2. Configuring /etc/systemd/logind.conf..."
sudo sed -i 's/#HandleLidSwitch=.*/HandleLidSwitch=suspend/' /etc/systemd/logind.conf
sudo sed -i 's/#HandleLidSwitchExternalPower=.*/HandleLidSwitchExternalPower=suspend/' /etc/systemd/logind.conf

echo "3. Rebuilding Initramfs..."
sudo mkinitcpio -P

echo "=== SUCCESS! Please reboot your system for changes to take effect. ==="
