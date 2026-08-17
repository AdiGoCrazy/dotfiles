#!/usr/bin/env python3

import sys
import os
import subprocess
import re

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

ALL_LOCKS = [
    "/tmp/bt_docket.lock",
    "/tmp/wifi_docket.lock",
    "/tmp/audio_docket.lock",
    "/tmp/clock_docket.lock",
    "/tmp/power_docket.lock"
]
CURRENT_LOCK = "/tmp/power_docket.lock"

# Close any other open dockets for mutual exclusion
for lock in ALL_LOCKS:
    if lock != CURRENT_LOCK and os.path.exists(lock):
        try:
            with open(lock, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 15)
        except Exception:
            pass

# Single-instance toggle behavior for Power Docket
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

class PowerDocket(Gtk.Window):
    def __init__(self):
        super().__init__(title="Power Docket")
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(280, 360)

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
        title_label.set_markup("<span font='13' weight='bold' foreground='#eb1c52'>⏻ System Power</span>")
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, False, False, 0)

        uptime_str = self.get_uptime()
        uptime_lbl = Gtk.Label()
        uptime_lbl.set_markup(f"<span font='9' foreground='#6e6a86'>Uptime: {uptime_str}</span>")
        uptime_lbl.set_halign(Gtk.Align.START)
        header_box.pack_start(uptime_lbl, False, False, 0)

        content_box.pack_start(header_box, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(sep, False, False, 2)

        # --- Action Buttons Grid ---
        actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # 1. Shutdown Button
        btn_shutdown = Gtk.Button()
        btn_shutdown.set_name("btn-power-shutdown")
        btn_shutdown.set_label("󰐥  Shutdown")
        btn_shutdown.connect("clicked", lambda b: self.execute_cmd(["systemctl", "poweroff"]))
        actions_box.pack_start(btn_shutdown, False, False, 0)

        # 2. Restart Button
        btn_restart = Gtk.Button()
        btn_restart.set_name("btn-power-restart")
        btn_restart.set_label("󰜉  Restart")
        btn_restart.connect("clicked", lambda b: self.execute_cmd(["systemctl", "reboot"]))
        actions_box.pack_start(btn_restart, False, False, 0)

        # 3. Log Out Button
        btn_logout = Gtk.Button()
        btn_logout.set_name("btn-power-logout")
        btn_logout.set_label("󰍃  Log Out")
        btn_logout.connect("clicked", lambda b: self.execute_cmd(["hyprctl", "dispatch", "exit"]))
        actions_box.pack_start(btn_logout, False, False, 0)

        # 4. Lock Screen Button
        btn_lock = Gtk.Button()
        btn_lock.set_name("btn-power-lock")
        btn_lock.set_label("󰌾  Lock Screen")
        btn_lock.connect("clicked", lambda b: self.execute_cmd(["/home/adi/.config/hypr/scripts/lock_screen.sh"]))
        actions_box.pack_start(btn_lock, False, False, 0)

        # 5. Suspend Button
        btn_suspend = Gtk.Button()
        btn_suspend.set_name("btn-power-suspend")
        btn_suspend.set_label("󰤄  Suspend")
        btn_suspend.connect("clicked", lambda b: self.execute_cmd(["systemctl", "suspend"]))
        actions_box.pack_start(btn_suspend, False, False, 0)

        content_box.pack_start(actions_box, True, True, 0)

        # Auto-close on mouse exit
        self.connect("leave-notify-event", self.on_mouse_leave)
        self.connect("destroy", lambda w: cleanup())

    def apply_css(self):
        css = b"""
        window {
            background-color: transparent;
        }
        #docket-root {
            background-color: rgba(10, 10, 26, 0.90);
            border: 1px solid rgba(235, 28, 82, 0.3);
            border-radius: 16px;
            color: #e0def4;
            font-family: 'JetBrainsMono Nerd Font', sans-serif;
        }
        button#btn-power-shutdown {
            background: rgba(235, 28, 82, 0.2);
            color: #eb1c52;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 13px;
            font-weight: bold;
            border: 1px solid rgba(235, 28, 82, 0.4);
            transition: all 0.2s ease;
        }
        button#btn-power-shutdown:hover {
            background: rgba(235, 28, 82, 0.5);
            color: #ffffff;
            border-color: rgba(235, 28, 82, 0.8);
        }
        button#btn-power-restart {
            background: rgba(246, 193, 119, 0.15);
            color: #f6c177;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 13px;
            font-weight: bold;
            border: 1px solid rgba(246, 193, 119, 0.35);
            transition: all 0.2s ease;
        }
        button#btn-power-restart:hover {
            background: rgba(246, 193, 119, 0.45);
            color: #ffffff;
            border-color: rgba(246, 193, 119, 0.8);
        }
        button#btn-power-logout {
            background: rgba(196, 167, 231, 0.15);
            color: #c4a7e7;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 13px;
            font-weight: bold;
            border: 1px solid rgba(196, 167, 231, 0.35);
            transition: all 0.2s ease;
        }
        button#btn-power-logout:hover {
            background: rgba(196, 167, 231, 0.45);
            color: #ffffff;
            border-color: rgba(196, 167, 231, 0.8);
        }
        button#btn-power-lock {
            background: rgba(156, 207, 216, 0.15);
            color: #9ccfd8;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 13px;
            font-weight: bold;
            border: 1px solid rgba(156, 207, 216, 0.35);
            transition: all 0.2s ease;
        }
        button#btn-power-lock:hover {
            background: rgba(156, 207, 216, 0.45);
            color: #ffffff;
            border-color: rgba(156, 207, 216, 0.8);
        }
        button#btn-power-suspend {
            background: rgba(255, 255, 255, 0.05);
            color: #e0def4;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 13px;
            font-weight: bold;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.2s ease;
        }
        button#btn-power-suspend:hover {
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
            border-color: rgba(255, 255, 255, 0.4);
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def get_uptime(self):
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        except Exception:
            return "Active"

    def execute_cmd(self, cmd_args):
        self.close()
        subprocess.Popen(cmd_args)

    def on_mouse_leave(self, widget, event):
        alloc = self.get_allocation()
        if not (0 <= event.x <= alloc.width and 0 <= event.y <= alloc.height):
            self.close()

if __name__ == "__main__":
    win = PowerDocket()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
