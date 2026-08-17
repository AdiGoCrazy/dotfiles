#!/usr/bin/env python3

import sys
import os
import time
import math
import datetime

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import cairo

ALL_LOCKS = ["/tmp/bt_docket.lock", "/tmp/wifi_docket.lock", "/tmp/audio_docket.lock", "/tmp/clock_docket.lock", "/tmp/power_docket.lock"]
CURRENT_LOCK = "/tmp/clock_docket.lock"

# Close any other open dockets for mutual exclusion
for lock in ALL_LOCKS:
    if lock != CURRENT_LOCK and os.path.exists(lock):
        try:
            with open(lock, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 15)
        except Exception:
            pass

# Single-instance toggle behavior for Clock Docket
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

class AnalogClock(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(170, 170)
        self.connect("draw", self.on_draw)

    def on_draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        radius = min(width, height) / 2.0 - 10

        center_x = width / 2.0
        center_y = height / 2.0

        now = datetime.datetime.now()
        hours = now.hour % 12
        minutes = now.minute
        seconds = now.second

        # Background Glass Circle
        cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
        cr.set_source_rgba(0.08, 0.08, 0.18, 0.85)
        cr.fill_preserve()
        cr.set_source_rgba(0.77, 0.65, 0.91, 0.5)  # Violet border
        cr.set_line_width(2.0)
        cr.stroke()

        # Minimalist Hour Tick Marks
        for i in range(12):
            angle = i * (math.pi / 6.0)
            x1 = center_x + (radius - 12) * math.sin(angle)
            y1 = center_y - (radius - 12) * math.cos(angle)
            x2 = center_x + (radius - 4) * math.sin(angle)
            y2 = center_y - (radius - 4) * math.cos(angle)

            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.set_source_rgba(0.88, 0.87, 0.96, 0.85)
            cr.set_line_width(3.0 if i % 3 == 0 else 1.5)
            cr.stroke()

        # Hour Hand (#c4a7e7 - Pastel Violet)
        hour_angle = (hours + minutes / 60.0) * (math.pi / 6.0)
        cr.move_to(center_x, center_y)
        cr.line_to(center_x + (radius * 0.48) * math.sin(hour_angle),
                   center_y - (radius * 0.48) * math.cos(hour_angle))
        cr.set_source_rgba(0.77, 0.65, 0.91, 1.0)
        cr.set_line_width(5.5)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.stroke()

        # Minute Hand (#9ccfd8 - Twilight Cyan)
        min_angle = (minutes + seconds / 60.0) * (math.pi / 30.0)
        cr.move_to(center_x, center_y)
        cr.line_to(center_x + (radius * 0.70) * math.sin(min_angle),
                   center_y - (radius * 0.70) * math.cos(min_angle))
        cr.set_source_rgba(0.61, 0.81, 0.85, 1.0)
        cr.set_line_width(4.0)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.stroke()

        # Second Hand (#f6c177 - Warm Coral)
        sec_angle = seconds * (math.pi / 30.0)
        cr.move_to(center_x, center_y)
        cr.line_to(center_x + (radius * 0.82) * math.sin(sec_angle),
                   center_y - (radius * 0.82) * math.cos(sec_angle))
        cr.set_source_rgba(0.96, 0.76, 0.47, 1.0)
        cr.set_line_width(2.0)
        cr.stroke()

        # Center Pin
        cr.arc(center_x, center_y, 5.0, 0, 2 * math.pi)
        cr.set_source_rgba(0.96, 0.76, 0.47, 1.0)
        cr.fill()

        return True

class ClockDocket(Gtk.Window):
    def __init__(self):
        super().__init__(title="Clock Docket")
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(520, 420)

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

        # --- Header Region: Big Digital Time & Subtitle ---
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        self.digital_lbl = Gtk.Label()
        self.digital_lbl.set_halign(Gtk.Align.START)
        header_box.pack_start(self.digital_lbl, False, False, 0)

        self.date_lbl = Gtk.Label()
        self.date_lbl.set_halign(Gtk.Align.START)
        header_box.pack_start(self.date_lbl, False, False, 0)

        content_box.pack_start(header_box, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(sep, False, False, 2)

        # --- Middle Region: Analog Clock (Left) + Calendar (Right) ---
        mid_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)

        # Analog Clock Left Box
        clock_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        clock_box.set_valign(Gtk.Align.CENTER)
        self.analog_clock = AnalogClock()
        clock_box.pack_start(self.analog_clock, True, True, 0)
        mid_box.pack_start(clock_box, False, False, 0)

        # GTK Calendar Right Box
        self.calendar = Gtk.Calendar()
        self.calendar.set_name("custom-calendar")
        mid_box.pack_start(self.calendar, True, True, 0)

        content_box.pack_start(mid_box, True, True, 0)

        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.pack_start(sep2, False, False, 2)

        # --- Footer Region: Today Jump Button ---
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        today_btn = Gtk.Button(label="󰃭 Jump to Today")
        today_btn.set_name("btn-settings")
        today_btn.connect("clicked", self.on_today_clicked)
        footer_box.pack_start(today_btn, True, True, 0)

        content_box.pack_start(footer_box, False, False, 0)

        # Auto-close on mouse exit
        self.connect("leave-notify-event", self.on_mouse_leave)
        self.connect("destroy", lambda w: cleanup())

        # Update Time Loop (1000ms)
        GLib.timeout_add(1000, self.update_time)
        self.update_time()

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
        button#btn-settings {
            background: rgba(255, 255, 255, 0.06);
            color: #c4a7e7;
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: bold;
            border: 1px solid rgba(196, 167, 231, 0.2);
            transition: all 0.2s ease;
        }
        button#btn-settings:hover {
            background: rgba(196, 167, 231, 0.25);
            color: #ffffff;
            border-color: rgba(196, 167, 231, 0.5);
        }
        calendar#custom-calendar {
            background-color: rgba(255, 255, 255, 0.03);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            color: #e0def4;
            padding: 10px;
            font-size: 14px;
        }
        calendar#custom-calendar:selected {
            background-color: rgba(196, 167, 231, 0.4);
            color: #ffffff;
            border-radius: 8px;
        }
        calendar#custom-calendar header,
        calendar#custom-calendar .header {
            color: #9ccfd8;
            font-size: 18px;
            font-weight: bold;
            padding-bottom: 6px;
        }
        calendar#custom-calendar header label,
        calendar#custom-calendar .header label {
            color: #9ccfd8;
            font-size: 18px;
            font-weight: bold;
        }
        calendar#custom-calendar button,
        calendar#custom-calendar header button,
        calendar#custom-calendar .header button {
            min-width: 44px;
            min-height: 44px;
            font-size: 22px;
            font-weight: bold;
            color: #c4a7e7;
            background: rgba(196, 167, 231, 0.25);
            border-radius: 12px;
            border: 1px solid rgba(196, 167, 231, 0.5);
            margin: 4px 6px;
            padding: 6px 14px;
        }
        calendar#custom-calendar button:hover,
        calendar#custom-calendar header button:hover {
            background: rgba(196, 167, 231, 0.55);
            color: #ffffff;
            border-color: rgba(196, 167, 231, 0.9);
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def update_time(self):
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%A, %B %d, %Y")

        self.digital_lbl.set_markup(f"<span font='18' weight='bold' foreground='#c4a7e7'>{time_str}</span>")
        self.date_lbl.set_markup(f"<span font='10' foreground='#9ccfd8'>{date_str}</span>")
        self.analog_clock.queue_draw()
        return True

    def on_today_clicked(self, btn):
        now = datetime.datetime.now()
        self.calendar.select_month(now.month - 1, now.year)
        self.calendar.select_day(now.day)

    def on_mouse_leave(self, widget, event):
        alloc = self.get_allocation()
        if not (0 <= event.x <= alloc.width and 0 <= event.y <= alloc.height):
            self.close()

if __name__ == "__main__":
    win = ClockDocket()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
