#!/usr/bin/env bash

# ==============================================================================
# HYPRLAND & WAYBAR RICE AUTOMATED INSTALLER
# ==============================================================================

set -euo pipefail

# --- Color Definitions ---
BOLD="\033[1m"
GREEN="\033[1;32m"
CYAN="\033[1;36m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

info()  { echo -e "${CYAN}[INFO]${RESET} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${RESET} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${RESET} $1"; }
error() { echo -e "${RED}[ERROR]${RESET} $1"; exit 1; }

echo -e "${BOLD}${CYAN}"
echo "  _  _                 _                 _   ___  _            "
echo " | || | _  _  _ __ _ _| | __ _ _ _  __| | | _ \(_)__ ___  "
echo " | __ || || || '_ \ '_| |/ _\` | ' \/ _\` | |   /| / _/ -_) "
echo " |_||_| \_, || .__/_| |_|\__,_|_||_\__,_| |_|_\|_\__\___| "
echo "        |__/ |_|                                          "
echo -e "${RESET}"
echo -e "${BOLD}Automated Hyprland & Waybar Setup Installer${RESET}\n"

# --- Step 1: System Checks ---
info "Checking Linux distribution..."
if [ ! -f /etc/arch-release ]; then
    warn "This installer is designed for Arch Linux. Proceeding anyway..."
fi

# --- Step 2: Detect Package Manager & AUR Helper ---
info "Detecting package manager..."
if ! command -v pacman &>/dev/null; then
    error "pacman package manager not found. Please run this script on Arch Linux."
fi

AUR_HELPER=""
if command -v yay &>/dev/null; then
    AUR_HELPER="yay"
elif command -v paru &>/dev/null; then
    AUR_HELPER="paru"
else
    warn "Neither 'yay' nor 'paru' was detected."
    read -rp "Would you like to install 'yay' automatically? (y/N): " choice
    case "$choice" in
        [yY][eE][sS]|[yY])
            info "Installing yay..."
            sudo pacman -S --needed --noconfirm base-devel git
            git clone https://aur.archlinux.org/yay.git /tmp/yay
            (cd /tmp/yay && makepkg -si --noconfirm)
            rm -rf /tmp/yay
            AUR_HELPER="yay"
            ;;
        *)
            warn "Skipping AUR helper installation. Package installation might be incomplete."
            ;;
    esac
fi

# --- Step 3: Install Required Packages ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKGLIST="$SCRIPT_DIR/pkglist.txt"

if [ -f "$PKGLIST" ]; then
    info "Installing packages from pkglist.txt..."
    # Filter out empty lines and comments
    mapfile -t PACKAGES < <(grep -vE '^\s*#|^\s*$' "$PKGLIST")
    
    if [ -n "$AUR_HELPER" ]; then
        $AUR_HELPER -S --needed --noconfirm "${PACKAGES[@]}" || warn "Some packages could not be installed automatically."
    else
        sudo pacman -S --needed --noconfirm "${PACKAGES[@]}" || warn "Some packages could not be installed automatically."
    fi
else
    warn "pkglist.txt not found! Skipping automated package installation."
fi

# --- Step 4: Backup Existing Configurations ---
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$HOME/.config_backup_$TIMESTAMP"
CONFIG_DEST="$HOME/.config"

info "Backing up existing configurations to $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

CONFIGS=("hypr" "waybar" "rofi" "dunst" "kitty")
for cfg in "${CONFIGS[@]}"; do
    if [ -d "$CONFIG_DEST/$cfg" ]; then
        info "Backing up $CONFIG_DEST/$cfg..."
        mv "$CONFIG_DEST/$cfg" "$BACKUP_DIR/"
    fi
done

# --- Step 5: Install Dotfiles ---
info "Installing configuration files to $CONFIG_DEST..."
mkdir -p "$CONFIG_DEST"

for cfg in "${CONFIGS[@]}"; do
    if [ -d "$SCRIPT_DIR/.config/$cfg" ]; then
        info "Deploying $cfg configuration..."
        cp -r "$SCRIPT_DIR/.config/$cfg" "$CONFIG_DEST/"
    fi
done

# --- Step 6: Set Executable Permissions on Scripts ---
info "Ensuring script execution permissions..."
chmod +x "$CONFIG_DEST/hypr/scripts/"*.sh 2>/dev/null || true
chmod +x "$CONFIG_DEST/waybar/scripts/"*.sh 2>/dev/null || true
chmod +x "$CONFIG_DEST/rofi/"*.sh 2>/dev/null || true

# --- Step 7: Final Completion Summary ---
echo ""
success "Installation complete!"
echo -e "${CYAN}--------------------------------------------------${RESET}"
echo -e "${BOLD}Next Steps:${RESET}"
echo -e " 1. If you are inside Hyprland, reload your session using ${BOLD}SUPER + SHIFT + R${RESET} or restart Waybar with ${BOLD}SUPER + K${RESET}."
echo -e " 2. If launching a new session, run: ${BOLD}uwsm start hyprland-uwsm.desktop${RESET} or ${BOLD}Hyprland${RESET}"
echo -e " 3. Backups of your previous configs are saved in: ${YELLOW}$BACKUP_DIR${RESET}"
echo -e "${CYAN}--------------------------------------------------${RESET}\n"
