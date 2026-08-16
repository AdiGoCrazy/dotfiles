# 🌌 Hyprland & Waybar Aesthetic Dotfiles

A modern, high-performance, and visually refined **Hyprland + Waybar** rice for Arch Linux, featuring smooth animations, glassmorphism UI, custom OSD notifications, and real-time system monitoring.

---

## 🎨 Key Features

* **Hyprland Compositor**: Custom bezier animation curves, soft shadows, background blur/vibrancy, and UWSM systemd unit integration.
* **Waybar Capsule**: Floating frosted glass bar with live telemetry:
  * Network bandwidth monitor (`network#speed`)
  * NVIDIA GPU utilization & temperature (`custom/gpu`)
  * Ollama local LLM status indicator (`custom/ollama`)
  * Docker active container dashboard (`custom/docker`)
  * CPU, Memory, Disk, Audio, Wi-Fi, Bluetooth, Battery, and Update checkers.
* **Notifications & OSD**: Custom Dunst OSD volume & brightness popups with smooth auto-expiry.
* **Terminal**: Customized Kitty terminal theme.
* **Launcher & Power Menu**: Wofi drun launcher and Rofi custom powermenu script.

---

## 🚀 Quick Start (Automated Installation)

Clone this repository and run the automated installer:

```bash
git clone https://github.com/YOUR_USERNAME/dotfiles.git ~/dotfiles
cd ~/dotfiles
chmod +x install.sh
./install.sh
```

> [!NOTE]
> The installer automatically creates a timestamped backup of your current `~/.config/{hypr,waybar,rofi,dunst,kitty}` directories in `~/.config_backup_<timestamp>` before applying new files.

---

## 🎹 Keybindings Reference

### 🚀 Applications & Launchers
| Keybinding | Action |
| :--- | :--- |
| <kbd>SUPER</kbd> + <kbd>Q</kbd> | Launch Kitty Terminal |
| <kbd>SUPER</kbd> + <kbd>E</kbd> | Launch Dolphin File Manager |
| <kbd>SUPER</kbd> + <kbd>F</kbd> | Launch Firefox |
| <kbd>SUPER</kbd> + <kbd>R</kbd> | Open Wofi App Launcher |
| <kbd>SUPER</kbd> + <kbd>B</kbd> | Open Bluetooth Manager |
| <kbd>SUPER</kbd> + <kbd>V</kbd> | Open Audio Control (Pavucontrol) |
| <kbd>SUPER</kbd> + <kbd>Backspace</kbd> | Lock Screen (Hyprlock) |

### 🪟 Window & Session Management
| Keybinding | Action |
| :--- | :--- |
| <kbd>SUPER</kbd> + <kbd>W</kbd> | Close Active Window |
| <kbd>SUPER</kbd> + <kbd>M</kbd> | Exit Hyprland (UWSM Stop) |
| <kbd>SUPER</kbd> + <kbd>K</kbd> | Restart Waybar |
| <kbd>SUPER</kbd> + <kbd>Arrow Keys</kbd> | Move Window Focus |
| <kbd>SUPER</kbd> + <kbd>1-0</kbd> | Switch Workspaces |
| <kbd>SUPER</kbd> + <kbd>SHIFT</kbd> + <kbd>1-0</kbd> | Move Window to Workspace |
| <kbd>SUPER</kbd> + <kbd>S</kbd> | Toggle Scratchpad Workspace |

### 📸 Screenshots & Media OSD
| Keybinding | Action |
| :--- | :--- |
| <kbd>SUPER</kbd> + <kbd>ALT</kbd> + <kbd>S</kbd> | Screenshot Area to Swappy |
| <kbd>Volume Up/Down/Mute</kbd> | Volume Controls (with Dunst OSD) |
| <kbd>Brightness Up/Down</kbd> | Screen Brightness Controls (with Dunst OSD) |
| <kbd>Media Play/Pause/Next/Prev</kbd> | Media Control (`playerctl`) |

---

## 📂 Repository Layout

```
dotfiles/
├── .config/
│   ├── hypr/               # Hyprland configs, lockscreen, papers & scripts
│   ├── waybar/             # Waybar layout, stylesheet & status scripts
│   ├── rofi/               # Rofi powermenu launcher scripts
│   ├── dunst/              # Notification daemon setup & assets
│   └── kitty/              # Kitty terminal configuration
├── install.sh              # Interactive / automated setup script
├── pkglist.txt             # Categorized Arch / AUR dependencies list
└── README.md               # Repository documentation
```

---

## 🛠️ Manual Setup

If you prefer to install dependencies and configurations manually:

1. **Install required dependencies**:
   ```bash
   sudo pacman -S --needed $(grep -vE '^\s*#|^\s*$' pkglist.txt)
   ```
2. **Copy configurations**:
   ```bash
   cp -r .config/* ~/.config/
   chmod +x ~/.config/hypr/scripts/*.sh ~/.config/waybar/scripts/*.sh ~/.config/rofi/*.sh
   ```

---

## 📄 License & Credits

Distributed under the MIT License. Feel free to fork and customize for your own Hyprland setup!
