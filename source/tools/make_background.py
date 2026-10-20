#!/usr/bin/env python3
"""Draws the launcher's background (assets/launcher/background.png): an
air hockey table seen from above, in the port's own style.  Our own
picture, made by this script (no photo, nothing from the game).

    python tools/make_background.py
"""
import math
import os
import struct
import zlib

W, H = 1600, 960
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'launcher',
                   'background.png')

# the table: centre, half size, corner radius (pixels)
TX, TY, THW, THH, TR = 1010, 480, 520, 300, 120
RAIL = 34


def smooth(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def rounded_box(px, py, hw, hh, r):
    """signed distance to a rounded rectangle centred at 0"""
    qx, qy = abs(px) - hw + r, abs(py) - hh + r
    outside = math.hypot(max(qx, 0), max(qy, 0))
    return outside + min(max(qx, qy), 0) - r


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def pixel(x, y):
    # the room: dark blue, lighter towards the table
    d_light = math.hypot((x - TX) / 900, (y - TY) / 700)
    c = mix((26, 46, 92), (6, 10, 26), smooth(0.0, 1.1, d_light))
    px, py = x - TX, y - TY
    # shadow under the table
    sd = rounded_box(px - 14, py - 22, THW + RAIL, THH + RAIL, TR + RAIL)
    c = mix(c, (0, 0, 0), 0.55 * (1 - smooth(-10, 60, sd)))
    # the rail
    rail = rounded_box(px, py, THW + RAIL, THH + RAIL, TR + RAIL)
    if rail < 1.5:
        shade = 0.5 + 0.5 * (-py / (THH + RAIL))
        rail_colour = mix((150, 18, 32), (235, 60, 70), max(0.0, min(1.0, shade)))
        c = mix(c, rail_colour, 1 - smooth(-1.5, 1.5, rail))
    # the playing surface
    surf = rounded_box(px, py, THW, THH, TR)
    if surf < 1.5:
        s = mix((228, 238, 250), (180, 205, 235), smooth(0, 1, math.hypot(px / THW, py / THH) * 0.8))
        # air holes
        if (int(x - TX + 4000) % 26 < 3) and (int(y - TY + 4000) % 26 < 3):
            s = mix(s, (140, 160, 190), 0.6)
        # markings: centre line (red), blue lines, centre circle, goal creases
        line = 1 - smooth(3, 5, abs(px))
        s = mix(s, (210, 40, 50), line)
        for bx in (-THW * 0.42, THW * 0.42):
            s = mix(s, (40, 90, 200), 1 - smooth(4, 6, abs(px - bx)))
        ring = abs(math.hypot(px, py) - 95)
        s = mix(s, (210, 40, 50), 1 - smooth(2.5, 4.5, ring))
        for gx in (-THW, THW):
            crease = abs(math.hypot(px - gx, py) - 120)
            if abs(px) < THW:
                s = mix(s, (40, 90, 200), 1 - smooth(2.5, 4.5, crease))
        # the goals: dark slots in the rail ends
        c = mix(c, s, 1 - smooth(-1.5, 1.5, surf))
    for gx in (-(THW + RAIL / 2), THW + RAIL / 2):
        g = rounded_box(px - gx, py, RAIL / 2 + 2, 70, 10)
        c = mix(c, (10, 12, 20), 1 - smooth(-1.5, 1.5, g))
    # puck and mallets, with a glow
    for (ox, oy, r, col, glow) in ((150, -60, 26, (20, 20, 24), (255, 230, 60)),
                                   (-300, 90, 42, (230, 40, 50), (255, 80, 90)),
                                   (330, 40, 42, (40, 110, 230), (90, 160, 255))):
        d = math.hypot(px - ox, py - oy)
        c = mix(c, glow, 0.35 * math.exp(-max(0.0, d - r) / 18))
        c = mix(c, (0, 0, 0), 0.35 * (1 - smooth(r - 4, r + 10, math.hypot(px - ox - 6, py - oy - 9))))
        body = mix(col, (255, 255, 255), 0.35 * smooth(r, 0, math.hypot(px - ox + r * 0.3, py - oy + r * 0.3)))
        if r > 30:
            body = mix(body, mix(col, (0, 0, 0), 0.35), 1 - smooth(r * 0.42, r * 0.48, d))
            body = mix(body, mix(col, (255, 255, 255), 0.25), 1 - smooth(r * 0.30, r * 0.36, d))
        c = mix(c, body, 1 - smooth(r - 1.2, r + 1.2, d))
    # puck trail
    for k in range(1, 7):
        d = math.hypot(px - (150 - k * 34), py - (-60 + k * 13))
        c = mix(c, (255, 220, 80), 0.12 * (1 - k / 7) * (1 - smooth(10, 26, d)))
    # left side darker for the menu
    c = mix(c, (4, 6, 16), 0.65 * (1 - smooth(0, 700, x)))
    return c


def main():
    rows = []
    for y in range(H):
        row = bytearray([0])
        for x in range(W):
            r, g, b = pixel(x + 0.5, y + 0.5)
            row += bytes((int(max(0, min(255, r))), int(max(0, min(255, g))), int(max(0, min(255, b)))))
        rows.append(bytes(row))
    raw = b''.join(rows)

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'wb').write(png)
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
