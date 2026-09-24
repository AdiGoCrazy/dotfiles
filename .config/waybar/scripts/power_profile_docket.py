#!/usr/bin/env python3

import sys
import os
import subprocess

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

ALL_LOCKS = [
    "/tmp/bt_docket.lock",
    "/tmp/wifi_docket.lock",
    "/tmp/audio_docket.lock",
    "/tmp/clock_docket.lock",
    "/tmp/power_docket.lock",
    "/tmp/power_profile_docket.lock"
]
CURRENT_LOCK = "/tmp/power_profile_docket.lock"

# Handle Waybar status query subcommand
def get_current_profile():
    profile = "balanced"
    if os.path.exists("/sys/firmware/acpi/platform_profile"):
        try:
            with open("/sys/firmware/acpi/platform_profile", "r") as f:
                profile = f.read().strip()
        except Exception:
            pass
    else:
        try:
            out = subprocess.check_output(["powerprofilesctl", "get"], text=True).strip()
            if out:
                profile = out
        except Exception:
            pass
    return profile

if len(sys.argv) > 1 and sys.argv[1] == "--status":
    prof = get_current_profile()
    if prof in ["low-power", "quiet", "power-saver"]:
        icon = "🍃"
        label = "Power Saver"
        cls = "power-saver"
    elif prof in ["performance", "custom"]:
        icon = "🚀"
        label = "Performance"
        cls = "performance"
    else:
        icon = "⚖️"
        label = "Balanced"
        cls = "balanced"
    
    print(f'{{"text": "{icon} {label}", "class": "{cls}", "tooltip": "Power Mode: {label}\\nLeft-Click: Open Power Profiles Menu"}}')
    sys.exit(0)

# Close any other open dockets for mutual exclusion
for lock in ALL_LOCKS:
    if lock != CURRENT_LOCK and os.path.exists(lock):
        try:
            with open(lock, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 15)
        except Exception:
            pass

# Single-instance toggle behavior
if os.path.exists(CURRENT_LOCK):
    try:
        with open(CURRENT_LOCK, 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, 15)
        sys.exit(0)
    except Exception:
        pass

with open(CURRENT_LOCK, 'w') as f:
    f.write(str(os.getpid()))

def cleanup():
    if os.path.exists(CURRENT_LOCK):
        try:
            os.remove(CURRENT_LOCK)
        except Exception:
            pass

class PowerProfileDocket(Gtk.Window):
    def __init__(self):
        super().__init__(title="Power Profile Docket")
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(320, 290)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)

        self.apply_css()

        # Root Card Container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_name("docket-root")
        main_box.set_margin_top(4)
        main_box.set_margin_bottom(4)
        main_box.set_margin_start(4)
        main_box.set_margin_end(4)
        self.add(main_box)

        # Inner Content Box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_margin_top(14)
        content_box.set_margin_bottom(14)
        content_box.set_margin_start(14)
        content_box.set_margin_end(14)
        main_box.pack_start(content_box, True, True, 0)

        # --- Header Region ---
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span font='13' weight='bold' foreground='#c4a7e7'>⚡ Power Mode Profiles</span>")
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, False, False, 0)

        self.status_lbl = Gtk.Label()
        self.status_lbl.set_halign(Gtk.Align.START)
        header_box.pack_start(self.status_lbl, False, False, 0)

        content_box.pack_start(header_box, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(sep, False, False, 2)

        # --- Profile Options Box ---
        options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # 1. Power Saver Card
        self.btn_saver = Gtk.Button()
        self.btn_saver.set_name("btn-prof-saver")
        self.btn_saver.set_label("🍃  Power Saver   (Max Battery & Quiet)")
        self.btn_saver.connect("clicked", lambda b: self.set_profile("low-power"))
        options_box.pack_start(self.btn_saver, False, False, 0)

        # 2. Balanced Card
        self.btn_balanced = Gtk.Button()
        self.btn_balanced.set_name("btn-prof-balanced")
        self.btn_balanced.set_label("⚖️  Balanced      (Standard Performance)")
        self.btn_balanced.connect("clicked", lambda b: self.set_profile("balanced"))
        options_box.pack_start(self.btn_balanced, False, False, 0)

        # 3. Performance / Allow-Everything Card
        self.btn_perf = Gtk.Button()
        self.btn_perf.set_name("btn-prof-perf")
        self.btn_perf.set_label("🚀  Performance   (Unrestricted Power)")
        self.btn_perf.connect("clicked", lambda b: self.set_profile("performance"))
        options_box.pack_start(self.btn_perf, False, False, 0)

        content_box.pack_start(options_box, True, True, 0)

        # Auto-close on mouse exit
        self.connect("leave-notify-event", self.on_mouse_leave)
        self.connect("destroy", lambda w: cleanup())

        # Start 1000ms loop to monitor external profile changes
        GLib.timeout_add(1000, self.update_ui_state)
        self.update_ui_state()

    def set_profile(self, target_prof):
        # Try powerprofilesctl first
        success = False
        try:
            subprocess.run(["powerprofilesctl", "set", target_prof], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            success = True
        except Exception:
            pass

        if not success and os.path.exists("/sys/firmware/acpi/platform_profile"):
            try:
                with open("/sys/firmware/acpi/platform_profile", "w") as f:
                    f.write(target_prof)
                success = True
            except Exception:
                # If permission denied, attempt pkexec / tee
                try:
                    subprocess.run(f"echo {target_prof} | sudo tee /sys/firmware/acpi/platform_profile", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

        self.update_ui_state()

    def update_ui_state(self):
        current = get_current_profile()
        
        if current in ["low-power", "quiet", "power-saver"]:
            self.status_lbl.set_markup("<span font='9' foreground='#9ccfd8'>Active Mode: <b>Power Saver</b></span>")
            self.btn_saver.set_name("btn-prof-saver-active")
            self.btn_balanced.set_name("btn-prof-balanced")
            self.btn_perf.set_name("btn-prof-perf")
        elif current in ["performance", "custom"]:
            self.status_lbl.set_markup("<span font='9' foreground='#eb1c52'>Active Mode: <b>Performance (Unrestricted)</b></span>")
            self.btn_saver.set_name("btn-prof-saver")
            self.btn_balanced.set_name("btn-prof-balanced")
            self.btn_perf.set_name("btn-prof-perf-active")
        else:
            self.status_lbl.set_markup("<span font='9' foreground='#f6c177'>Active Mode: <b>Balanced</b></span>")
            self.btn_saver.set_name("btn-prof-saver")
            self.btn_balanced.set_name("btn-prof-balanced-active")
            self.btn_perf.set_name("btn-prof-perf")

        return True

    def apply_css(self):
        css = b"""
        window {
            background-color: transparent;
        }
        #docket-root {
            background-color: rgba(10, 10, 26, 0.90);
            border: 1px solid rgba(196, 167, 231, 0.3);
            border-radius: 16px;
            color: #e0def4;
            font-family: 'JetBrainsMono Nerd Font', sans-serif;
        }
        button#btn-prof-saver, button#btn-prof-balanced, button#btn-prof-perf {
            background: rgba(255, 255, 255, 0.05);
            color: #e0def4;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 12px;
            font-weight: bold;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.2s ease;
        }
        button#btn-prof-saver:hover {
            background: rgba(156, 207, 216, 0.25);
            color: #9ccfd8;
            border-color: rgba(156, 207, 216, 0.5);
        }
        button#btn-prof-balanced:hover {
            background: rgba(246, 193, 119, 0.25);
            color: #f6c177;
            border-color: rgba(246, 193, 119, 0.5);
        }
        button#btn-prof-perf:hover {
            background: rgba(235, 28, 82, 0.25);
            color: #eb1c52;
            border-color: rgba(235, 28, 82, 0.5);
        }
        button#btn-prof-saver-active {
            background: rgba(156, 207, 216, 0.35);
            color: #ffffff;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 12px;
            font-weight: bold;
            border: 2px solid #9ccfd8;
        }
        button#btn-prof-balanced-active {
            background: rgba(246, 193, 119, 0.35);
            color: #ffffff;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 12px;
            font-weight: bold;
            border: 2px solid #f6c177;
        }
        button#btn-prof-perf-active {
            background: rgba(235, 28, 82, 0.45);
            color: #ffffff;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 12px;
            font-weight: bold;
            border: 2px solid #eb1c52;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_mouse_leave(self, widget, event):
        alloc = self.get_allocation()
        if not (0 <= event.x <= alloc.width and 0 <= event.y <= alloc.height):
            self.close()

if __name__ == "__main__":
    win = PowerProfileDocket()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
