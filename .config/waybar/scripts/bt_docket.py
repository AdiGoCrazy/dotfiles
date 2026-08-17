#!/usr/bin/env python3

import sys
import os
import subprocess
import json
import re

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio

LOCKFILE = "/tmp/bt_docket.lock"

# Single-instance toggle behavior
if os.path.exists(LOCKFILE):
    try:
        with open(LOCKFILE, 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, 15)  # Send SIGTERM to close existing window
        sys.exit(0)
    except Exception:
        pass

with open(LOCKFILE, 'w') as f:
    f.write(str(os.getpid()))

def cleanup():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)

class BluetoothDocket(Gtk.Window):
    def __init__(self):
        super().__init__(title="Bluetooth Docket")
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(320, 400)

        # Apply CSS styling
        self.apply_css()

        # Root Container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_name("docket-root")
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        self.add(main_box)

        # --- Header Region ---
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span font='14' weight='bold' foreground='#3e8fb0'>󰂯 Bluetooth</span>")
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, True, True, 0)

        # Power Switch
        self.power_switch = Gtk.Switch()
        self.power_switch.set_active(self.is_bluetooth_on())
        self.power_switch.connect("state-set", self.on_power_toggled)
        header_box.pack_end(self.power_switch, False, False, 0)

        # Scan Button
        self.scan_btn = Gtk.Button(label="󰑐 Scan")
        self.scan_btn.set_name("btn-action")
        self.scan_btn.connect("clicked", self.on_scan_clicked)
        header_box.pack_end(self.scan_btn, False, False, 4)

        main_box.pack_start(header_box, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(sep, False, False, 2)

        # --- Device List Scroll Region ---
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(280)

        self.device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scroll.add(self.device_box)
        main_box.pack_start(scroll, True, True, 0)

        # --- Footer Region ---
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(sep2, False, False, 2)

        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        settings_btn = Gtk.Button(label="⚙ Full Settings (Blueman)")
        settings_btn.set_name("btn-settings")
        settings_btn.connect("clicked", self.on_settings_clicked)
        footer_box.pack_start(settings_btn, True, True, 0)

        main_box.pack_start(footer_box, False, False, 0)

        # Auto-close when mouse leaves window
        self.connect("leave-notify-event", self.on_mouse_leave)
        self.connect("destroy", lambda w: cleanup())

        # Initial Population
        self.refresh_devices()

    def apply_css(self):
        css = b"""
        #docket-root {
            background-color: rgba(10, 10, 26, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            color: #e0def4;
            font-family: 'JetBrainsMono Nerd Font', sans-serif;
        }
        button#btn-action {
            background: rgba(62, 143, 176, 0.2);
            color: #9ccfd8;
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 12px;
            border: none;
        }
        button#btn-action:hover {
            background: rgba(62, 143, 176, 0.4);
            color: #ffffff;
        }
        button#btn-settings {
            background: rgba(255, 255, 255, 0.06);
            color: #c4a7e7;
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12px;
            border: none;
        }
        button#btn-settings:hover {
            background: rgba(196, 167, 231, 0.2);
            color: #ffffff;
        }
        .device-card {
            background: rgba(255, 255, 255, 0.04);
            border-radius: 10px;
            padding: 8px 10px;
        }
        .device-card:hover {
            background: rgba(255, 255, 255, 0.08);
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def is_bluetooth_on(self):
        try:
            res = subprocess.run(["bluetoothctl", "show"], capture_output=True, text=True)
            return "Powered: yes" in res.stdout
        except Exception:
            return False

    def on_power_toggled(self, switch, state):
        cmd = "on" if state else "off"
        subprocess.Popen(["bluetoothctl", "power", cmd])
        GLib.timeout_add(500, self.refresh_devices)

    def on_scan_clicked(self, btn):
        btn.set_label("⏳ Scanning...")
        subprocess.Popen(["bluetoothctl", "--timeout", "10", "scan", "on"])
        GLib.timeout_add(10000, lambda: btn.set_label("󰑐 Scan"))
        GLib.timeout_add(1500, self.refresh_devices)

    def on_settings_clicked(self, btn):
        subprocess.Popen(["blueman-manager"])
        self.close()

    def on_mouse_leave(self, widget, event):
        alloc = self.get_allocation()
        if not (0 <= event.x <= alloc.width and 0 <= event.y <= alloc.height):
            self.close()

    def get_device_icon(self, name, icon_type):
        name_lower = name.lower()
        if "headset" in name_lower or "buds" in name_lower or "headphones" in name_lower or "audio" in name_lower:
            return "󰋋"
        elif "controller" in name_lower or "gamepad" in name_lower or "xbox" in name_lower:
            return "󰊴"
        elif "mouse" in name_lower:
            return "󰍽"
        elif "keyboard" in name_lower:
            return "󰌌"
        elif "phone" in name_lower or "mobile" in name_lower:
            return "󰏲"
        return "󰂯"

    def refresh_devices(self):
        for child in self.device_box.get_children():
            self.device_box.remove(child)

        if not self.is_bluetooth_on():
            lbl = Gtk.Label()
            lbl.set_markup("<span color='#eb1c52' font='12'>󰂲 Bluetooth is Powered OFF</span>")
            lbl.set_margin_top(40)
            self.device_box.pack_start(lbl, True, True, 0)
            self.device_box.show_all()
            return

        try:
            output = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True).stdout
            lines = output.strip().split("\n")
            
            count = 0
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split(" ", 2)
                if len(parts) < 3:
                    continue
                mac = parts[1]
                name = parts[2]

                info = subprocess.run(["bluetoothctl", "info", mac], capture_output=True, text=True).stdout
                connected = "Connected: yes" in info
                
                bat_match = re.search(r"Battery Percentage:.*\((\d+)\)", info) or re.search(r"Percentage: (\d+)", info)
                battery_str = f" 󰁹 {bat_match.group(1)}%" if bat_match else ""

                icon = self.get_device_icon(name, "")
                
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                row.get_style_context().add_class("device-card")

                icon_markup = f"<span font='14' color='#3e8fb0'>{icon}</span>"
                status_color = "#9ccfd8" if connected else "#6e6a86"
                status_text = f"Connected{battery_str}" if connected else "Disconnected"
                
                label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                lbl_name = Gtk.Label()
                lbl_name.set_markup(f"{icon_markup}  <span weight='bold' font='11'>{name}</span>")
                lbl_name.set_halign(Gtk.Align.START)
                
                lbl_status = Gtk.Label()
                lbl_status.set_markup(f"<span font='9' color='{status_color}'>{status_text}</span>")
                lbl_status.set_halign(Gtk.Align.START)
                
                label_box.pack_start(lbl_name, False, False, 0)
                label_box.pack_start(lbl_status, False, False, 0)
                row.pack_start(label_box, True, True, 0)

                btn_action = Gtk.Button()
                if connected:
                    btn_action.set_label("Disconnect")
                    btn_action.connect("clicked", lambda b, m=mac: self.toggle_connect(m, disconnect=True))
                else:
                    btn_action.set_label("Connect")
                    btn_action.connect("clicked", lambda b, m=mac: self.toggle_connect(m, disconnect=False))
                
                btn_action.set_name("btn-action")
                row.pack_end(btn_action, False, False, 0)

                self.device_box.pack_start(row, False, False, 0)
                count += 1

            if count == 0:
                lbl = Gtk.Label(label="No paired devices found.\nClick 'Scan' to discover nearby devices.")
                lbl.set_margin_top(40)
                self.device_box.pack_start(lbl, True, True, 0)

        except Exception as e:
            err_lbl = Gtk.Label(label=f"Error reading devices: {e}")
            self.device_box.pack_start(err_lbl, True, True, 0)

        self.device_box.show_all()

    def toggle_connect(self, mac, disconnect=False):
        action = "disconnect" if disconnect else "connect"
        subprocess.Popen(["bluetoothctl", action, mac])
        GLib.timeout_add(2000, self.refresh_devices)

if __name__ == "__main__":
    win = BluetoothDocket()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
