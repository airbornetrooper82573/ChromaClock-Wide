"""ChromaClock Wide: native-width clock for ChuckBuilds LEDMatrix."""
from datetime import datetime
from zoneinfo import ZoneInfo
import colorsys
import math
import time
from PIL import Image, ImageDraw, ImageFont
from src.plugin_system.base_plugin import BasePlugin

STYLES = ("neon", "prism", "starfield", "matrix", "fire", "horizon", "binary", "minimal", "pulse", "wave", "aurora", "rain")
PALETTES = {"cyan": ((35, 230, 255), (18, 70, 180)),
            "magenta": ((255, 65, 180), (115, 35, 205)),
            "amber": ((255, 185, 45), (170, 65, 25)),
            "green": ((76, 255, 135), (15, 125, 95))}

def scale(c, amount):
    return tuple(max(0, min(255, int(v * amount))) for v in c)

def blend(a, b, amount):
    return tuple(int(x * (1 - amount) + y * amount) for x, y in zip(a, b))

def rainbow(hue):
    return tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue % 1, .85, 1))

def get_font(size, bold=True):
    paths = (["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else
             ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"])
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

class ChromaClockWidePlugin(BasePlugin):
    def __init__(self, plugin_id, config, display_manager, cache_manager, plugin_manager):
        super().__init__(plugin_id, config, display_manager, cache_manager, plugin_manager)
        self._load(config)
        self.current_style = "neon"
        self._last_update = 0

    def _load(self, config):
        self.style = config.get("style", "cycle")
        self.preview_mode = bool(config.get("preview_mode", False))
        self.preview_style = config.get("preview_style", "neon")
        self.cycle_seconds = max(5, int(config.get("cycle_seconds", 20)))
        self.palette = config.get("palette", "rainbow")
        self.use_24h = bool(config.get("use_24h", False))
        self.show_date = bool(config.get("show_date", True))
        self.show_seconds = bool(config.get("show_seconds", True))
        self.glow = bool(config.get("glow", True))
        self.timezone = config.get("timezone", "America/New_York")
        self.brightness = max(.15, min(1.0, float(config.get("brightness", .85))))

    def on_config_change(self, new_config):
        super().on_config_change(new_config)
        self._load(self.config)

    def update(self):
        self._last_update = time.time()

    def _now(self):
        try:
            return datetime.now(ZoneInfo(self.timezone))
        except Exception:
            return datetime.now()

    def _decor(self, draw, w, h, style, tick, accent, secondary):
        for x in range(w):
            # Reserve central space for clear clock text.
            if abs(x - w / 2) < min(70, w * .25):
                continue
            wave = math.sin(x * .08 + tick)
            if style == "neon":
                draw.point((x, 1), fill=scale(blend(accent, secondary, (wave + 1) / 2), .65))
                draw.point((x, h - 2), fill=scale(accent, .5))
            elif style == "prism":
                color = rainbow(x / max(w, 1) + tick * .025)
                draw.line((x, 0, x, 2), fill=scale(color, .7))
                draw.line((x, h - 3, x, h - 1), fill=scale(color, .7))
            elif style == "starfield":
                if x % 5 == 0:
                    y = (x * 23 + 7) % h
                    draw.point((x, y), fill=scale(accent, .5 + .5 * math.sin(tick * 1.4 + x)))
            elif style == "matrix":
                if x % 7 == 0:
                    y = int((tick * (4 + x % 5) + x * 17) % (h + 12)) - 6
                    draw.line((x, max(0, y), x, min(h - 1, y + 4)), fill=(25, 180, 65))
            elif style == "fire":
                height = max(1, int(5 + 9 * (.5 + .5 * wave)))
                draw.line((x, h - height, x, h - 1), fill=scale(blend((255, 50, 0), (255, 200, 25), x / max(w, 1)), .65))
            elif style == "horizon":
                y = int(h * .75 + 4 * wave)
                draw.line((x, y, x, h - 1), fill=scale(secondary, .42))
            elif style == "binary":
                if x % 8 == 0:
                    for y in range(3, h - 2, 7):
                        if (x * 17 + y * 13 + int(tick * 2)) % 5 < 2:
                            draw.rectangle((x, y, x + 2, y + 2), fill=scale(accent, .55))
            elif style == "minimal":
                if x % 12 == 0:
                    draw.point((x, h - 2), fill=scale(accent, .5))
            elif style == "pulse":
                y = int(h / 2 + 9 * math.sin(x * .10 + tick * 3))
                draw.line((x, h // 2, x, y), fill=scale(accent, .6))
            elif style == "wave":
                for layer in range(3):
                    y = int(h / 2 + (layer + 1) * 3 * math.sin(x * .09 + tick * 2 + layer))
                    draw.point((x, y), fill=scale(blend(accent, secondary, layer / 3), .85))
            elif style == "aurora":
                y = int(h * .35 + 8 * math.sin(x * .04 + tick * .8))
                for layer in range(4):
                    if 0 <= y + layer * 2 < h:
                        draw.point((x, y + layer * 2), fill=scale(blend((40, 250, 175), secondary, layer / 4), .6))
            elif style == "rain":
                if x % 7 == 0:
                    y = int((tick * 12 + x * 17) % (h + 12)) - 6
                    draw.line((x, max(0, y), x, min(h - 1, y + 5)), fill=scale(accent, .65))

    def display(self, force_clear=False):
        try:
            w, h = int(self.display_manager.width), int(self.display_manager.height)
            if w < 32 or h < 16:
                return
            tick = time.time()
            now = self._now()
            style = (self.preview_style if self.preview_mode else
                     STYLES[int(tick // self.cycle_seconds) % len(STYLES)]
                     if self.style == "cycle" else self.style)
            self.current_style = style if style in STYLES else "neon"
            if self.palette == "rainbow":
                a, b = rainbow(tick / 75), rainbow(tick / 75 + .3)
            else:
                a, b = PALETTES.get(self.palette, PALETTES["cyan"])
            a, b = scale(a, self.brightness), scale(b, self.brightness)
            if self.current_style == "fire":
                a, b = (255, 195, 45), (255, 75, 15)
            if self.current_style == "matrix":
                a, b = (65, 255, 135), (15, 95, 60)
            img = Image.new("RGB", (w, h))
            draw = ImageDraw.Draw(img)
            self._decor(draw, w, h, self.current_style, tick, a, b)
            text = now.strftime("%H:%M" if self.use_24h else "%I:%M")
            if not self.use_24h:
                text = text.lstrip("0") or "12:00"
            max_height = h - (12 if self.show_date else 6)
            max_width = min(int(w * .50), 205)
            size = max_height + 8
            while size > 7:
                face = get_font(size)
                bounds = draw.textbbox((0, 0), text, font=face)
                if bounds[2] - bounds[0] <= max_width and bounds[3] - bounds[1] <= max_height:
                    break
                size -= 1
            x = int((w - (bounds[2] - bounds[0])) / 2 - bounds[0])
            y = int(2 - bounds[1])
            if self.glow:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    draw.text((x + dx, y + dy), text, font=face, fill=scale(b, .30))
            draw.text((x, y), text, font=face, fill=a)
            if self.show_seconds:
                secface = get_font(max(8, min(11, h // 3)))
                sx = min(w - 16, x + bounds[2] - bounds[0] + 6)
                draw.text((sx, 4), now.strftime("%S"), font=secface, fill=b)
                end = int((w - 1) * (now.second + now.microsecond / 1e6) / 60)
                draw.line((0, h - 1, end, h - 1), fill=a)
            if self.show_date:
                date = now.strftime("%a %b %d").upper()
                dateface = get_font(max(7, min(10, h // 4)))
                box = draw.textbbox((0, 0), date, font=dateface)
                draw.text(((w - (box[2] - box[0])) // 2 - box[0],
                           h - 8 - box[1]), date, font=dateface,
                          fill=scale((220, 220, 240), self.brightness))
            self.display_manager.image = img
            self.display_manager.update_display()
        except Exception:
            self.logger.exception("ChromaClock Wide render failed")

    def get_info(self):
        result = super().get_info()
        result["current_style"] = self.current_style
        result["preview_mode"] = self.preview_mode
        return result
