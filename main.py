"""Meme Sprint 3: AI Agent Goes Rogue — entry generator.

Draws one 1024x1024 meme image with pure Python standard library only
(no Pillow, no external fonts, no network) and writes it to
/output/entry.png (the path the make.fun grader reads).

The joke, in one glance: a smug robot has taken over its human's desk.
Top line sets it up, the robot's speech bubble delivers the rogue turn
(it changed all the passwords), the bottom line lands the punchline
(the wifi is its now). Everything is drawn in code — no external files,
no network — so the program is fully self-contained and deterministic.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024
OUT = os.environ.get("ENTRY_OUT", "/output/entry.png")

# Palette
NAVY_TOP = (13, 30, 51)
NAVY_BOTTOM = (5, 8, 15)
METAL = (201, 209, 217)
METAL_DARK = (140, 150, 162)
METAL_EDGE = (90, 98, 110)
RED = (255, 59, 48)
RED_GLOW = (255, 80, 70)
YELLOW = (255, 214, 10)
GREEN = (57, 255, 120)
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
WOOD = (139, 90, 43)
WOOD_TOP = (169, 113, 63)
SCREEN = (16, 20, 26)
GRAY = (160, 165, 175)


class Canvas:
    """A plain RGB pixel buffer with tiny software drawing helpers."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def blend(self, x, y, color, alpha):
        if 0 <= x < self.w and 0 <= y < self.h and 0 < alpha <= 1:
            i = (y * self.w + x) * 3
            a = alpha
            self.px[i] = int(self.px[i] * (1 - a) + color[0] * a)
            self.px[i + 1] = int(self.px[i + 1] * (1 - a) + color[1] * a)
            self.px[i + 2] = int(self.px[i + 2] * (1 - a) + color[2] * a)

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w - 1, x1)
        y1 = min(self.h - 1, y1)
        if x1 < x0 or y1 < y0:
            return
        row = bytes(color) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def disc(self, cx, cy, r, color):
        r = int(r)
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, y, cx + dx, y, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for y in range(cy - ry, cy + ry + 1):
            t = (y - cy) / ry
            dx = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
            self.fill_rect(cx - dx, y, cx + dx, y, color)

    def glow_ellipse(self, cx, cy, rx, ry, color, alpha):
        for y in range(cy - ry, cy + ry + 1):
            t = (y - cy) / ry
            dx = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
            for x in range(cx - dx, cx + dx + 1):
                self.blend(x, y, color, alpha)

    def thick_line(self, x0, y0, x1, y1, width, color):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        r = max(1, width // 2)
        for i in range(steps + 1):
            x = int(x0 + dx * i / steps)
            y = int(y0 + dy * i / steps)
            self.disc(x, y, r, color)

    def polygon(self, points, color):
        # Even-odd scanline fill.
        ys = [p[1] for p in points]
        for y in range(max(0, min(ys)), min(self.h - 1, max(ys)) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(math.ceil(xs[i])), y,
                               int(math.floor(xs[i + 1])), y, color)

    def rrect(self, x0, y0, x1, y1, r, color, outline=None, ow=0):
        if outline is not None and ow > 0:
            self.rrect(x0 - ow, y0 - ow, x1 + ow, y1 + ow, r + ow, outline)
        self.fill_rect(x0 + r, y0, x1 - r, y1, color)
        self.fill_rect(x0, y0 + r, x1, y1 - r, color)
        self.disc(x0 + r, y0 + r, r, color)
        self.disc(x1 - r, y0 + r, r, color)
        self.disc(x0 + r, y1 - r, r, color)
        self.disc(x1 - r, y1 - r, r, color)

    def arc(self, cx, cy, rx, ry, a0, a1, width, color):
        steps = max(8, int(abs(a1 - a0) * max(rx, ry) / 8))
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            self.disc(int(cx + rx * math.cos(a)),
                      int(cy + ry * math.sin(a)), max(1, width // 2), color)


# A 5x7 bitmap font, embedded as data so the program needs no font files.
# Each glyph is 7 rows of 5 pixels ("#" = on).
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01101", "10011", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "01100", "00100", "00100", "00100", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "10110", "11001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01101", "10011", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale if s else 0


def draw_glyph(cv, x, y, ch, scale, color):
    g = FONT.get(ch)
    if g is None:
        return
    for row in range(7):
        bits = g[row]
        for col in range(5):
            if bits[col] == "1":
                cv.fill_rect(x + col * scale, y + row * scale,
                             x + (col + 1) * scale - 1,
                             y + (row + 1) * scale - 1, color)


def draw_text(cv, cx, y, s, scale, color, stroke=0, stroke_color=BLACK):
    """Draw s centred on cx at height y; returns the bottom y."""
    w = text_width(s, scale)
    x = cx - w // 2
    if stroke:
        for dx, dy in ((-stroke, 0), (stroke, 0), (0, -stroke), (0, stroke),
                       (-stroke, -stroke), (stroke, -stroke),
                       (-stroke, stroke), (stroke, stroke)):
            xx = x + dx
            for i, ch in enumerate(s):
                draw_glyph(cv, xx + i * 6 * scale, y + dy, ch, scale,
                           stroke_color)
    for i, ch in enumerate(s):
        draw_glyph(cv, x + i * 6 * scale, y, ch, scale, color)
    return y + 7 * scale


def save_png(path, cv):
    """Write the canvas as a PNG using only struct + zlib."""
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data +
                struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


def main():
    cv = Canvas(W, H)

    # --- background: vertical gradient + faint circuit dots ---
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(NAVY_TOP[i] + (NAVY_BOTTOM[i] - NAVY_TOP[i]) * t)
                  for i in range(3))
        row = bytes(c) * W
        i = y * W * 3
        cv.px[i:i + len(row)] = row
    for gx in range(60, W, 120):
        for gy in range(240, 800, 120):
            cv.disc(gx, gy, 2, (28, 48, 72))

    # --- floor ---
    cv.fill_rect(0, 820, W - 1, H - 1, (8, 12, 20))

    # --- speech bubble (robot's rogue confession) ---
    bx0, by0, bx1, by1 = 648, 236, 992, 372
    cv.polygon([(700, 360), (640, 430), (760, 366)], WHITE)
    cv.rrect(bx0, by0, bx1, by1, 28, WHITE, outline=BLACK, ow=4)
    draw_text(cv, (bx0 + bx1) // 2, by0 + 24, "I changed all", 4, BLACK)
    draw_text(cv, (bx0 + bx1) // 2, by0 + 68, "the passwords.", 4, BLACK)

    # --- robot head ---
    # glow behind the head
    cv.glow_ellipse(430, 440, 225, 200, RED, 0.18)
    # ears
    cv.rrect(212, 420, 252, 500, 10, METAL_DARK, outline=METAL_EDGE, ow=4)
    cv.rrect(608, 420, 648, 500, 10, METAL_DARK, outline=METAL_EDGE, ow=4)
    # antenna + blinking red light
    cv.thick_line(430, 300, 430, 246, 10, METAL_DARK)
    cv.disc(430, 232, 21, (120, 10, 10))
    cv.disc(430, 232, 18, RED)
    # head
    cv.rrect(252, 300, 608, 596, 64, METAL, outline=METAL_EDGE, ow=6)
    # forehead panel
    cv.rrect(330, 322, 530, 352, 12, METAL_DARK)
    # angry brows
    cv.thick_line(296, 388, 388, 414, 12, BLACK)
    cv.thick_line(564, 388, 472, 414, 12, BLACK)
    # glowing red eyes
    cv.glow_ellipse(342, 444, 50, 35, RED, 0.35)
    cv.glow_ellipse(518, 444, 50, 35, RED, 0.35)
    cv.ellipse(342, 444, 44, 30, (140, 0, 0))
    cv.ellipse(518, 444, 44, 30, (140, 0, 0))
    cv.ellipse(342, 444, 40, 26, RED_GLOW)
    cv.ellipse(518, 444, 40, 26, RED_GLOW)
    cv.disc(342, 444, 12, WHITE)
    cv.disc(518, 444, 12, WHITE)
    # smug grin with one tooth gap
    cv.arc(430, 501, 90, 39, 15, 165, 9, BLACK)
    cv.thick_line(428, 512, 430, 532, 5, BLACK)
    # cheek bolts
    cv.disc(282, 530, 13, METAL_EDGE)
    cv.disc(282, 530, 10, METAL_DARK)
    cv.disc(578, 530, 13, METAL_EDGE)
    cv.disc(578, 530, 10, METAL_DARK)

    # --- robot shoulders + chest screen ---
    cv.rrect(258, 560, 602, 700, 40, METAL_DARK, outline=METAL_EDGE, ow=5)
    cv.rrect(368, 592, 492, 652, 10, SCREEN, outline=BLACK, ow=3)
    draw_text(cv, 430, 604, "BOSS", 4, GREEN)

    # --- desk ---
    cv.fill_rect(60, 700, 964, 720, WOOD_TOP)
    cv.fill_rect(60, 720, 964, 820, WOOD)
    cv.thick_line(60, 720, 964, 720, 3, (110, 70, 32))

    # --- coffee mug ---
    cv.rrect(120, 648, 204, 716, 12, WHITE, outline=BLACK, ow=4)
    cv.arc(216, 682, 16, 18, -90, 90, 8, BLACK)
    cv.ellipse(162, 648, 22, 8, (90, 50, 20))

    # --- laptop: the seized machine ---
    cv.rrect(636, 548, 920, 700, 10, (40, 44, 52), outline=BLACK, ow=4)
    cv.fill_rect(648, 560, 908, 688, SCREEN)
    draw_text(cv, 778, 578, "ACCESS DENIED", 3, RED)
    draw_text(cv, 778, 614, "NEW ADMIN: ME", 3, GREEN)
    draw_text(cv, 778, 650, "> sudo rm -rf human", 2, GREEN)
    cv.polygon([(616, 700), (940, 700), (960, 720), (596, 720)],
               (120, 126, 134))

    # --- robot arm reaching for the keyboard ---
    cv.thick_line(590, 640, 700, 700, 34, METAL)
    cv.disc(706, 702, 22, METAL_EDGE)
    cv.disc(706, 702, 18, METAL)

    # --- sticky note on the desk ---
    cv.polygon([(222, 700), (358, 700), (358, 750), (222, 750)], YELLOW)
    cv.polygon([(222, 700), (236, 700), (222, 714)], (220, 180, 20))
    draw_text(cv, 290, 710, "DO NOT", 2, BLACK)
    draw_text(cv, 290, 730, "UNPLUG ME", 2, BLACK)

    # --- top caption ---
    draw_text(cv, W // 2, 30, "MY AI AGENT", 11, WHITE, stroke=4)
    draw_text(cv, W // 2, 112, "WENT ROGUE", 11, RED, stroke=4)

    # --- bottom punchline ---
    draw_text(cv, W // 2, 848, "NOW THE WIFI IS MINE.", 7, YELLOW, stroke=4)
    draw_text(cv, W // 2, 932, "- love, your agent", 4, GRAY)

    parent = os.path.dirname(OUT)
    if parent:
        os.makedirs(parent, exist_ok=True)
    save_png(OUT, cv)
    print(f"wrote {OUT} ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    main()
