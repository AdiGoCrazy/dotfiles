#!/usr/bin/env python3

import sys
import os
import subprocess
import re

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio

LOCKFILE = "/tmp/audio_docket.lock"

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

class AudioDocket(Gtk.Window):
    def __init__(self):
        super().__init__(title="Audio Docket")
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(360, 460)

        # Enable RGBA visual transparency for rounded corners
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
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span font='13' weight='bold' foreground='#c4a7e7'>󰕾  Audio Controls</span>")
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, True, True, 0)

        # Mute Toggle Button
        self.mute_btn = Gtk.Button(label="󰕾 Mute")
        self.mute_btn.set_name("btn-action")
        self.mute_btn.connect("clicked", self.on_mute_clicked)
        header_box.pack_end(self.mute_btn, False, False, 0)

        content_box.pack_start(header_box, False, False, 0)

        # Master Volume Slider
        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vol_icon = Gtk.Label()
        vol_icon.set_markup("<span font='14' color='#c4a7e7'>󰓃</span>")
        vol_box.pack_start(vol_icon, False, False, 0)

        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_value(self.get_master_volume())
        self.vol_scale.connect("value-changed", self.on_volume_changed)
        vol_box.pack_start(self.vol_scale, True, True, 0)

        self.vol_pct_lbl = Gtk.Label(label=f"{int(self.vol_scale.get_value())}%")
        self.vol_pct_lbl.set_name("vol-pct")
        vol_box.pack_end(self.vol_pct_lbl, False, False, 0)

        content_box.pack_start(vol_box, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(sep, False, False, 2)

        # Section Label: Output Devices
        out_lbl = Gtk.Label()
        out_lbl.set_markup("<span font='10' weight='bold' foreground='#9ccfd8'>PLAYBACK OUTPUT DEVICES</span>")
        out_lbl.set_halign(Gtk.Align.START)
        content_box.pack_start(out_lbl, False, False, 0)

        # --- Device List Scroll Region ---
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(240)

        self.sinks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scroll.add(self.sinks_box)
        content_box.pack_start(scroll, True, True, 0)

        # --- Footer Region ---
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(sep2, False, False, 2)

        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mixer_btn = Gtk.Button(label="⚙ Full Audio Mixer (Pavucontrol)")
        mixer_btn.set_name("btn-settings")
        mixer_btn.connect("clicked", self.on_mixer_clicked)
        footer_box.pack_start(mixer_btn, True, True, 0)

        content_box.pack_start(footer_box, False, False, 0)

        # Auto-close on mouse exit
        self.connect("leave-notify-event", self.on_mouse_leave)
        self.connect("destroy", lambda w: cleanup())

        # Initial Population
        self.refresh_sinks()

    def apply_css(self):
        css = b"""
        window {
            background-color: transparent;
        }
        #docket-root {
            background-color: rgba(10, 10, 26, 0.90);
            border: 1px solid rgba(196, 167, 231, 0.25);
            border-radius: 16px;
            color: #e0def4;
            font-family: 'JetBrainsMono Nerd Font', sans-serif;
        }
        button#btn-action {
            background: rgba(196, 167, 231, 0.2);
            color: #c4a7e7;
            border-radius: 10px;
            padding: 5px 12px;
            font-size: 12px;
            border: 1px solid rgba(196, 167, 231, 0.3);
            transition: all 0.2s ease;
        }
        button#btn-action:hover {
            background: rgba(196, 167, 231, 0.4);
            color: #ffffff;
            border-color: rgba(196, 167, 231, 0.6);
        }
        button#btn-settings {
            background: rgba(255, 255, 255, 0.06);
            color: #9ccfd8;
            border-radius: 10px;
            padding: 7px 14px;
            font-size: 12px;
            border: 1px solid rgba(156, 207, 216, 0.2);
            transition: all 0.2s ease;
        }
        button#btn-settings:hover {
            background: rgba(156, 207, 216, 0.25);
            color: #ffffff;
            border-color: rgba(156, 207, 216, 0.5);
        }
        .sink-card {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 10px 12px;
            transition: all 0.2s ease;
        }
        .sink-card:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(196, 167, 231, 0.3);
        }
        .sink-card-active {
            background: rgba(196, 167, 231, 0.12);
            border: 1px solid rgba(196, 167, 231, 0.4);
            border-radius: 12px;
            padding: 10px 12px;
        }
        #vol-pct {
            color: #c4a7e7;
            font-weight: bold;
            font-size: 13px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def get_master_volume(self):
        try:
            res = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True)
            match = re.search(r"/ (\d+)%", res.stdout)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return 50

    def on_volume_changed(self, scale):
        val = int(scale.get_value())
        self.vol_pct_lbl.set_text(f"{val}%")
        subprocess.Popen(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"])

    def on_mute_clicked(self, btn):
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
        res = subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"], capture_output=True, text=True)
        if "yes" in res.stdout.lower():
            btn.set_label("󰝟 Muted")
        else:
            btn.set_label("󰕾 Mute")

    def on_mixer_clicked(self, btn):
        subprocess.Popen(["pavucontrol"])
        self.close()

    def on_mouse_leave(self, widget, event):
        alloc = self.get_allocation()
        if not (0 <= event.x <= alloc.width and 0 <= event.y <= alloc.height):
            self.close()

    def get_sink_icon(self, name, desc):
        desc_lower = (name + " " + desc).lower()
        if "headset" in desc_lower or "buds" in desc_lower or "headphones" in desc_lower or "bluez" in desc_lower:
            return "󰋋"
        elif "hdmi" in desc_lower or "displayport" in desc_lower:
            return "󰍹"
        return "󰓃"

    def refresh_sinks(self):
        for child in self.sinks_box.get_children():
            self.sinks_box.remove(child)

        try:
            default_sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True).stdout.strip()
            
            output = subprocess.run(["pactl", "list", "sinks"], capture_output=True, text=True).stdout
            
            sink_blocks = output.split("Sink #")
            count = 0

            for block in sink_blocks:
                if not block.strip():
                    continue
                
                name_match = re.search(r"Name: (\S+)", block)
                desc_match = re.search(r"Description: (.+)", block)
                vol_match = re.search(r"Volume:.* / (\d+)%", block)

                if not name_match:
                    continue

                sink_name = name_match.group(1)
                sink_desc = desc_match.group(1).strip() if desc_match else sink_name
                sink_vol = vol_match.group(1) if vol_match else "--"

                is_default = (sink_name == default_sink)
                icon = self.get_sink_icon(sink_name, sink_desc)

                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                if is_default:
                    row.get_style_context().add_class("sink-card-active")
                else:
                    row.get_style_context().add_class("sink-card")

                icon_markup = f"<span font='14' color='#c4a7e7'>{icon}</span>"
                status_color = "#9ccfd8" if is_default else "#6e6a86"
                status_text = f"Active Output • {sink_vol}%" if is_default else f"Volume: {sink_vol}%"

                label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                lbl_name = Gtk.Label()
                lbl_name.set_markup(f"{icon_markup}  <span weight='bold' font='11'>{sink_desc}</span>")
                lbl_name.set_halign(Gtk.Align.START)

                lbl_status = Gtk.Label()
                lbl_status.set_markup(f"<span font='9' color='{status_color}'>{status_text}</span>")
                lbl_status.set_halign(Gtk.Align.START)

                label_box.pack_start(lbl_name, False, False, 0)
                label_box.pack_start(lbl_status, False, False, 0)
                row.pack_start(label_box, True, True, 0)

                btn_action = Gtk.Button()
                if is_default:
                    btn_action.set_label("Active")
                    btn_action.set_sensitive(False)
                else:
                    btn_action.set_label("Select")
                    btn_action.connect("clicked", lambda b, s=sink_name: self.set_default_sink(s))

                btn_action.set_name("btn-action")
                row.pack_end(btn_action, False, False, 0)

                self.sinks_box.pack_start(row, False, False, 0)
                count += 1

            if count == 0:
                lbl = Gtk.Label(label="No audio output devices detected.")
                lbl.set_margin_top(40)
                self.sinks_box.pack_start(lbl, True, True, 0)

        except Exception as e:
            err_lbl = Gtk.Label(label=f"Error reading audio sinks: {e}")
            self.sinks_box.pack_start(err_lbl, True, True, 0)

        self.sinks_box.show_all()

    def set_default_sink(self, sink_name):
        subprocess.run(["pactl", "set-default-sink", sink_name])
        GLib.timeout_add(300, self.refresh_sinks)

if __name__ == "__main__":
    win = AudioDocket()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
