#!/usr/bin/env python3
"""news-image-20261126 -- one image summing up Thursday 26 November 2026.

Pure standard library. Draws a newspaper front page (masthead + lead story
+ six story panels + footer strip) and writes it as a deterministic PNG to
OUTPUT_DIR / MAKEFUN_OUTPUT_DIR / /output / entry.png.
No network, no third-party packages, no files read at runtime.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)
INK = (20, 24, 34)
NAVY = (18, 33, 61)
GOLD = (212, 175, 55)
RED = (178, 34, 34)
WHITE = (255, 255, 255)
GREY = (90, 90, 90)
LIGHT = (232, 226, 210)
SKY = (135, 206, 235)
SKY_D = (70, 130, 180)
ORANGE = (232, 120, 30)
FLAME = (255, 176, 32)
GREEN = (46, 125, 50)
PANEL = (255, 255, 255)

# ------------------------------------------------- 5x7 bitmap font (A-Z 0-9 punct)
# Each glyph: 7 rows, each row a 5-bit integer (bit 4 = leftmost pixel).
FONT = {
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ' ': (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    '.': (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ',': (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    '-': (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    ':': (0x00, 0x0C, 0x00, 0x00, 0x0C, 0x00, 0x00),
    ';': (0x00, 0x0C, 0x00, 0x0C, 0x04, 0x08, 0x00),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '/': (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    '%': (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '+': (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    '=': (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    '*': (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
}

BLANK = (0, 0, 0, 0, 0, 0, 0)


def glyph(ch):
    return FONT.get(ch, FONT.get(ch.upper(), BLANK))


def text_width(s, scale):
    return len(s) * 6 * scale - scale


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def border(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, c)
                elif abs(d2 - r * r) <= r:
                    self.set(xx, yy, c)

    def tri(self, x0, y0, x1, y1, x2, y2, c):
        # filled triangle via scanline
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        def edge(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)
        for y in range(ay, cy + 1):
            if y < by:
                xa, xb = edge(ax, ay, bx, by, y), edge(ax, ay, cx, cy, y)
            else:
                xa, xb = edge(bx, by, cx, cy, y), edge(ax, ay, cx, cy, y)
            if xa > xb:
                xa, xb = xb, xa
            for x in range(int(xa), int(xb) + 1):
                self.set(x, y, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = glyph(ch)
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_c(self, cx, y, s, scale, c):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, c)

    def wrap(self, x, y, s, scale, max_w, c, lh=None):
        """Word-wrap text; returns y after last line."""
        lh = lh or (9 * scale)
        words = s.upper().split()
        line, yy = "", y
        for wd in words:
            trial = (line + " " + wd).strip()
            if text_width(trial, scale) <= max_w or not line:
                line = trial
            else:
                self.text(x, yy, line, scale, c)
                yy += lh
                line = wd
        if line:
            self.text(x, yy, line, scale, c)
            yy += lh
        return yy


# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------- icon scenes
def draw_flame(cv, x, y, s):
    """Stylised flame, base at (x, y), height ~ s."""
    cv.tri(x, y, x - s // 2, y - s // 2, x + s // 2, y - s // 2, ORANGE)
    cv.tri(x, y - s // 4, x - s // 3, y - s, x + s // 3, y - s, FLAME)
    cv.tri(x, y - s // 2, x - s // 5, y - s * 5 // 4, x + s // 5, y - s * 5 // 4,
           (255, 220, 90))


def draw_refinery(cv, x, y, w, h):
    """Oil refinery with towers, pipes and flames. Box (x,y,w,h)."""
    cv.rect(x, y, w, h, (38, 48, 66))
    cv.rect(x, y + h - 26, w, 26, (28, 36, 50))
    # towers
    for i, (tx, tw, th) in enumerate([(18, 26, 78), (58, 20, 96), (96, 30, 66)]):
        cv.rect(x + tx, y + h - 26 - th, tw, th, (120, 130, 150))
        cv.rect(x + tx - 3, y + h - 26 - th - 8, tw + 6, 8, (150, 160, 180))
    # storage tank
    cv.circle(x + w - 52, y + h - 52, 26, (160, 165, 175))
    cv.rect(x + w - 78, y + h - 52, 52, 26, (160, 165, 175))
    # pipes
    cv.rect(x + 44, y + h - 60, 60, 6, (200, 200, 200))
    # flames on towers
    draw_flame(cv, x + 31, y + h - 26 - 78 - 8, 22)
    draw_flame(cv, x + 68, y + h - 26 - 96 - 8, 26)
    draw_flame(cv, x + 111, y + h - 26 - 66 - 8, 18)
    # smoke
    cv.circle(x + 31, y + 22, 10, (180, 180, 180))
    cv.circle(x + 68, y + 12, 12, (200, 200, 200))
    cv.circle(x + 105, y + 26, 9, (170, 170, 170))
    # price tag
    cv.rect(x + w - 150, y + 12, 136, 30, GOLD)
    cv.text(x + w - 142, y + 19, "BRENT $94+", 2, NAVY)


def draw_globe(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cx, cy, r = x + w // 2, y + h // 2 + 6, 62
    cv.circle(cx, cy, r, SKY_D)
    cv.circle(cx, cy, r - 6, (46, 125, 50))
    # meridians
    for k in range(-2, 3):
        cv.line(cx + k * 22, cy - r + 8, cx + k * 22, cy + r - 8, (255, 255, 255))
    cv.line(cx - r + 8, cy, cx + r - 8, cy, (255, 255, 255))
    cv.circle(cx, cy, r, WHITE, fill=False)
    # tariff tag
    cv.rect(x + w - 96, y + 10, 84, 30, RED)
    cv.text(x + w - 88, y + 17, "15%?", 2, WHITE)


def draw_rocket(cv, x, y, w, h):
    cv.rect(x, y, w, h, (12, 18, 38))
    # stars
    for sx, sy in [(20, 18), (60, 40), (150, 14), (190, 46), (30, 80),
                   (170, 84), (110, 24), (205, 70)]:
        cv.rect(x + sx, y + sy, 4, 4, WHITE)
    cx = x + w // 2
    # body
    cv.tri(cx, y + 10, cx - 24, y + 64, cx + 24, y + 64, WHITE)
    cv.rect(cx - 24, y + 64, 48, 26, (220, 225, 235))
    cv.tri(cx - 24, y + 90, cx - 42, y + 104, cx - 24, y + 76, RED)
    cv.tri(cx + 24, y + 90, cx + 42, y + 104, cx + 24, y + 76, RED)
    cv.circle(cx, y + 46, 10, SKY_D)
    cv.circle(cx, y + 46, 6, SKY)
    # flag stripe
    cv.rect(cx - 24, y + 76, 48, 7, RED)
    # flame below the engine
    draw_flame(cv, cx, y + h - 4, 16)
    # station ring
    cv.line(x + 8, y + h - 18, x + 52, y + h - 18, GOLD)
    cv.circle(x + 30, y + h - 18, 6, GOLD)


def draw_tanker(cv, x, y, w, h):
    cv.rect(x, y, w, h, (70, 30, 26))
    # road
    cv.rect(x, y + h - 30, w, 30, (50, 50, 50))
    cv.rect(x + 10, y + h - 18, 26, 4, (255, 220, 90))
    cv.rect(x + 90, y + h - 18, 26, 4, (255, 220, 90))
    cv.rect(x + 170, y + h - 18, 26, 4, (255, 220, 90))
    # tank
    cv.circle(x + 96, y + 78, 34, (200, 200, 200))
    cv.rect(x + 62, y + 44, 68, 68, (200, 200, 200))
    cv.rect(x + 62, y + 44, 68, 10, (150, 150, 150))
    # cab
    cv.rect(x + 140, y + 66, 46, 46, RED)
    cv.rect(x + 148, y + 72, 20, 18, SKY)
    # wheels
    cv.circle(x + 84, y + h - 30, 13, INK)
    cv.circle(x + 84, y + h - 30, 6, GREY)
    cv.circle(x + 160, y + h - 30, 13, INK)
    cv.circle(x + 160, y + h - 30, 6, GREY)
    # fire
    draw_flame(cv, x + 96, y + 46, 30)
    draw_flame(cv, x + 130, y + 52, 22)


def draw_drone(cv, x, y, w, h):
    cv.rect(x, y, w, h, (222, 214, 196))
    cx, cy = x + w // 2, y + h // 2
    # ground
    cv.rect(x, y + h - 34, w, 34, (120, 110, 88))
    cv.rect(x + 14, y + h - 52, 34, 18, (90, 84, 66))
    cv.rect(x + 60, y + h - 44, 26, 10, (90, 84, 66))
    cv.rect(x + 150, y + h - 48, 40, 14, (90, 84, 66))
    # sky band
    cv.rect(x, y, w, 26, (200, 210, 220))
    # drone body
    cv.rect(cx - 34, cy - 12, 68, 24, INK)
    cv.circle(cx, cy, 10, RED)
    cv.line(cx - 34, cy - 12, cx - 58, cy - 34, INK)
    cv.line(cx + 34, cy - 12, cx + 58, cy - 34, INK)
    cv.line(cx - 34, cy + 12, cx - 58, cy + 34, INK)
    cv.line(cx + 34, cy + 12, cx + 58, cy + 34, INK)
    for rx, ry in [(cx - 58, cy - 34), (cx + 58, cy - 34),
                   (cx - 58, cy + 34), (cx + 58, cy + 34)]:
        cv.circle(rx, ry, 12, GREY, fill=False)
        cv.line(rx - 14, ry, rx + 14, ry, GREY)
    # blast
    draw_flame(cv, cx + 74, cy + 40, 20)


def draw_shield(cv, x, y, w, h):
    cv.rect(x, y, w, h, (24, 60, 100))
    cx, cy = x + w // 2, y + h // 2 + 4
    # shield
    cv.tri(cx, cy - 52, cx - 46, cy - 34, cx + 46, cy - 34, GOLD)
    cv.rect(cx - 46, cy - 34, 92, 40, GOLD)
    cv.tri(cx, cy + 46, cx - 46, cy + 6, cx + 46, cy + 6, GOLD)
    cv.tri(cx, cy - 42, cx - 34, cy - 28, cx + 34, cy - 28, WHITE)
    cv.rect(cx - 34, cy - 28, 68, 30, WHITE)
    cv.tri(cx, cy + 34, cx - 34, cy + 2, cx + 34, cy + 2, WHITE)
    # check mark (thick)
    for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2)]:
        cv.line(cx - 20 + dx, cy - 2 + dy, cx - 6 + dx, cy + 14 + dy, GREEN)
        cv.line(cx - 6 + dx, cy + 14 + dy, cx + 22 + dx, cy - 18 + dy, GREEN)
    # "20" tag
    cv.rect(x + 10, y + 10, 58, 28, WHITE)
    cv.text(x + 16, y + 16, "20", 2, NAVY)


def draw_parade(cv, x, y, w, h):
    cv.rect(x, y, w, h, (200, 214, 228))
    # storm cloud
    cv.circle(x + 60, y + 26, 22, (90, 96, 110))
    cv.circle(x + 88, y + 20, 26, (110, 116, 130))
    cv.circle(x + 118, y + 28, 20, (90, 96, 110))
    cv.rect(x + 44, y + 30, 92, 14, (90, 96, 110))
    # rain
    for rx in (52, 76, 100, 124):
        cv.line(x + rx, y + 48, x + rx - 6, y + 62, SKY_D)
    # balloon
    bx, by = x + w - 70, y + 46
    cv.circle(bx, by, 30, RED)
    cv.tri(bx, by + 26, bx - 14, by + 44, bx + 14, by + 44, RED)
    cv.circle(bx - 10, by - 8, 8, (255, 120, 120))
    cv.line(bx, by + 44, bx - 8, y + h - 20, INK)
    cv.line(bx, by + 44, bx + 10, y + h - 20, INK)
    # street
    cv.rect(x, y + h - 26, w, 26, (60, 60, 60))
    cv.rect(x + 16, y + h - 16, 30, 4, (255, 220, 90))
    cv.rect(x + 96, y + h - 16, 30, 4, (255, 220, 90))
    # "100 YRS" tag
    cv.rect(x + 10, y + h - 62, 108, 28, NAVY)
    cv.text(x + 16, y + h - 56, "100 YRS", 2, WHITE)


# ------------------------------------------------------------------ layout
def panel(cv, x, y, w, h, tag, headline, body, draw_icon):
    cv.rect(x, y, w, h, PANEL)
    cv.border(x, y, w, h, INK, 2)
    draw_icon(cv, x + 2, y + 2, w - 4, 118)
    cv.rect(x, y + 122, w, 4, GOLD)
    yy = y + 134
    cv.text(x + 12, yy, tag, 1, RED)
    yy += 16
    yy = cv.wrap(x + 12, yy, headline, 2, w - 24, NAVY, lh=20)
    cv.wrap(x + 12, yy + 2, body, 1, w - 24, INK, lh=11)


def build():
    cv = Canvas(W, H, PAPER)
    # ---- masthead
    cv.rect(0, 0, W, 118, NAVY)
    cv.rect(0, 114, W, 4, GOLD)
    cv.text_c(W // 2, 14, "THE WORLD IN ONE DAY", 5, WHITE)
    cv.text_c(W // 2, 62, "THURSDAY, 26 NOVEMBER 2026", 2, GOLD)
    cv.text_c(W // 2, 88, "THE DAY'S NEWS FROM AROUND THE WORLD", 1, (200, 205, 215))

    # ---- lead story
    lx, ly, lw, lh = 24, 132, 976, 252
    cv.rect(lx, ly, lw, lh, PANEL)
    cv.border(lx, ly, lw, lh, INK, 2)
    cv.rect(lx, ly, 10, lh, RED)
    draw_refinery(cv, lx + 14, ly + 14, 300, lh - 28)
    tx = lx + 330
    cv.text(tx, ly + 20, "LEAD STORY  -  MIDDLE EAST", 1, RED)
    yy = cv.wrap(tx, ly + 46, "HOUTHIS CLAIM STRIKE ON SAUDI REFINERY", 3,
                 lw - 346, NAVY, lh=30)
    yy = cv.wrap(tx, yy + 6, "Brent crude tops $94 as attacks are claimed on Ras Tanura, the kingdom's biggest refinery, and on Riyadh.", 2,
                 lw - 346, INK, lh=20)
    cv.wrap(tx, yy + 4, "Oil jumps on fears of Gulf supply disruption; markets fall on tariff worries.", 1,
            lw - 346, GREY, lh=11)

    # ---- six panels, 3 x 2
    pw, ph, gap = 312, 268, 20
    gy0, gy1 = 404, 692
    panels = [
        (24, gy0, "TRADE - USA", "US PLANS NEW TARIFFS",
         "China, the EU, Japan and Brazil face higher duties over subsidised production.",
         draw_globe),
        (356, gy0, "SPACE - CHINA", "PAKISTAN'S FIRST ASTRONAUT",
         "Flies to China's Tiangong space station aboard Shenzhou-24.",
         draw_rocket),
        (688, gy0, "EGYPT", "CAIRO TANKER FIRE KILLS 30",
         "A fuel tanker bursts into flames on the highway ring road around Cairo.",
         draw_tanker),
        (24, gy1, "SUDAN", "DRONE STRIKES KILL 19",
         "Civilians dead in attacks on Blue Nile state, reports say.",
         draw_drone),
        (356, gy1, "COLOMBIA", "20 HOSTAGES FREED",
         "Police storm a supermarket after a 17-hour siege; all are rescued.",
         draw_shield),
        (688, gy1, "USA - THANKSGIVING", "STORM HALTS PARADE",
         "Macy's Thanksgiving parade postponed for the first time in 100 years.",
         draw_parade),
    ]
    for (px, py, tag, head, body, icon) in panels:
        panel(cv, px, py, pw, ph, tag, head, body, icon)

    # ---- footer strip
    fy = 976
    cv.rect(0, fy, W, 48, NAVY)
    cv.rect(0, fy, W, 4, GOLD)
    cv.text_c(W // 2, fy + 16,
              "ALSO: HUAWEI GUILTY IN TRADE-SECRETS CASE - GUKESH DRAWS IN CHESS FINAL",
              1, WHITE)
    return cv


def main():
    out = (os.environ.get("OUTPUT_DIR")
           or os.environ.get("MAKEFUN_OUTPUT_DIR")
           or "/output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "entry.png")
    size = write_png(build(), path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
