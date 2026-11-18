"""Old-style IBM boot screens with small, BIOS-era palettes.

Each design is drawn at 4x, reduced to the target size, then snapped to a
limited palette: the design's own few colours plus 7 blend shades between
each pair of them. That is how period 256-colour boot logos kept serif
text and diagonals smooth. The PCjr screen is the exception: it is drawn
pixel-exact in the 16 CGA colours.

usage: python -I tools/ibm_screens.py tools/screen_assets OUT_DIR [design ...]
Needs Pillow, NumPy and (for the ThinkPad (R) and INTERNAL USE ONLY (R)) the
Windows fonts timesbd.ttf and arial.ttf.
ASSETS_DIR holds:
  ibm_8bar_mask.png          8-bar IBM, white on black, no (R), high resolution
  plex_letters_mask.png      1956 Rand IBM wordmark, white on black (1200x788 frame)
  plex_fill_mask.png         filled quarter of the B, same frame
  thinkpad_letters_mask.png  serif ThinkPad wordmark (1997), letters only
  thinkpad_dot_mask.png      its i-dot
  lenovo2003_mask.png        2003 italic lenovo
  lenovo2015.png             2015 Lenovo (red box, white text), RGBA
"""
import os, sys
from itertools import combinations
import numpy as np
from PIL import Image, ImageDraw

SS = 4                                           # supersampling before reduction
SIZES = [(640, 480), (640, 360), (672, 378), (1280, 960), (1920, 1080)]
STEPS = 8                                        # 7 blend shades per colour pair


# --------------------------------------------------------------------------- helpers
def ramp(palette):
    """Base colours plus STEPS-1 blends between every pair (max 256).
    Pairs with the background (palette[0]) come first, so if the 256 limit
    cuts anything it is a blend between two foreground colours."""
    out = list(dict.fromkeys(palette))
    pairs = sorted(combinations(palette, 2), key=lambda p: palette[0] not in p)
    for a, b in pairs:
        for k in range(1, STEPS):
            c = tuple(round(a[i] + (b[i] - a[i]) * k / STEPS) for i in range(3))
            if c not in out: out.append(c)
    return out[:256]


def snap(im, palette):
    """Map to the palette, nearest colour, no dithering."""
    pal = Image.new("P", (1, 1))
    flat = [v for c in palette for v in c]
    pal.putpalette(flat + flat[:3] * (256 - len(palette)))
    return im.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE)


def fit_layer(layer, W, H, frac_w, frac_h=None):
    lay = layer.crop(layer.getbbox())
    k = min(frac_w * W / lay.width, (frac_h or frac_w) * H / lay.height)
    lay = lay.resize((max(1, round(lay.width * k)), max(1, round(lay.height * k))), Image.LANCZOS)
    return lay, ((W - lay.width) // 2, (H - lay.height) // 2)


def tinted(mask, col):
    im = Image.new("RGBA", mask.size, col + (255,)); im.putalpha(mask); return im


# --------------------------------------------------------------------------- designs
class Diagonal:
    """8-bar IBM at 40 degrees, after Paul Rand's IBM packaging, 1973-84."""
    def __init__(s, bg, fg): s.bg, s.fg, s.palette = bg, fg, [bg, fg]
    def draw(s, A, W, H):
        frac = 0.62 if W / H > 1.5 else 0.62 * 1.15
        lw = int(frac * W)
        m = A["8bar"].resize((lw, round(A["8bar"].height * lw / A["8bar"].width)), Image.LANCZOS)
        m = m.rotate(40, resample=Image.BICUBIC, expand=True)
        im = Image.new("RGBA", (W, H), s.bg + (255,))
        im.alpha_composite(tinted(m, s.fg), ((W - m.width) // 2, (H - m.height) // 2))
        return im


class Dominoes:
    """Five tipping colour blocks and a small black 8-bar IBM, on white."""
    BG = (0xF7, 0xF6, 0xF2)
    BLOCKS = [(52, 155, 12, (0x0B, 0x0B, 0x0B)), (100, 155, 22, (0x12, 0x95, 0x5A)),
              (155, 152, 33, (0xFF, 0xC4, 0x1A)), (215, 158, 48, (0xE2, 0x20, 0x2F)),
              (280, 162, 62, (0x0E, 0x6C, 0xB8))]
    IBM = (382, 172, 22, 95)                      # centre x, y, clockwise tilt, width
    palette = [BG] + [b[3] for b in BLOCKS]
    def draw(s, A, W, H):
        U = 8
        lay = Image.new("RGBA", (480 * U, 300 * U), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for cx, cy, tilt, col in s.BLOCKS:
            t = np.radians(tilt); c, si = np.cos(t), np.sin(t)
            pts = [(-19, -47.5), (19, -47.5), (19, 47.5), (-19, 47.5)]
            d.polygon([((cx + x * c - y * si) * U, (cy + x * si + y * c) * U) for x, y in pts], fill=col)
        cx, cy, tilt, iw = s.IBM
        m = A["8bar"].resize((iw * U, round(A["8bar"].height * iw * U / A["8bar"].width)), Image.LANCZOS)
        m = m.rotate(-tilt, resample=Image.BICUBIC, expand=True)
        lay.alpha_composite(tinted(m, s.BLOCKS[0][3]), (cx * U - m.width // 2, cy * U - m.height // 2))
        im = Image.new("RGBA", (W, H), s.BG + (255,))
        lay, pos = fit_layer(lay, W, H, 0.80)
        im.alpha_composite(lay, pos)
        return im


class Annual1991:
    """8-bar IBM with each bar its own colour, after the 1991 Annual Report cover."""
    BARS = [(0xE4, 0x4A, 0x2C), (0x45, 0x48, 0xA8), (0xA6, 0x6E, 0x2E), (0x3A, 0x95, 0x3C)]
    def __init__(s, bg): s.bg, s.palette = bg, [bg] + s.BARS
    def draw(s, A, W, H):
        mask = A["8bar"]; a = np.asarray(mask) > 127
        rows = np.flatnonzero(np.diff(np.r_[0, a.any(1).astype(int), 0]))
        bands = list(zip(rows[::2], rows[1::2])); assert len(bands) == 8
        rgb = np.zeros(a.shape + (3,), np.uint8)
        for k, (y0, y1) in enumerate(bands): rgb[y0:y1] = s.BARS[k % 4]
        logo = Image.fromarray(rgb).convert("RGBA"); logo.putalpha(mask)
        im = Image.new("RGBA", (W, H), s.bg + (255,))
        lay, pos = fit_layer(logo, W, H, 0.62)
        im.alpha_composite(lay, pos)
        return im


class Plex:
    """1956 Rand IBM wordmark with construction marks (after the IBM Plex launch art),
    recoloured in the IBM blue of Rand's 1972 8-bar logo. With striped=True the
    filled quarter of the B is cut into 8-bar stripes (same bar:pitch ratio,
    scaled to the letter height, aligned to the baseline)."""
    BG, FG, MARK = (0, 0, 0), (0xFF, 0xFF, 0xFF), (0x1F, 0x70, 0xC1)
    palette = [BG, FG, MARK]
    FRAME = (1200, 788); BOX = (78, 186, 1102, 645)   # content incl. circles
    CAP = (211, 586)                                  # letter top / baseline in frame
    def __init__(s, striped=True): s.striped = striped
    def stripes(s, sz, k):
        """Mask (frame scaled by k) that is 255 on 8-bar bars, 0 in the gaps."""
        pitch = (s.CAP[1] - s.CAP[0]) / 401.15 * 53.3   # 8-bar SVG: pitch 53.3, bar 27.93
        bar = pitch * 27.93 / 53.3
        y = np.arange(sz[1]) / k
        on = ((s.CAP[1] - y) % pitch) < bar
        return Image.fromarray(np.repeat((on * 255).astype(np.uint8)[:, None], sz[0], 1))
    def draw(s, A, W, H):
        k = min(0.86 * W / (s.BOX[2] - s.BOX[0]), 0.72 * H / (s.BOX[3] - s.BOX[1]))
        ox = (W - (s.BOX[2] - s.BOX[0]) * k) / 2 - s.BOX[0] * k
        oy = (H - (s.BOX[3] - s.BOX[1]) * k) / 2 - s.BOX[1] * k
        sz = (round(s.FRAME[0] * k), round(s.FRAME[1] * k))
        im = Image.new("RGBA", (W, H), s.BG + (255,))
        im.alpha_composite(tinted(A["plex"].resize(sz, Image.LANCZOS), s.FG), (round(ox), round(oy)))
        fill = A["plexfill"].resize(sz, Image.LANCZOS)
        if s.striped:                                   # gaps cut through to the background
            im.alpha_composite(tinted(fill, s.BG), (round(ox), round(oy)))
            fill = Image.fromarray((np.asarray(fill, np.uint16) * np.asarray(s.stripes(sz, k)) // 255).astype(np.uint8))
        im.alpha_composite(tinted(fill, s.MARK), (round(ox), round(oy)))
        d = ImageDraw.Draw(im)
        P = lambda x, y: (ox + x * k, oy + y * k)
        lw = max(1, round(3.2 * k))
        for cx, cy, r in [(135.2, 550.9, 53.15), (880.7, 588.2, 53.15)]:
            d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], outline=s.MARK, width=lw)
        cx, cy, r = 535.8, 308.5, 118.45
        d.arc([P(cx - r, cy - r), P(cx + r, cy + r)], -82.5, 82.5, fill=s.MARK, width=lw)
        d.rectangle([P(566.5, 275), P(566.5 + 3.2, 382)], fill=s.MARK)
        return im


class PCjr:
    """IBM PCjr power-on screen, CGA 320x200 (logo panel + colour bar)."""
    CGA = [(0x00,0x00,0x00),(0x00,0x00,0xAA),(0x00,0xAA,0x00),(0x00,0xAA,0xAA),
           (0xAA,0x00,0x00),(0xAA,0x00,0xAA),(0xAA,0x55,0x00),(0xAA,0xAA,0xAA),
           (0x55,0x55,0x55),(0x55,0x55,0xFF),(0x55,0xFF,0x55),(0x55,0xFF,0xFF),
           (0xFF,0x55,0x55),(0xFF,0x55,0xFF),(0xFF,0xFF,0x55),(0xFF,0xFF,0xFF)]
    palette = CGA
    T, M = [(2, 9)], [(4, 7)]
    ROWS = [T + [(10,19)] + [(22,26),(35,39)], T + [(10,20)] + [(22,27),(34,39)],
            T + [(10,21)] + [(22,28),(33,39)], M + [(12,15),(18,21)] + [(24,29),(32,37)],
            M + [(12,15),(18,21)] + [(24,30),(31,37)], M + [(12,20)] + [(24,37)],
            M + [(12,19)] + [(24,37)], M + [(12,20)] + [(24,37)],
            M + [(12,15),(18,21)] + [(24,37)], M + [(12,15),(18,21)] + [(24,27),(28,33),(34,37)],
            T + [(10,21)] + [(22,27),(29,32),(34,39)], T + [(10,20)] + [(22,27),(30,31),(34,39)],
            T + [(10,19)] + [(22,27),(34,39)]]
    def rects(s):
        yield (0, 0, 320, 136, 1)
        for k, spans in enumerate(s.ROWS):
            for c0, c1 in spans: yield (c0 * 8, 20 + 8 * k, c1 * 8, 24 + 8 * k, 15)
        for i in range(15): yield (16 + 16 * i, 160, 32 + 16 * i, 198, i + 1)
    def draw(s, A, W, H):
        # 320x200 on a 4:3 tube; pillarbox inside wider frames
        h = H; w = round(H * 4 / 3); ox = (W - w) // 2
        im = Image.new("RGBA", (W, H), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
        for x0, y0, x1, y1, c in s.rects():
            d.rectangle([ox + x0 * w / 320, y0 * h / 200, ox + x1 * w / 320 - 1, y1 * h / 200 - 1], fill=s.CGA[c])
        return im


class ThinkPadBoot:
    """Late-90s ThinkPad POST screen: serif ThinkPad(R) lower left, maker logo top right."""
    RED_DOT = (0xD4, 0x00, 0x00)
    FONT = "C:/Windows/Fonts/timesbd.ttf"
    def __init__(s, bg, text, corner, corner_col=None, red_dot=False):
        s.bg, s.text, s.corner, s.corner_col, s.red_dot = bg, text, corner, corner_col, red_dot
        s.palette = [bg, text] + ([corner_col] if corner_col else []) + ([s.RED_DOT] if red_dot else [])
        if corner == "lenovo2015": s.palette += [(0xE4, 0x20, 0x22), (0xFF, 0xFF, 0xFF)]
    def draw(s, A, W, H):
        from PIL import ImageFont
        im = Image.new("RGBA", (W, H), s.bg + (255,))
        # ThinkPad wordmark: measured from a ThinkPad 600-era boot screen
        tw = round(0.387 * H); k = tw / A["tp"].width; th = round(A["tp"].height * k)
        x0, y0 = round(0.183 * H), round(0.93 * H) - th
        im.alpha_composite(tinted(A["tp"].resize((tw, th), Image.LANCZOS), s.text), (x0, y0))
        im.alpha_composite(tinted(A["tpdot"].resize((tw, th), Image.LANCZOS),
                                  s.RED_DOT if s.red_dot else s.text), (x0, y0))
        f = ImageFont.truetype(s.FONT, max(8, round(0.45 * th)))
        ImageDraw.Draw(im).text((x0 + tw + round(0.006 * H), y0), "\u00ae", font=f, fill=s.text, anchor="lt")
        # maker logo, top right
        right, top = W - round(0.107 * H), round(0.10 * H)
        if s.corner == "ibm":
            src, cw = A["8bar"], 0.173
        elif s.corner == "lenovo2003":
            src, cw = A["len03"], 0.22
        else:
            src, cw = A["len15"], 0.20
        cw = round(cw * H); ch = round(src.height * cw / src.width)
        logo = src.resize((cw, ch), Image.LANCZOS)
        logo = tinted(logo, s.corner_col) if logo.mode == "L" else logo
        im.alpha_composite(logo, (right - cw, top))
        return im


class RandBee:
    """After Paul Rand's Tokyo/Osaka Communication Arts poster: six tumbling
    squares around the striped bee, with halftone wings. Text and signature left out.
    Geometry is measured from the 500x701 poster."""
    BG = (0xE7, 0xED, 0xED)
    INK = (0x0B, 0x0B, 0x0B)
    SQUARES = [  # centre x, y, rotation, side, colour (draw order = overlap order)
        (158.0, 199.1, 32.00, 141.8, (0x34, 0x83, 0x2A)),
        (301.6, 134.2, 72.75, 147.3, (0xFC, 0xB7, 0x08)),
        (237.3, 427.0, 81.75, 126.4, (0x85, 0x17, 0x66)),
        (115.8, 378.9, 63.00, 142.0, (0xE0, 0x0A, 0x18)),
        (260.7, 563.4, 24.00, 143.2, (0x16, 0x4D, 0x24)),
        (396.2, 412.5, 16.00, 135.2, (0x02, 0x2A, 0x6F)),
    ]
    BARS = [(308.8, 238.6), (301.8, 263.2), (295.2, 286.7), (288.5, 310.1)]   # 60 x 12.5 at 15.5 deg
    DOTS = [(270.3, 326.3), (296.3, 333.3)]                                   # diameter 18.7
    WINGS = [(244.7, 273.9, 62.5), (348.1, 292.7, -18.5)]                     # 58 x 36, long-axis angle
    palette = [BG, INK] + [s[4] for s in SQUARES]

    @staticmethod
    def quad(cx, cy, w, h, deg, U):
        t = np.radians(deg); c, s = np.cos(t), np.sin(t)
        return [((cx + x * c - y * s) * U, (cy + x * s + y * c) * U)
                for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]]

    def draw(s, A, W, H):
        U = 8
        lay = Image.new("RGBA", (500 * U, 701 * U), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for cx, cy, rot, side, col in s.SQUARES:
            d.polygon(s.quad(cx, cy, side, side, rot, U), fill=col)
        for cx, cy in s.BARS:
            d.polygon(s.quad(cx, cy, 60, 12.5, 15.5, U), fill=s.INK)
        r = 18.7 / 2
        for cx, cy in s.DOTS:
            d.ellipse([(cx - r) * U, (cy - r) * U, (cx + r) * U, (cy + r) * U], fill=s.INK)
        pitch, dot = 2.2, 0.31                       # halftone screen, poster px
        for cx, cy, ang in s.WINGS:                  # wings sit on top of the third bar
            d.polygon(s.quad(cx, cy, 58, 36, ang, U), fill=s.BG)
            t = np.radians(ang + 45); c, si = np.cos(t), np.sin(t)
            tw = np.radians(ang); cw, sw = np.cos(tw), np.sin(tw)
            n = int(40 / pitch)
            for i in range(-n, n + 1):
                for j in range(-n, n + 1):
                    x, y = cx + (i * c - j * si) * pitch, cy + (i * si + j * c) * pitch
                    u = (x - cx) * cw + (y - cy) * sw; v = -(x - cx) * sw + (y - cy) * cw
                    if abs(u) < 29 - dot * pitch and abs(v) < 18 - dot * pitch:
                        rr = dot * pitch
                        d.ellipse([(x - rr) * U, (y - rr) * U, (x + rr) * U, (y + rr) * U], fill=s.INK)
        im = Image.new("RGBA", (W, H), s.BG + (255,))
        lay, pos = fit_layer(lay, W, H, 0.92)
        im.alpha_composite(lay, pos)
        return im


class OS2Rings:
    """The OS/2 ring artwork. zoom=None: the black diamond centred on white, as
    drawn. zoom=k: on black, k x the screen height, so the rings fill the screen
    and the diamond's edges fall outside it."""
    palette = [(0, 0, 0), (0x16, 0x79, 0x47), (0xBF, 0xBE, 0xBE), (0xF1, 0x47, 0x1D),
               (0xFA, 0xBC, 0x09), (0x17, 0x70, 0xC1)]
    def __init__(s, zoom=None):
        s.zoom = zoom
        if zoom is None: s.palette = s.palette + [(0xFF, 0xFF, 0xFF)]
    def draw(s, A, W, H):
        art = A["os2art"]
        bg = (0, 0, 0, 255) if s.zoom else (0xFF, 0xFF, 0xFF, 255)
        im = Image.new("RGBA", (W, H), bg)
        side = round((s.zoom or 0.94) * H)
        # zoomed: centre on the middle of the ring cluster (artwork px 1170, 1210 of 2560)
        cx, cy = (1170 / 2560, 1210 / 2560) if s.zoom else (0.5, 0.5)
        im.alpha_composite(art.resize((side, side), Image.LANCZOS),
                           (round(W / 2 - cx * side), round(H / 2 - cy * side)))
        return im


class OS2Ring:
    """A single OS/2 ring, centred on black."""
    def __init__(s, col): s.col, s.palette = col, [(0, 0, 0), col]
    def draw(s, A, W, H):
        side = round(0.66 * H)
        im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        im.alpha_composite(tinted(A["os2ring"].resize((side, side), Image.LANCZOS), s.col),
                           ((W - side) // 2, (H - side) // 2))
        return im


class ThinkPadBee:
    """The user's compositions (customibm/customibm2/customlenovo, 640x480):
    the Rand bee poster centred, ThinkPad(R) anchored bottom-left, a maker logo
    anchored top-right. All offsets and sizes are in units of screen height
    (measured at H=480), so the corner items keep their corner positions as the
    width changes."""
    TEXT, RED_DOT, LOGO = (0x0B, 0x0B, 0x0B), (0xD4, 0x00, 0x00), (0x3B, 0x5B, 0x8E)
    FONT = "C:/Windows/Fonts/timesbd.ttf"
    CORNERS = {   # mask key, logo width (or rotated length), right margin, top margin, tilt, colour
        "ibm":        ("8bar", 78, 26, 23, 0, LOGO),
        "ibm_tilted": ("8bar", 120, 12, 11, 22, TEXT),
        "lenovo":     ("len03", 84, 22, 20, 0, LOGO),
    }
    def __init__(s, corner):
        s.corner = corner
        s.palette = RandBee.palette + [s.RED_DOT, s.CORNERS[corner][5]]
    def draw(s, A, W, H):
        from PIL import ImageFont
        u = H / 480
        im = RandBee().draw(A, W, H)
        # ThinkPad(R), 20 px from the left, ink bottom 18 px above the bottom edge
        tw = round(0.387 * H); k = tw / A["tp"].width; th = round(A["tp"].height * k)
        x0, y0 = round((0.183 - 67 / 480) * H), round(0.96125 * H) - th
        im.alpha_composite(tinted(A["tp"].resize((tw, th), Image.LANCZOS), s.TEXT), (x0, y0))
        im.alpha_composite(tinted(A["tpdot"].resize((tw, th), Image.LANCZOS), s.RED_DOT), (x0, y0))
        f = ImageFont.truetype(s.FONT, max(8, round(0.45 * th)))
        ImageDraw.Draw(im).text((x0 + tw + round(0.006 * H), y0), "\u00ae", font=f, fill=s.TEXT, anchor="lt")
        # maker logo, top right
        key, width, rm, tm, tilt, col = s.CORNERS[s.corner]
        src = A[key].crop(A[key].getbbox())
        lw = round(width * u); lh = round(src.height * lw / src.width)
        logo = src.resize((lw, lh), Image.LANCZOS)
        if tilt: logo = logo.rotate(-tilt, resample=Image.BICUBIC, expand=True)
        logo = logo.crop(logo.getbbox())
        im.alpha_composite(tinted(logo, col), (W - round(rm * u) - logo.width, round(tm * u)))
        return im


class InternalUse:
    """After the 1980s 'IBM INTERNAL USE ONLY' sweatshirt print: 8-bar IBM with a
    tracked-out slab-serif line underneath and a small circled R. The subtext is
    Rokkitt (OFL), a Rockwell/Memphis-style slab, the closest open match to the
    print. Proportions are measured from the photo, relative to logo height."""
    TEXT = "INTERNAL USE ONLY"
    WEIGHT = 650
    def __init__(s, bg, fg):
        s.bg, s.fg, s.palette = bg, fg, [bg, fg]
    def font(s, A, size):
        from PIL import ImageFont
        f = ImageFont.truetype(A["rokkitt"], size); f.set_variation_by_axes([s.WEIGHT]); return f
    def draw(s, A, W, H):
        from PIL import ImageFont
        src = A["8bar"].crop(A["8bar"].getbbox())
        lw = round(0.667 * H); lh = round(src.height * lw / src.width)
        cap = 0.151 * lh; gap = 0.135 * lh
        lx, ly = (W - lw) // 2, round((H - (lh + gap + cap)) / 2)
        im = Image.new("RGBA", (W, H), s.bg + (255,))
        im.alpha_composite(tinted(src.resize((lw, lh), Image.LANCZOS), s.fg), (lx, ly))
        # subtext: cap height `cap`, tracked to run from the logo's left edge to 97.5% of its width
        probe = s.font(A, 100); hb = probe.getbbox("H")
        font = s.font(A, max(6, round(100 * cap / (hb[3] - hb[1]))))
        widths = [font.getlength(c) for c in s.TEXT]
        first = font.getbbox(s.TEXT[0])[0]; last = font.getbbox(s.TEXT[-1])[2]
        natural = sum(widths[:-1]) + last - first
        track = (0.975 * lw - natural) / (len(s.TEXT) - 1)
        d = ImageDraw.Draw(im)
        x, base = lx - first, ly + lh + gap + cap
        for c, cw in zip(s.TEXT, widths):
            d.text((x, base), c, font=font, fill=s.fg, anchor="ls")
            x += cw + track
        # circled R just past the M's bottom-right corner
        r = 0.073 * lh; cx, cy = lx + lw + 0.056 * lh, ly + lh + 0.026 * lh
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=s.fg, width=max(1, round(0.014 * lh)))
        rf = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", max(6, round(1.1 * r)))
        d.text((cx, cy), "R", font=rf, fill=s.fg, anchor="mm")
        return im


SHIRT_BLUE, PRINT_WHITE = (0x26, 0x52, 0x96), (0xF4, 0xF4, 0xF0)

OS2_RED, OS2_YELLOW, OS2_GREEN =(0xF1, 0x47, 0x1D), (0xFA, 0xBC, 0x09), (0x16, 0x79, 0x47)
OS2_BLUE, OS2_GREY, IBM_BLUE = (0x17, 0x70, 0xC1), (0xBF, 0xBE, 0xBE), (0x1F, 0x70, 0xC1)
BLACK0, WHITE0 = (0, 0, 0), (0xFF, 0xFF, 0xFF)
CREAM = (0xEF, 0xE7, 0xC3)

DESIGNS = {
    "thinkpad_ibm_black":        ThinkPadBoot(BLACK0, CREAM, "ibm", (0x40, 0xC8, 0xEB)),
    "thinkpad_ibm_white":        ThinkPadBoot(WHITE0, BLACK0, "ibm", (0x1F, 0x70, 0xC1)),
    "thinkpad_lenovo2003_black": ThinkPadBoot(BLACK0, CREAM, "lenovo2003", (0x3A, 0x8F, 0xD8), red_dot=True),
    "thinkpad_lenovo2003_white": ThinkPadBoot(WHITE0, BLACK0, "lenovo2003", (0x25, 0x69, 0xA7), red_dot=True),
    "thinkpad_lenovo2015_black": ThinkPadBoot(BLACK0, CREAM, "lenovo2015", red_dot=True),
    "thinkpad_lenovo2015_white": ThinkPadBoot(WHITE0, BLACK0, "lenovo2015", red_dot=True),
    "ibm_pcjr": PCjr(),
    "ibm_diagonal_grey":  Diagonal((0x8C, 0x8B, 0x92), (0xF4, 0xF4, 0xF2)),
    "ibm_diagonal_black": Diagonal((0x0A, 0x0A, 0x0C), (0x2E, 0x9E, 0x68)),
    "ibm_diagonal_green": Diagonal((0x2F, 0x73, 0x47), (0xF4, 0xF4, 0xF2)),
    "ibm_diagonal_blue":  Diagonal(IBM_BLUE, (0xF4, 0xF4, 0xF2)),
    "ibm_diagonal_red":   Diagonal(OS2_RED, (0xF4, 0xF4, 0xF2)),
    "ibm_diagonal_yellow": Diagonal(OS2_YELLOW, (0x0A, 0x0A, 0x0C)),
    "ibm_rand_bee":       RandBee(),
    "thinkpad_bee_ibm":        ThinkPadBee("ibm"),
    "thinkpad_bee_ibm_tilted": ThinkPadBee("ibm_tilted"),
    "thinkpad_bee_lenovo":     ThinkPadBee("lenovo"),
    "ibm_internal_use_blue":  InternalUse(SHIRT_BLUE, PRINT_WHITE),
    "ibm_internal_use_black": InternalUse(BLACK0, IBM_BLUE),
    "os2_diamond":        OS2Rings(),
    "os2_rings":          OS2Rings(zoom=1.3),
    "os2_ring_red":       OS2Ring(OS2_RED),
    "os2_ring_yellow":    OS2Ring(OS2_YELLOW),
    "os2_ring_green":     OS2Ring(OS2_GREEN),
    "os2_ring_blue":      OS2Ring(OS2_BLUE),
    "os2_ring_grey":      OS2Ring(OS2_GREY),
    "ibm_dominoes":       Dominoes(),
    "ibm_annual1991_white": Annual1991((0xF7, 0xF6, 0xF2)),
    "ibm_annual1991_black": Annual1991((0x0A, 0x0A, 0x0C)),
    "ibm_plex_1956":      Plex(striped=True),
    "ibm_plex_1956_solid": Plex(striped=False),
}


def main(assets, out, only=None):
    A = {"8bar": Image.open(f"{assets}/ibm_8bar_mask.png").convert("L"),
         "plex": Image.open(f"{assets}/plex_letters_mask.png").convert("L"),
         "plexfill": Image.open(f"{assets}/plex_fill_mask.png").convert("L"),
         "tp": Image.open(f"{assets}/thinkpad_letters_mask.png").convert("L"),
         "tpdot": Image.open(f"{assets}/thinkpad_dot_mask.png").convert("L"),
         "len03": Image.open(f"{assets}/lenovo2003_mask.png").convert("L"),
         "len15": Image.open(f"{assets}/lenovo2015.png").convert("RGBA"),
         "os2art": Image.open(f"{assets}/os2_artwork.png").convert("RGBA"),
         "os2ring": Image.open(f"{assets}/os2_ring_mask.png").convert("L"),
         "rokkitt": f"{assets}/Rokkitt[wght].ttf"}
    os.makedirs(out, exist_ok=True)
    for name, des in DESIGNS.items():
        if only and name not in only: continue
        dst = f"{out}/{name}"; os.makedirs(dst, exist_ok=True)
        for w, h in SIZES:
            if isinstance(des, PCjr):           # pixel-exact CGA rectangles
                im = snap(des.draw(A, w, h), des.palette)
            else:
                hi = des.draw(A, w * SS, h * SS).convert("RGB")
                im = snap(hi.resize((w, h), Image.BOX), ramp(des.palette))
            im.save(f"{dst}/{name}_{w}x{h}.png")
            if (w, h) == (672, 378):            # 24-bit uncompressed, as the AMI patcher needs
                im.convert("RGB").save(f"{dst}/{name}_{w}x{h}.bmp")
        print(name, "ok")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:] or None)
