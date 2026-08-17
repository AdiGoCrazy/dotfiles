#!/usr/bin/env python3

import sys
import os
import subprocess
import re

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio

ALL_LOCKS = ["/tmp/bt_docket.lock", "/tmp/wifi_docket.lock", "/tmp/audio_docket.lock", "/tmp/clock_docket.lock", "/tmp/power_docket.lock"]
CURRENT_LOCK = "/tmp/wifi_docket.lock"

# Close any other open dockets for mutual exclusion
for lock in ALL_LOCKS:
    if lock != CURRENT_LOCK and os.path.exists(lock):
        try:
            with open(lock, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 15)
        except Exception:
            pass

# Single-instance toggle behavior for Wi-Fi Docket
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

class PasswordDialog(Gtk.Dialog):
    def __init__(self, parent, ssid):
        super().__init__(title=f"Connect to {ssid}", transient_for=parent, flags=0)
        self.set_default_size(300, 140)
        self.set_modal(True)

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(14)
        box.set_margin_bottom(14)
        box.set_margin_start(14)
        box.set_margin_end(14)

        lbl = Gtk.Label(label=f"Enter Wi-Fi Password for '{ssid}':")
        lbl.set_halign(Gtk.Align.START)
        box.pack_start(lbl, False, False, 0)

        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)
        self.entry.set_activates_default(True)
        box.pack_start(self.entry, False, False, 0)

        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        btn_connect = self.add_button("Connect", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        self.show_all()

    def get_password(self):
        return self.entry.get_text()

class WifiDocket(Gtk.Window):
    def __init__(self):
        super().__init__(title="Wi-Fi Docket")
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(360, 440)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)

        self.apply_css()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_name("docket-root")
        main_box.set_margin_top(4)
        main_box.set_margin_bottom(4)
        main_box.set_margin_start(4)
        main_box.set_margin_end(4)
        self.add(main_box)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_margin_top(14)
        content_box.set_margin_bottom(14)
        content_box.set_margin_start(14)
        content_box.set_margin_end(14)
        main_box.pack_start(content_box, True, True, 0)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span font='13' weight='bold' foreground='#9ccfd8'>󰤨  Wi-Fi Networks</span>")
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, True, True, 0)

        self.power_switch = Gtk.Switch()
        self.power_switch.set_active(self.is_wifi_on())
        self.power_switch.connect("state-set", self.on_power_toggled)
        header_box.pack_end(self.power_switch, False, False, 0)

        self.scan_btn = Gtk.Button(label="󰑐 Rescan")
        self.scan_btn.set_name("btn-action")
        self.scan_btn.connect("clicked", self.on_scan_clicked)
        header_box.pack_end(self.scan_btn, False, False, 6)

        content_box.pack_start(header_box, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(sep, False, False, 2)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(300)

        self.network_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scroll.add(self.network_box)
        content_box.pack_start(scroll, True, True, 0)

        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(sep2, False, False, 2)

        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        settings_btn = Gtk.Button(label="⚙ Full Settings (iwgtk)")
        settings_btn.set_name("btn-settings")
        settings_btn.connect("clicked", self.on_settings_clicked)
        footer_box.pack_start(settings_btn, True, True, 0)

        content_box.pack_start(footer_box, False, False, 0)

        self.connect("leave-notify-event", self.on_mouse_leave)
        self.connect("destroy", lambda w: cleanup())

        self.refresh_networks()

    def apply_css(self):
        css = b"""
        window {
            background-color: transparent;
        }
        #docket-root {
            background-color: rgba(10, 10, 26, 0.90);
            border: 1px solid rgba(156, 207, 216, 0.25);
            border-radius: 16px;
            color: #e0def4;
            font-family: 'JetBrainsMono Nerd Font', sans-serif;
        }
        button#btn-action {
            background: rgba(156, 207, 216, 0.2);
            color: #9ccfd8;
            border-radius: 10px;
            padding: 5px 12px;
            font-size: 12px;
            border: 1px solid rgba(156, 207, 216, 0.3);
            transition: all 0.2s ease;
        }
        button#btn-action:hover {
            background: rgba(156, 207, 216, 0.4);
            color: #ffffff;
            border-color: rgba(156, 207, 216, 0.6);
        }
        button#btn-settings {
            background: rgba(255, 255, 255, 0.06);
            color: #c4a7e7;
            border-radius: 10px;
            padding: 7px 14px;
            font-size: 12px;
            border: 1px solid rgba(196, 167, 231, 0.2);
            transition: all 0.2s ease;
        }
        button#btn-settings:hover {
            background: rgba(196, 167, 231, 0.25);
            color: #ffffff;
            border-color: rgba(196, 167, 231, 0.5);
        }
        .network-card {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 10px 12px;
            transition: all 0.2s ease;
        }
        .network-card:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(156, 207, 216, 0.25);
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def is_wifi_on(self):
        try:
            res = subprocess.run(["nmcli", "radio", "wifi"], capture_output=True, text=True)
            return "enabled" in res.stdout.lower()
        except Exception:
            return False

    def on_power_toggled(self, switch, state):
        cmd = "on" if state else "off"
        subprocess.Popen(["nmcli", "radio", "wifi", cmd])
        GLib.timeout_add(1000, self.refresh_networks)

    def on_scan_clicked(self, btn):
        btn.set_label("⏳ Rescanning...")
        subprocess.Popen(["nmcli", "device", "wifi", "rescan"])
        GLib.timeout_add(4000, lambda: btn.set_label("󰑐 Rescan"))
        GLib.timeout_add(1500, self.refresh_networks)

    def on_settings_clicked(self, btn):
        if os.path.exists("/usr/bin/iwgtk"):
            subprocess.Popen(["iwgtk"])
        else:
            subprocess.Popen(["nm-connection-editor"])
        self.close()

    def on_mouse_leave(self, widget, event):
        alloc = self.get_allocation()
        if not (0 <= event.x <= alloc.width and 0 <= event.y <= alloc.height):
            self.close()

    def get_signal_icon(self, signal_pct):
        try:
            val = int(signal_pct)
            if val >= 80:
                return "󰤨"
            elif val >= 55:
                return "󰤥"
            elif val >= 30:
                return "󰤢"
            return "󰤟"
        except Exception:
            return "󰤨"

    def refresh_networks(self):
        for child in self.network_box.get_children():
            self.network_box.remove(child)

        if not self.is_wifi_on():
            lbl = Gtk.Label()
            lbl.set_markup("<span color='#eb1c52' font='12'>󰖪 Wi-Fi Radio is OFF</span>")
            lbl.set_margin_top(40)
            self.network_box.pack_start(lbl, True, True, 0)
            self.network_box.show_all()
            return

        try:
            cmd = ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list"]
            output = subprocess.run(cmd, capture_output=True, text=True).stdout
            lines = output.strip().split("\n")

            seen_ssids = set()
            count = 0

            for line in lines:
                if not line.strip():
                    continue
                parts = line.split(":")
                if len(parts) < 4:
                    continue
                
                in_use = parts[0].strip() == "*"
                ssid = parts[1].strip()
                signal = parts[2].strip()
                security = parts[3].strip()

                if not ssid or ssid in seen_ssids:
                    continue
                seen_ssids.add(ssid)

                icon = self.get_signal_icon(signal)
                sec_icon = "🔒" if security and security != "--" else "🔓"

                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                row.get_style_context().add_class("network-card")

                status_color = "#9ccfd8" if in_use else "#6e6a86"
                status_text = f"Connected • Signal: {signal}% {sec_icon}" if in_use else f"Signal: {signal}% • {sec_icon} {security}"

                label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                lbl_name = Gtk.Label()
                lbl_name.set_markup(f"<span font='14' color='#9ccfd8'>{icon}</span>  <span weight='bold' font='11'>{ssid}</span>")
                lbl_name.set_halign(Gtk.Align.START)

                lbl_status = Gtk.Label()
                lbl_status.set_markup(f"<span font='9' color='{status_color}'>{status_text}</span>")
                lbl_status.set_halign(Gtk.Align.START)

                label_box.pack_start(lbl_name, False, False, 0)
                label_box.pack_start(lbl_status, False, False, 0)
                row.pack_start(label_box, True, True, 0)

                btn_action = Gtk.Button()
                if in_use:
                    btn_action.set_label("Disconnect")
                    btn_action.connect("clicked", lambda b, s=ssid: self.disconnect_wifi(s))
                else:
                    btn_action.set_label("Connect")
                    btn_action.connect("clicked", lambda b, s=ssid, sec=security: self.connect_wifi(s, sec))

                btn_action.set_name("btn-action")
                row.pack_end(btn_action, False, False, 0)

                self.network_box.pack_start(row, False, False, 0)
                count += 1

            if count == 0:
                lbl = Gtk.Label(label="No Wi-Fi networks found.\nClick 'Rescan' to search.")
                lbl.set_margin_top(40)
                self.network_box.pack_start(lbl, True, True, 0)

        except Exception as e:
            err_lbl = Gtk.Label(label=f"Error reading Wi-Fi networks: {e}")
            self.network_box.pack_start(err_lbl, True, True, 0)

        self.network_box.show_all()

    def disconnect_wifi(self, ssid):
        subprocess.Popen(["nmcli", "device", "disconnect", "wlan0"])
        GLib.timeout_add(1500, self.refresh_networks)

    def connect_wifi(self, ssid, security):
        if security and security != "--":
            dialog = PasswordDialog(self, ssid)
            res = dialog.run()
            password = dialog.get_password()
            dialog.destroy()

            if res == Gtk.ResponseType.OK and password:
                subprocess.Popen(["nmcli", "device", "wifi", "connect", ssid, "password", password])
                GLib.timeout_add(3000, self.refresh_networks)
        else:
            subprocess.Popen(["nmcli", "device", "wifi", "connect", ssid])
            GLib.timeout_add(3000, self.refresh_networks)

if __name__ == "__main__":
    win = WifiDocket()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
