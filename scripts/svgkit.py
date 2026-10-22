"""SVG asset generator for the BaneleChakuma profile README.

All assets are self-contained SVGs (embedded Fira Code subset, SMIL animation)
so they render inside GitHub's <img> sandbox with no outside services.
Every animation's resting/default state is the finished design, so renderers
that skip animation still show the full content.

Design system (v2)
------------------
* Geometry  - one radius scale (RADIUS), 1px hairlines, and "viewfinder" corner
              brackets that follow the radius of the glass panel they frame.
* Depth     - every card is a deep stage (key + fill light, dot grid, film grain,
              a light-catching hairline edge) holding a frosted glass panel with
              a soft drop shadow and halo. Dots stop at the glass and particles
              behind it turn into soft bokeh, so the glass reads as real.
* Type      - Fira Code 700 display, 600 labels and buttons, 500 UI, 400 text.
* Motion    - GitHub shows README images as plain <img>, so hover can't exist
              there. Links carry an ambient light sheen and an arrow nudge
              instead, and everything enters with one staggered expo-out reveal.
"""
import base64
import hashlib
import io
import math
import os
import random
import re as _re
import struct
import zlib
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
ADV = 0.6  # Fira Code advance width, in em

# ------------------------------------------------------------------ design tokens
RADIUS = {'stage': 20, 'panel': 14, 'chip': 10, 'button': 12, 'box': 9, 'cell': 2.5}
EXPO_OUT = '0.16 1 0.3 1'   # entrances
SOFT_OUT = '0.25 1 0.5 1'   # small settles
EASE_IO = '0.65 0 0.35 1'   # travelling light

_DARK = dict(
    # stage: deep aubergine, fuchsia key light, violet fill light
    stage0='#0b0710', stage1='#170a1f', key='#c026d3', key_op=0.36, fill='#7c3aed', fill_op=0.17,
    vignette_op=0.5, dot='#f0abfc', dot_op=0.15, grain_op=0.45,
    edge0='#f5d0fe', edge0_op=0.46, edge1='#f0abfc', edge1_op=0.07,
    # glass
    glass='#130a1a', glass_op=0.5, glass_hi='#ffffff', glass_hi_op=0.065,
    rim0='#f5d0fe', rim0_op=0.7, rim1='#c026d3', rim1_op=0.2, inner_op=0.18,
    shadow='#000000', shadow_op=0.62, halo='#c026d3', halo_op=0.22,
    # ink
    name0='#ffffff', name1='#fbe8ff', name2='#f0abfc', name_glow='#d946ef', name_glow_op=0.45,
    title='#e879f9', text='#fae8ff', label='#f0abfc', label_op=0.8, muted='#dcb8e6',
    head0='#fdf4ff', head1='#f5d0fe', head2='#e879f9',
    line='#e879f9', bracket='#f5d0fe', accent='#d946ef', soft='#f0abfc', deep='#86198f',
    # components
    chip0='#271030', chip1='#16081d', chip_text='#fae8ff', chip_rim0='#f0abfc', chip_rim1='#a21caf', chip_hi=0.16,
    btn0='#c026d3', btn1='#86198f', btn_text='#ffffff', btn_val='#1a0a22', btn_val_text='#fae8ff',
    glow='#c026d3', glow_op=0.5, sheen='#ffffff', sheen_op=0.18,
    box='#1c0b25', box_op=0.94, shadow_small_op=0.55, packet='#fdf4ff',
)
_LIGHT = dict(
    stage0='#fffbff', stage1='#f7ebfb', key='#f0abfc', key_op=0.55, fill='#c4b5fd', fill_op=0.32,
    vignette_op=0, dot='#c026d3', dot_op=0.15, grain_op=0.3,
    edge0='#e879f9', edge0_op=0.6, edge1='#f0abfc', edge1_op=0.28,
    glass='#ffffff', glass_op=0.58, glass_hi='#ffffff', glass_hi_op=0.55,
    rim0='#e879f9', rim0_op=0.75, rim1='#f0abfc', rim1_op=0.38, inner_op=0.9,
    shadow='#701a75', shadow_op=0.16, halo='#e879f9', halo_op=0.2,
    name0='#4a044e', name1='#86198f', name2='#c026d3', name_glow='#f0abfc', name_glow_op=0.6,
    title='#a21caf', text='#701a75', label='#a21caf', label_op=0.9, muted='#86198f',
    head0='#701a75', head1='#86198f', head2='#a21caf',
    line='#c026d3', bracket='#a21caf', accent='#a21caf', soft='#d946ef', deep='#86198f',
    chip0='#ffffff', chip1='#fbf0fd', chip_text='#701a75', chip_rim0='#e879f9', chip_rim1='#f0abfc', chip_hi=0.9,
    btn0='#c026d3', btn1='#a21caf', btn_text='#ffffff', btn_val='#ffffff', btn_val_text='#701a75',
    glow='#c026d3', glow_op=0.28, sheen='#e879f9', sheen_op=0.3,
    box='#ffffff', box_op=0.9, shadow_small_op=0.11, packet='#86198f',
)
THEMES = {'dark': _DARK, 'light': _LIGHT}
for _th in THEMES.values():  # v1 key names, kept so older imports keep working
    _th.update(panel0=_th['stage0'], panel1=_th['stage1'], chip_fill=_th['chip1'],
               btn_fill=_th['btn0'], heading=_th['head2'])


def font_css(weights_text):
    """weights_text: {weight: text_needing_that_weight} -> @font-face rules (base64 woff2 subsets)."""
    rules = []
    for weight, text in sorted(weights_text.items()):
        chars = ''.join(sorted(set(text))) or ' '
        font = TTFont(f'{FONT_DIR}/fira-code-latin-{weight}-normal.woff2', recalcTimestamp=False)
        opts = subset.Options()
        opts.flavor = 'woff2'
        opts.layout_features = []
        opts.name_IDs = []
        opts.notdef_outline = True
        sub = subset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = 'woff2'
        font['head'].modified = font['head'].created  # keep output byte-identical between runs
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        rules.append(
            "@font-face{font-family:'FC';font-weight:%d;src:url(data:font/woff2;base64,%s) format('woff2')}" % (weight, b64)
        )
    return ''.join(rules)


def tw(text, size, spacing=0.0):
    """Rendered width of monospace text."""
    return len(text) * ADV * size + max(0, len(text) - 1) * spacing


def f(x):
    return ('%.3f' % x).rstrip('0').rstrip('.')


def svg_open(W, H, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">'
            f'<title id="t">{escape(title)}</title>')


def style(css):
    return f"<style>{css}text{{font-family:'FC',ui-monospace,monospace}}</style>"


# ------------------------------------------------------------------ paint helpers
def _stops(stops):
    return ''.join(f'<stop offset="{f(o)}" stop-color="{c}" stop-opacity="{f(a)}"/>' for o, c, a in stops)


def lin(id_, stops, x1=0, y1=0, x2=1, y2=0, user=False):
    u = ' gradientUnits="userSpaceOnUse"' if user else ''
    return f'<linearGradient id="{id_}"{u} x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}">{_stops(stops)}</linearGradient>'


def rad(id_, stops, cx=0.5, cy=0.5, r=0.5):
    return f'<radialGradient id="{id_}" cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}">{_stops(stops)}</radialGradient>'


def blur(id_, sd, W, H, x=0, y=0, glow=False):
    """Gaussian blur over a fixed user-space region (cheap and never clipped)."""
    merge = '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>' if glow else ''
    return (f'<filter id="{id_}" filterUnits="userSpaceOnUse" x="{f(x)}" y="{f(y)}" width="{f(W)}" height="{f(H)}" '
            f'color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="{sd}"/>{merge}</filter>')


def _png_chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)


def noise_uri(size=72, seed=11):
    """Film-grain tile as a 4-bit palette PNG built in pure Python (deterministic, about 2 KB).

    Half the grains are white and half black, so the texture adds tooth without
    shifting the colour underneath; it also breaks up banding in dark gradients.
    """
    rnd = random.Random(seed)
    alphas = [0, 9, 17, 28]
    palette = [(255, 255, 255)] * 4 + [(0, 0, 0)] * 4
    rows = bytearray()
    for _ in range(size):
        rows.append(0)
        px = []
        for _ in range(size):
            level = min(3, int(rnd.random() ** 1.7 * 4))
            px.append(level + (4 if rnd.random() < 0.5 else 0))
        for i in range(0, size, 2):
            rows.append(px[i] << 4 | px[i + 1])
    png = (b'\x89PNG\r\n\x1a\n'
           + _png_chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 4, 3, 0, 0, 0))
           + _png_chunk(b'PLTE', bytes(c for rgb in palette for c in rgb))
           + _png_chunk(b'tRNS', bytes(alphas + alphas))
           + _png_chunk(b'IDAT', zlib.compress(bytes(rows), 9))
           + _png_chunk(b'IEND', b''))
    return 'data:image/png;base64,' + base64.b64encode(png).decode()


NOISE = noise_uri()


# ------------------------------------------------------------------ motion helpers
def discrete(values, times, dur, begin='0s', repeat='indefinite', attr='width', fill='freeze'):
    """SMIL discrete animation from (time_sec, value) pairs over a cycle of `dur` seconds."""
    kt = ';'.join(f(t / dur) for t in times)
    vs = ';'.join(f(v) if isinstance(v, (int, float)) else v for v in values)
    rep = '' if repeat is None else f' repeatCount="{repeat}"'
    return (f'<animate attributeName="{attr}" calcMode="discrete" values="{vs}" keyTimes="{kt}" '
            f'dur="{f(dur)}s" begin="{begin}"{rep} fill="{fill}"/>')


def typing_tracks(lines, cw, intro, type_s=0.075, hold=1.9, del_s=0.03, gap=0.4):
    """Builds per-line width tracks and one shared cursor-x track for a looping typewriter."""
    t = intro
    slots = []
    for text in lines:
        n = len(text)
        slots.append((t, n))
        t += n * type_s + hold + n * del_s + gap
    cycle = t
    tracks = []
    for (start, n) in slots:
        times, vals = [0.0], [0.0]
        for k in range(1, n + 1):
            times.append(start + k * type_s)
            vals.append(k * cw)
        end_hold = start + n * type_s + hold
        for k in range(1, n + 1):
            times.append(end_hold + k * del_s)
            vals.append((n - k) * cw)
        tracks.append((times, vals))
    # cursor: follows whichever line is active (0 when idle)
    ctimes, cvals = [0.0], [0.0]
    for (times, vals) in tracks:
        for tt, vv in zip(times[1:], vals[1:]):
            ctimes.append(tt)
            cvals.append(vv)
    return tracks, (ctimes, cvals), cycle


def reveal(begin, dur=0.7, rise=6, spline=EXPO_OUT):
    """One-shot entrance: fade in (and rise) after `begin` seconds, resting on the finished state."""
    tot = begin + dur
    k = f(begin / tot)
    out = (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{k};1" calcMode="spline" '
           f'keySplines="0 0 1 1;0.4 0 0.2 1" dur="{f(tot)}s" fill="freeze"/>')
    if rise:
        out += (f'<animateTransform attributeName="transform" type="translate" values="0 {f(rise)};0 {f(rise)};0 0" '
                f'keyTimes="0;{k};1" calcMode="spline" keySplines="0 0 1 1;{spline}" dur="{f(tot)}s" fill="freeze"/>')
    return out


def sheen(clip_id, x, y, w, h, begin, period, op, band=34):
    """Slanted light band that sweeps a shape once per period: the ambient stand-in for hover.

    Needs a horizontal 'shg' gradient in the file's <defs>.
    """
    k = h * 0.36
    travel = w + band + 2 * k
    hit = 0.95 / period
    d = f'M{f(x - band - k)} {f(y + h)}h{f(band)}l{f(k)} {f(-h)}h{f(-band)}z'
    return (f'<g clip-path="url(#{clip_id})"><path d="{d}" fill="url(#shg)" opacity="{f(op)}">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{f(travel)} 0;{f(travel)} 0" '
            f'keyTimes="0;{f(hit)};1" calcMode="spline" keySplines="{EASE_IO};0 0 1 1" dur="{f(period)}s" '
            f'begin="{f(begin)}s" repeatCount="indefinite"/></path></g>')


def sheen_grad(color):
    return lin('shg', [(0, color, 0), (0.5, color, 1), (1, color, 0)])


def arrow(cx, cy, col, sw=1.7, s=4.5):
    return (f'<path d="M{f(cx - s)} {f(cy + s)}L{f(cx + s)} {f(cy - s)}M{f(cx - s + 2.4)} {f(cy - s)}H{f(cx + s)}V{f(cy + s - 2.4)}" '
            f'fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')


def nudge(begin, period, dist=2.2):
    """Arrow nudges up-right as the sheen reaches it, then settles."""
    a, b = 0.22 / period, 0.62 / period
    return (f'<animateTransform attributeName="transform" type="translate" values="0 0;{f(dist)} {f(-dist)};0 0;0 0" '
            f'keyTimes="0;{f(a)};{f(b)};1" calcMode="spline" keySplines="{SOFT_OUT};0.5 0 0.5 1;0 0 1 1" '
            f'dur="{f(period)}s" begin="{f(begin)}s" repeatCount="indefinite"/>')


# ------------------------------------------------------------------ surfaces
def rrect_d(x, y, w, h, r):
    """Rounded-rectangle path data."""
    return (f'M{f(x + r)} {f(y)}H{f(x + w - r)}A{r} {r} 0 0 1 {f(x + w)} {f(y + r)}V{f(y + h - r)}'
            f'A{r} {r} 0 0 1 {f(x + w - r)} {f(y + h)}H{f(x + r)}A{r} {r} 0 0 1 {f(x)} {f(y + h - r)}'
            f'V{f(y + r)}A{r} {r} 0 0 1 {f(x + r)} {f(y)}Z')


def stage(th, W, H, key=(0.74, 0.14, 0.62), fill=(0.06, 1.05, 0.72), panel=None, dots=True, grain=1.0, dots_begin=None):
    """Card backdrop: deep gradient, key + fill light, dot grid, film grain, light-catching edge.

    `panel` = (x, y, w, h, r) of the glass panel: defines clip paths 'out' (stage minus panel) and
    'in' (panel) so the dot grid and crisp particles stop at the glass. Clip paths are vector
    operations, far cheaper than masks for an image that keeps animating.
    Returns (defs, body, edge): draw body first, edge last so the rim sits on top of everything.
    """
    r = RADIUS['stage']
    d = [lin('sg', [(0, th['stage0'], 1), (1, th['stage1'], 1)], 0, 0, 1, 1),
         rad('sk', [(0, th['key'], th['key_op']), (1, th['key'], 0)], *key),
         rad('sf', [(0, th['fill'], th['fill_op']), (1, th['fill'], 0)], *fill),
         f'<clipPath id="sc"><rect width="{W}" height="{H}" rx="{r}"/></clipPath>',
         lin('se', [(0, th['edge0'], th['edge0_op']), (0.45, th['edge1'], th['edge1_op'] * 1.6),
                    (1, th['edge1'], th['edge1_op'])], 0, 0, 1, 1)]
    if panel:
        d.append(f'<clipPath id="out"><path d="M0 0H{W}V{H}H0Z{rrect_d(*panel)}" clip-rule="evenodd"/></clipPath>')
        d.append(f'<clipPath id="in"><path d="{rrect_d(*panel)}"/></clipPath>')
    b = ['<g clip-path="url(#sc)">',
         f'<rect width="{W}" height="{H}" fill="url(#sg)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#sk)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#sf)"/>']
    if dots:
        d.append(f'<pattern id="sd" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="0.9" fill="{th["dot"]}"/></pattern>')
        intro = '' if dots_begin is None else reveal(dots_begin, 0.8, 0)
        if panel:
            b.append(f'<g clip-path="url(#out)">{intro}<rect width="{W}" height="{H}" fill="url(#sd)" opacity="{f(th["dot_op"])}"/></g>')
        else:
            d.append(rad('sdf', [(0, '#ffffff', 1), (0.72, '#ffffff', 0.6), (1, '#ffffff', 0)], 0.5, 0.5, 0.75))
            d.append(f'<mask id="sdm" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#sdf)"/></mask>')
            b.append(f'<rect width="{W}" height="{H}" fill="url(#sd)" opacity="{f(th["dot_op"])}" mask="url(#sdm)"/>')
    if th['vignette_op']:
        d.append(rad('sv', [(0.5, '#000000', 0), (1, '#000000', th['vignette_op'])], 0.5, 0.42, 0.8))
        b.append(f'<rect width="{W}" height="{H}" fill="url(#sv)"/>')
    if grain:
        d.append(f'<pattern id="sn" width="72" height="72" patternUnits="userSpaceOnUse"><image href="{NOISE}" width="72" height="72"/></pattern>')
        b.append(f'<rect width="{W}" height="{H}" fill="url(#sn)" opacity="{f(th["grain_op"] * grain)}"/>')
    b.append('</g>')
    edge = f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="{f(r - 0.5)}" fill="none" stroke="url(#se)"/>'
    return ''.join(d), ''.join(b), edge


def glass(th, x, y, w, h, W, H, r=RADIUS['panel']):
    """Frosted panel: soft drop shadow, translucent fill, top sheen, lit rim, inner top highlight."""
    m = 44
    d = [lin('gh', [(0, th['glass_hi'], th['glass_hi_op']), (0.55, th['glass_hi'], 0)], 0, 0, 0, 1),
         lin('gr', [(0, th['rim0'], th['rim0_op']), (0.5, th['rim1'], th['rim1_op'] * 1.5), (1, th['rim1'], th['rim1_op'])], 0, 0, 1, 1),
         lin('gi', [(0, '#ffffff', th['inner_op']), (0.22, '#ffffff', 0)], 0, 0, 0, 1),
         blur('gsb', 13, w + 2 * m, h + 2 * m, x - m, y - m)]
    b = [f'<rect x="{f(x + 10)}" y="{f(y + 12)}" width="{f(w - 20)}" height="{f(h - 6)}" rx="{r}" fill="{th["shadow"]}" '
         f'opacity="{f(th["shadow_op"])}" filter="url(#gsb)"/>',
         f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{r}" fill="{th["glass"]}" fill-opacity="{f(th["glass_op"])}"/>',
         f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{r}" fill="url(#gh)"/>',
         f'<rect x="{f(x + 1.5)}" y="{f(y + 1.5)}" width="{f(w - 3)}" height="{f(h - 3)}" rx="{f(r - 1.5)}" fill="none" stroke="url(#gi)"/>',
         f'<rect x="{f(x + 0.5)}" y="{f(y + 0.5)}" width="{f(w - 1)}" height="{f(h - 1)}" rx="{f(r - 0.5)}" fill="none" stroke="url(#gr)" stroke-width="1.1"/>']
    return ''.join(d), ''.join(b)


def brackets(th, x, y, w, h, r=RADIUS['panel'], off=6, tail=10, sw=2, op=0.95):
    """Viewfinder corners: short arcs concentric with the panel's own corner radius."""
    R = f(r + off)
    ps = [f'M{f(x - off)} {f(y + r + tail)}V{f(y + r)}A{R} {R} 0 0 1 {f(x + r)} {f(y - off)}H{f(x + r + tail)}',
          f'M{f(x + w - r - tail)} {f(y - off)}H{f(x + w - r)}A{R} {R} 0 0 1 {f(x + w + off)} {f(y + r)}V{f(y + r + tail)}',
          f'M{f(x + w + off)} {f(y + h - r - tail)}V{f(y + h - r)}A{R} {R} 0 0 1 {f(x + w - r)} {f(y + h + off)}H{f(x + w - r - tail)}',
          f'M{f(x + r + tail)} {f(y + h + off)}H{f(x + r)}A{R} {R} 0 0 1 {f(x - off)} {f(y + h - r)}V{f(y + h - r - tail)}']
    return ''.join(f'<path d="{p}" fill="none" stroke="{th["bracket"]}" stroke-width="{sw}" stroke-linecap="round" '
                   f'stroke-opacity="{f(op)}"/>' for p in ps)


def chamfer_path(x, y, w, h, c):
    """Rectangle with the top-left and bottom-right corners cut (v1 shape, kept for compatibility)."""
    return (f'M{f(x + c)} {f(y)}H{f(x + w)}V{f(y + h - c)}L{f(x + w - c)} {f(y + h)}'
            f'H{f(x)}V{f(y + c)}Z')


def diamond(cx, cy, s, rx, **attrs):
    extra = ''.join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return (f'<rect x="{f(cx - s / 2)}" y="{f(cy - s / 2)}" width="{f(s)}" height="{f(s)}" rx="{f(rx)}" '
            f'transform="rotate(45 {f(cx)} {f(cy)})"{extra}/>')


# ------------------------------------------------------------------ header
PIPE_STEPS = ['extract', 'validate', 'clean', 'load']


def header(theme_name):
    th = THEMES[theme_name]
    W, H = 900, 250
    name = 'BANELE CHAKUMA'
    title = 'ASPIRING DATA ENGINEER'
    lines = ['Hello reader', 'welcome to my github profile', 'making a difference with tech']
    label = 'STATUS'
    fs_tag = 17
    cw = ADV * fs_tag
    tracks, (ctimes, cvals), cycle = typing_tracks(lines, cw, intro=1.5)
    css = font_css({700: name, 600: title + label + '>', 500: ''.join(PIPE_STEPS), 400: ''.join(lines)})

    px, py, pw, ph, pr = 28, 26, 844, 198, RADIUS['panel']
    x0, x1 = px + 26, px + pw - 26          # content edges: 54 .. 846
    cx, cy = W / 2, H / 2
    open_anim = ('<animateTransform attributeName="transform" type="scale" values="0.001 0.02;1 0.02;1 1" '
                 'keyTimes="0;0.45;1" calcMode="spline" keySplines="0.2 0.8 0.2 1;0.25 1 0.35 1" dur="0.95s" fill="freeze"/>')

    def opening(inner):
        """The glass opens from a line (v1 signature), scaled about the card centre."""
        return (f'<g transform="translate({f(cx)} {f(cy)})"><g>{open_anim}'
                f'<g transform="translate({f(-cx)} {f(-cy)})">{inner}</g></g></g>')

    sdefs, sbody, sedge = stage(th, W, H, key=(0.74, 0.12, 0.62), fill=(0.08, 1.0, 0.7),
                                panel=(px, py, pw, ph, pr), dots_begin=0.85)
    gdefs, gbody = glass(th, px, py, pw, ph, W, H, pr)

    p = [svg_open(W, H, 'Banele Chakuma, Aspiring Data Engineer'), style(css), '<defs>', sdefs, gdefs]
    p.append(lin('nm', [(0, th['name0'], 1), (0.5, th['name1'], 1), (1, th['name2'], 1)], 0, 0, 0.55, 1))
    p.append(lin('dv', [(0, th['accent'], 0.75), (1, th['accent'], 0)], 124, 0, 818, 0, user=True))
    p.append(lin('dv2', [(0, th['soft'], 0.95), (0.08, th['accent'], 0.7), (0.5, th['accent'], 0.22), (1, th['accent'], 0)], x0, 0, x1, 0, user=True))
    p.append(rad('bk', [(0, th['line'], 0.85), (0.45, th['line'], 0.3), (1, th['line'], 0)]))
    p.append(rad('pk', [(0, th['line'], 0.75), (1, th['line'], 0)]))
    p.append(blur('nb', 9, 460, 110, 20, 50))
    p.append(blur('cgl', 2.6, 820, 60, 50, 166, glow=True))
    for i, _ in enumerate(lines):
        w0 = tw(lines[0], fs_tag) if i == 0 else 0
        p.append(f'<clipPath id="ty{i}"><rect x="{x0 + 22}" y="177" width="{f(w0)}" height="30">'
                 + discrete(tracks[i][1], tracks[i][0], cycle) + '</rect></clipPath>')
    p.append('</defs>')

    p.append(sbody)
    # drifting particles: crisp in the margin, soft bokeh behind the glass
    rnd = random.Random(7)
    crisp, bokeh = [], []
    for _ in range(24):
        x = rnd.uniform(18, 882)
        y = rnd.uniform(40, 244)
        r = rnd.choice([0.8, 1.0, 1.3, 1.7])
        dur = rnd.uniform(6.5, 11.5)
        beg = -rnd.uniform(0, dur)
        rise = rnd.uniform(40, 90)
        drift = rnd.uniform(-8, 8)
        op = rnd.uniform(0.35, 0.85)
        move = (f'<animateTransform attributeName="transform" type="translate" values="0 0;{f(drift)} {f(-rise)}" '
                f'dur="{f(dur)}s" begin="{f(beg)}s" repeatCount="indefinite"/>')

        def fade_loop(o):
            return f'<animate attributeName="opacity" values="0;{f(o)};0" dur="{f(dur)}s" begin="{f(beg)}s" repeatCount="indefinite"/>'
        crisp.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{th["line"]}" opacity="0">{move}{fade_loop(op)}</circle>')
        bokeh.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r * 3.4)}" fill="url(#bk)" opacity="0">{move}{fade_loop(op * 0.6)}</circle>')
    p.append('<g clip-path="url(#sc)"><g clip-path="url(#out)">' + reveal(0.85, 0.8, 0) + ''.join(crisp) + '</g></g>')
    p.append(opening(gbody + brackets(th, px, py, pw, ph, pr)))
    p.append('<g clip-path="url(#in)">' + reveal(0.85, 0.8, 0) + ''.join(bokeh) + '</g>')

    # top strip
    p.append('<g>' + reveal(0.8, 0.6, 0))
    p.append(f'<text x="{x0}" y="56" font-size="11" font-weight="600" letter-spacing="4" fill="{th["label"]}" '
             f'fill-opacity="{f(th["label_op"])}">{label}</text>')
    p.append(f'<line x1="124" y1="52" x2="818" y2="52" stroke="url(#dv)" stroke-width="1"/>')
    p.append(f'<circle cx="{x1 - 4}" cy="52" r="4" fill="none" stroke="{th["accent"]}" stroke-width="1.2" opacity="0">'
             f'<animate attributeName="r" values="4;11" dur="2.4s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0.7;0" dur="2.4s" repeatCount="indefinite"/></circle>')
    p.append(f'<rect x="{x1 - 8}" y="48" width="8" height="8" rx="2" fill="{th["accent"]}">'
             '<animate attributeName="opacity" values="1;0.35;1" dur="2.4s" repeatCount="indefinite"/></rect>')
    p.append('</g>')
    # name: crisp gradient over a wide soft halo
    p.append('<g>' + reveal(0.95, 0.75, 6))
    p.append(f'<text x="{x0}" y="113" font-size="40" font-weight="700" letter-spacing="2.6" fill="{th["name_glow"]}" '
             f'opacity="{f(th["name_glow_op"])}" filter="url(#nb)">{name}</text>')
    p.append(f'<text x="{x0}" y="113" font-size="40" font-weight="700" letter-spacing="2.6" fill="url(#nm)">{name}</text>')
    p.append('</g>')
    p.append('<g>' + reveal(1.12, 0.75, 6))
    p.append(f'<text x="{x0 + 2}" y="144" font-size="13.5" font-weight="600" letter-spacing="5.4" fill="{th["title"]}">{title}</text>')
    p.append(f'<line x1="{x0}" y1="162" x2="{x1}" y2="162" stroke="url(#dv2)" stroke-width="1"/>')
    p.append('</g>')
    # typing taglines
    p.append('<g>' + reveal(1.3, 0.3, 0))
    p.append(f'<text x="{x0}" y="197" font-size="{fs_tag}" font-weight="600" fill="{th["accent"]}">&gt;</text>')
    for i, line in enumerate(lines):
        p.append(f'<text x="{x0 + 22}" y="197" font-size="{fs_tag}" font-weight="400" fill="{th["text"]}" clip-path="url(#ty{i})">{escape(line)}</text>')
    cur0 = x0 + 22 + tw(lines[0], fs_tag) + 3
    p.append(f'<g filter="url(#cgl)"><rect x="{f(cur0)}" y="182" width="9" height="19" rx="1.5" fill="{th["line"]}">'
             + discrete([x0 + 22 + v + 3 for v in cvals], ctimes, cycle, attr='x')
             + '<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" calcMode="discrete" dur="1s" repeatCount="indefinite"/>'
             + '</rect></g>')
    p.append('</g>')
    p.append(pipeline_motif(th, reveal(1.25, 0.7, 6), [x1 - 274, x1 - 188, x1 - 102, x1 - 16], 113))
    p.append(sedge)
    p.append('</svg>')
    return ''.join(p)


def pipeline_motif(th, entrance, xs, y):
    """Small animated extract -> validate -> clean -> load pipeline (words from the README)."""
    period = 3.6
    out = ['<g>' + entrance]
    for i in range(3):
        out.append(f'<line x1="{xs[i] + 17}" y1="{y}" x2="{xs[i + 1] - 17}" y2="{y}" stroke="{th["accent"]}" stroke-width="1.6" '
                   f'stroke-linecap="round" stroke-dasharray="0.01 5" opacity="0.85">'
                   f'<animate attributeName="stroke-dashoffset" values="10.02;0" dur="1.4s" repeatCount="indefinite"/></line>')
    for i, x in enumerate(xs):
        arrive = (i * 0.9) % period
        pulse = (f'dur="{period}s" begin="{f(arrive + 1.4)}s" repeatCount="indefinite"')
        out.append(f'<circle cx="{x}" cy="{y}" r="17" fill="url(#pk)" opacity="0">'
                   f'<animate attributeName="opacity" values="0;0.75;0;0" keyTimes="0;0.08;0.45;1" {pulse}/></circle>')
        out.append(diamond(x, y, 22, 3.5, fill=th['stage0'], fill_opacity='0.6', stroke=th['line'], stroke_width='1.2'))
        out.append(diamond(x, y, 8, 1.2, fill=th['soft'], opacity='0.4')[:-2]
                   + f'><animate attributeName="opacity" values="0.4;1;0.4;0.4" keyTimes="0;0.08;0.3;1" {pulse}/></rect>')
        out.append(f'<text x="{x}" y="{y + 34}" font-size="10.5" font-weight="500" letter-spacing="0.6" '
                   f'text-anchor="middle" fill="{th["muted"]}">{PIPE_STEPS[i]}</text>')
    for i in range(3):
        x1, x2 = xs[i] + 17, xs[i + 1] - 17
        b0 = 1.4 + i * 0.9
        move = (f'<animateTransform attributeName="transform" type="translate" values="{x1} 0;{x2} 0;{x2} 0" '
                f'keyTimes="0;0.25;1" calcMode="spline" keySplines="0.45 0 0.55 1;0 0 1 1" dur="{period}s" begin="{f(b0)}s" repeatCount="indefinite"/>')
        vis = (f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.03;0.22;0.25;1" dur="{period}s" '
               f'begin="{f(b0)}s" repeatCount="indefinite"/>')
        out.append(f'<g opacity="0">{move}{vis}<circle cx="0" cy="{y}" r="7" fill="url(#pk)" opacity="0.8"/>'
                   f'<circle cx="0" cy="{y}" r="2.4" fill="{th["packet"]}"/></g>')
    out.append('</g>')
    return ''.join(out)


# ------------------------------------------------------------------ section heading
def heading(text, theme_name, width=None):
    """Section heading: diamond glyph + text typed once + rule that draws in after typing.

    The image is sized to its text (plus a short rule) so it stays legible when phones scale it down.
    The glyph's left point sits on x=1 so it lines up optically with the paragraph text below.
    """
    th = THEMES[theme_name]
    H = 44
    fs, ls = 20, 0.4
    adv = ADV * fs + ls
    gx, gy = 11, 22
    x0, base = 31, 29
    n = len(text)
    if width is None:
        width = int(math.ceil(x0 + n * adv + 22 + 160))
    start, per = 0.25, 0.055
    t_end = start + n * per
    full = n * adv
    css = font_css({700: text})
    times = [0.0] + [start + k * per for k in range(1, n + 1)]
    widths = [0.0] + [k * adv for k in range(1, n + 1)]
    cur_x = [x0 + w + 3 for w in widths]
    line_x1 = x0 + full + 22
    blink = [0.0, t_end + 0.45, t_end + 0.9, t_end + 1.35, t_end + 1.8, t_end + 2.25, t_end + 2.7]
    blink_v = [1, 0, 1, 0, 1, 0, 0]
    total_blink = blink[-1] + 0.01
    p = [svg_open(width, H, text), style(css), '<defs>',
         lin('hg', [(0, th['head0'], 1), (0.55, th['head1'], 1), (1, th['head2'], 1)], 0, 0, 0, 1),
         lin('r', [(0, th['accent'], 0.9), (0.35, th['accent'], 0.4), (1, th['accent'], 0)], line_x1, 0, width - 6, 0, user=True),
         rad('gg', [(0, th['accent'], 0.6), (1, th['accent'], 0)]),
         f'<clipPath id="c"><rect x="{x0 - 2}" y="0" width="{f(full + 4)}" height="{H}">'
         + discrete([0.0] + [w + 4 for w in widths[1:]], times, t_end + 0.01, repeat=None) + '</rect></clipPath>',
         '</defs>']
    # glyph: outline diamond, pulsing core, soft glow
    p.append(f'<circle cx="{gx}" cy="{gy}" r="12" fill="url(#gg)" opacity="0.55">'
             '<animate attributeName="opacity" values="0.55;0.15;0.55" dur="2.6s" repeatCount="indefinite"/></circle>')
    p.append(diamond(gx, gy, 14, 2.2, fill='none', stroke=th['head2'], stroke_width='1.5'))
    p.append(diamond(gx, gy, 6, 1, fill=th['soft'])[:-2]
             + '><animate attributeName="opacity" values="1;0.35;1" dur="2.6s" repeatCount="indefinite"/></rect>')
    p.append(f'<text x="{x0}" y="{base}" font-size="{fs}" font-weight="700" letter-spacing="{ls}" fill="url(#hg)" clip-path="url(#c)">{escape(text)}</text>')
    p.append(f'<rect x="{f(x0 + full + 3)}" y="{base - 17}" width="10" height="21" rx="1.5" fill="{th["line"]}" opacity="0">'
             + discrete(cur_x, times, t_end + 0.01, attr='x', repeat=None)
             + discrete(blink_v, blink, total_blink, attr='opacity', repeat=None) + '</rect>')
    a = t_end / (t_end + 0.8)
    draw = (f'keyTimes="0;{f(a)};1" calcMode="spline" keySplines="0 0 1 1;{EXPO_OUT}" dur="{f(t_end + 0.8)}s" fill="freeze"')
    p.append(f'<line x1="{f(line_x1 + 8)}" y1="{base - 7}" x2="{width - 6}" y2="{base - 7}" stroke="url(#r)" stroke-width="1.2" stroke-linecap="round">'
             f'<animate attributeName="x2" values="{f(line_x1 + 8)};{f(line_x1 + 8)};{width - 6}" {draw}/></line>')
    p.append(diamond(line_x1 + 2, base - 7, 4.2, 0.8, fill=th['accent'])[:-2]
             + f'><animate attributeName="opacity" values="0;0;1" {draw}/></rect>')
    p.append('</svg>')
    return ''.join(p)


# ------------------------------------------------------------------ skill chips
def chips(items, theme_name):
    """Row of glass skill chips that settle in one by one; a soft light passes over each in turn."""
    th = THEMES[theme_name]
    fs = 14.5
    h, gap, pad, r = 36, 12, 15, RADIUS['chip']
    widths = [pad + 7 + 11 + tw(t, fs) + pad for t in items]
    mx, mt, mb = 2, 3, 11
    W = int(math.ceil(mx * 2 + sum(widths) + gap * (len(items) - 1)))
    H = mt + h + mb
    css = font_css({500: ''.join(items)})
    xs, x = [], mx
    for w in widths:
        xs.append(x)
        x += w + gap
    p = [svg_open(W, H, ', '.join(items)), style(css), '<defs>',
         lin('cf', [(0, th['chip0'], 1), (1, th['chip1'], 1)], 0, 0, 0, 1),
         lin('cr', [(0, th['chip_rim0'], 0.85), (1, th['chip_rim1'], 0.5)], 0, 0, 0, 1),
         lin('ci', [(0, '#ffffff', th['chip_hi']), (0.45, '#ffffff', 0)], 0, 0, 0, 1),
         sheen_grad(th['sheen']), blur('cb', 4.5, W, H)]
    p += [f'<clipPath id="k{i}"><rect x="{f(x)}" y="{mt}" width="{f(w)}" height="{h}" rx="{r}"/></clipPath>'
          for i, (x, w) in enumerate(zip(xs, widths))]
    p.append('</defs>')
    p.append(f'<g filter="url(#cb)" opacity="{f(th["shadow_small_op"])}">' + reveal(0.3, 0.8, 0)
             + ''.join(f'<rect x="{f(x + 6)}" y="{mt + 10}" width="{f(w - 12)}" height="{h - 7}" rx="{r}" fill="{th["shadow"]}"/>'
                       for x, w in zip(xs, widths)) + '</g>')
    for i, (t, x, w) in enumerate(zip(items, xs, widths)):
        p.append('<g>' + reveal(0.15 + i * 0.12, 0.55, 7, SOFT_OUT))
        p.append(f'<rect x="{f(x)}" y="{mt}" width="{f(w)}" height="{h}" rx="{r}" fill="url(#cf)"/>')
        p.append(sheen(f'k{i}', x, mt, w, h, begin=2.2 + i * 0.32, period=8, op=th['sheen_op']))
        p.append(f'<rect x="{f(x + 1.5)}" y="{mt + 1.5}" width="{f(w - 3)}" height="{h - 3}" rx="{r - 1.5}" fill="none" stroke="url(#ci)"/>')
        p.append(f'<rect x="{f(x + 0.5)}" y="{mt + 0.5}" width="{f(w - 1)}" height="{h - 1}" rx="{r - 0.5}" fill="none" stroke="url(#cr)"/>')
        p.append(diamond(x + pad + 3.5, mt + h / 2, 6.4, 0.9, fill=th['accent']))
        p.append(f'<text x="{f(x + pad + 18)}" y="{f(mt + h / 2 + 5)}" font-size="{fs}" font-weight="500" fill="{th["chip_text"]}">{escape(t)}</text>')
        p.append('</g>')
    p.append('</svg>')
    return ''.join(p)


# ------------------------------------------------------------------ link buttons
def button(label, value, theme_name, delay=0.0):
    """Two-part link button: lit label segment + glass value segment with an arrow.

    `delay` staggers the ambient sheen so a row of buttons shimmers in sequence.
    """
    th = THEMES[theme_name]
    h, r = 40, RADIUS['button']
    fs_l, fs_v = 13.5, 14
    lw = 16 + tw(label, fs_l, 0.6) + 16
    vw = (16 + tw(value, fs_v) + 12 + 12 + 10) if value else 0
    if not value:
        lw += 22
    mx, mt, mb = 10, 6, 14
    W = int(math.ceil(mx * 2 + lw + vw))
    H = mt + h + mb
    x0, y0, bw = mx, mt, lw + vw
    css = font_css({600: label, 500: value or ''})
    alt = label + (f' {value}' if value else '')
    period, begin = 7.0, 2.4 + delay
    p = [svg_open(W, H, alt), style(css), '<defs>',
         f'<clipPath id="o"><rect x="{x0}" y="{y0}" width="{f(bw)}" height="{h}" rx="{r}"/></clipPath>',
         lin('bf', [(0, th['btn0'], 1), (1, th['btn1'], 1)], 0, 0, 1, 1),
         lin('bh', [(0, '#ffffff', 0.26), (0.5, '#ffffff', 0)], 0, 0, 0, 1),
         lin('rim', [(0, th['soft'], 0.95), (1, th['accent'], 0.55)], 0, 0, 1, 1),
         sheen_grad('#ffffff' if theme_name == 'dark' else th['sheen']), blur('bg', 5, W, H),
         '</defs>']
    p.append(f'<rect x="{f(x0 + 8)}" y="{f(y0 + 9)}" width="{f(bw - 16)}" height="{h - 4}" rx="{r}" fill="{th["glow"]}" '
             f'opacity="{f(th["glow_op"])}" filter="url(#bg)"/>')
    p.append('<g clip-path="url(#o)">')
    p.append(f'<rect x="{x0}" y="{y0}" width="{f(lw)}" height="{h}" fill="url(#bf)"/>')
    if value:
        p.append(f'<rect x="{f(x0 + lw)}" y="{y0}" width="{f(vw)}" height="{h}" fill="{th["btn_val"]}" fill-opacity="0.94"/>')
        p.append(f'<line x1="{f(x0 + lw)}" y1="{y0}" x2="{f(x0 + lw)}" y2="{y0 + h}" stroke="#ffffff" stroke-opacity="0.18"/>')
    p.append(f'<rect x="{x0}" y="{y0}" width="{f(lw)}" height="{h}" fill="url(#bh)"/>')
    p.append(sheen('o', x0, y0, bw, h, begin, period, 0.34 if theme_name == 'dark' else 0.4))
    p.append('</g>')
    p.append(f'<rect x="{f(x0 + 0.5)}" y="{f(y0 + 0.5)}" width="{f(bw - 1)}" height="{h - 1}" rx="{f(r - 0.5)}" fill="none" stroke="url(#rim)" stroke-width="1.1"/>')
    p.append(f'<text x="{x0 + 16}" y="{f(y0 + h / 2 + 4.8)}" font-size="{fs_l}" font-weight="600" letter-spacing="0.6" fill="{th["btn_text"]}">{escape(label)}</text>')
    reach = begin + 0.95 * (bw - 14) / (bw + 34 + h * 0.72) - 0.1
    if value:
        p.append(f'<text x="{f(x0 + lw + 16)}" y="{f(y0 + h / 2 + 5)}" font-size="{fs_v}" font-weight="500" fill="{th["btn_val_text"]}">{escape(value)}</text>')
        p.append(f'<g>{nudge(reach, period)}{arrow(x0 + bw - 17, y0 + h / 2, th["line"])}</g>')
    else:
        p.append(f'<g>{nudge(reach, period)}{arrow(x0 + lw - 19, y0 + h / 2, th["btn_text"])}</g>')
    p.append('</svg>')
    return ''.join(p)


# ------------------------------------------------------------------ section divider
def divider(theme_name):
    """Hairline divider with a centre diamond; draws outward from the centre when it scrolls into view."""
    th = THEMES[theme_name]
    W, H = 900, 32
    cx, cy = W / 2, 20
    p = [svg_open(W, H, 'Section divider'), '<defs>',
         lin('dl', [(0, th['accent'], 0), (1, th['accent'], 0.6)], 8, 0, cx - 20, 0, user=True),
         lin('dr', [(0, th['accent'], 0.6), (1, th['accent'], 0)], cx + 20, 0, W - 8, 0, user=True),
         rad('dg', [(0, th['accent'], 0.45), (1, th['accent'], 0)]),
         '</defs>']
    grow = f'calcMode="spline" keySplines="0 0 1 1;{EXPO_OUT}" keyTimes="0;0.15;1" dur="1.3s" fill="freeze"'
    p.append(f'<line x1="8" y1="{cy}" x2="{f(cx - 20)}" y2="{cy}" stroke="url(#dl)" stroke-width="1" stroke-linecap="round">'
             f'<animate attributeName="x1" values="{f(cx - 20)};{f(cx - 20)};8" {grow}/></line>')
    p.append(f'<line x1="{f(cx + 20)}" y1="{cy}" x2="{W - 8}" y2="{cy}" stroke="url(#dr)" stroke-width="1" stroke-linecap="round">'
             f'<animate attributeName="x2" values="{f(cx + 20)};{f(cx + 20)};{W - 8}" {grow}/></line>')
    for dx in (-14, 14):
        p.append(f'<circle cx="{f(cx + dx)}" cy="{cy}" r="1.3" fill="{th["accent"]}" opacity="0.8"/>')
    p.append(f'<circle cx="{f(cx)}" cy="{cy}" r="10" fill="url(#dg)"/>')
    p.append(diamond(cx, cy, 9, 1.6, fill=th['stage0'], stroke=th['line'], stroke_width='1.2'))
    p.append(diamond(cx, cy, 3.6, 0.6, fill=th['soft']))
    p.append('</svg>')
    return ''.join(p)


def uniq(svg):
    """Prefix every id (and its references) with a per-file hash so inlined copies never collide."""
    pre = 'b' + hashlib.md5(svg.encode()).hexdigest()[:6] + '-'
    ids = set(_re.findall(r'id="([^"]+)"', svg))
    for i in sorted(ids, key=len, reverse=True):
        svg = svg.replace(f'id="{i}"', f'id="{pre}{i}"').replace(f'url(#{i})', f'url(#{pre}{i})') \
                 .replace(f'aria-labelledby="{i}"', f'aria-labelledby="{pre}{i}"')
    return svg


# ------------------------------------------------------------------ featured project card
def project_card(theme_name):
    """SafeShelf Tembisa card: title, one-liner, stack and a small animated truck-to-shelf scene."""
    th = THEMES[theme_name]
    W, H = 840, 222
    label, title = 'FEATURED PROJECT', 'SafeShelf Tembisa'
    sub = 'From the delivery truck to the shelf'
    stack = 'Python · SQLite · pytest · GitHub Actions'
    cta = 'View the repo'
    css = font_css({700: title, 600: label + cta, 500: stack, 400: sub})
    px, py, pw, ph, pr = 16, 16, 808, 190, RADIUS['panel']
    x0, x1 = px + 26, px + pw - 26          # 42 .. 798
    sdefs, sbody, sedge = stage(th, W, H, key=(0.82, 0.22, 0.6), fill=(0.04, 1.05, 0.7), dots=False)
    gdefs, gbody = glass(th, px, py, pw, ph, W, H, pr)
    cw = 14 + tw(cta, 13) + 12 + 12 + 12
    cy0, ch = 148, 34
    p = [svg_open(W, H, 'SafeShelf Tembisa: tracking food from the delivery truck to the shelf. View the repository.'),
         style(css), '<defs>', sdefs, gdefs,
         lin('nm', [(0, th['name0'], 1), (0.55, th['name1'], 1), (1, th['name2'], 1)], 0, 0, 0.9, 1),
         lin('bf', [(0, th['btn0'], 1), (1, th['btn1'], 1)], 0, 0, 1, 1),
         lin('bh', [(0, '#ffffff', 0.26), (0.5, '#ffffff', 0)], 0, 0, 0, 1),
         sheen_grad('#ffffff'), blur('bg', 5, cw + 40, ch + 40, x0 - 20, cy0 - 12), rad('pk', [(0, th['line'], 0.75), (1, th['line'], 0)]),
         rad('fg', [(0, th['accent'], 0.6), (1, th['accent'], 0)]),
         f'<clipPath id="cta"><rect x="{x0}" y="{cy0}" width="{f(cw)}" height="{ch}" rx="10"/></clipPath>',
         '</defs>', sbody, gbody, brackets(th, px, py, pw, ph, pr)]
    p.append('<g>' + reveal(0.15, 0.6, 0) + f'<text x="{x0}" y="46" font-size="10.5" font-weight="600" letter-spacing="3.2" '
             f'fill="{th["label"]}" fill-opacity="{f(th["label_op"])}">{label}</text></g>')
    p.append('<g>' + reveal(0.25, 0.7, 6) + f'<text x="{x0}" y="85" font-size="28" font-weight="700" fill="url(#nm)">{title}</text></g>')
    p.append('<g>' + reveal(0.35, 0.7, 6) + f'<text x="{x0}" y="110" font-size="14.5" font-weight="400" fill="{th["text"]}">{escape(sub)}</text></g>')
    dot = f'<tspan fill="{th["accent"]}">·</tspan>'
    p.append('<g>' + reveal(0.45, 0.7, 6) + f'<text x="{x0}" y="133" font-size="12" font-weight="500" fill="{th["muted"]}">'
             + f' {dot} '.join(escape(s) for s in stack.split(' · ')) + '</text></g>')
    # CTA
    p.append('<g>' + reveal(0.55, 0.7, 6))
    p.append(f'<rect x="{x0 + 8}" y="{cy0 + 8}" width="{f(cw - 16)}" height="{ch - 4}" rx="10" fill="{th["glow"]}" '
             f'opacity="{f(th["glow_op"])}" filter="url(#bg)"/>')
    p.append(f'<rect x="{x0}" y="{cy0}" width="{f(cw)}" height="{ch}" rx="10" fill="url(#bf)"/>')
    p.append(f'<rect x="{x0}" y="{cy0}" width="{f(cw)}" height="{ch}" rx="10" fill="url(#bh)"/>')
    p.append(sheen('cta', x0, cy0, cw, ch, 2.6, 7.0, 0.34))
    p.append(f'<rect x="{f(x0 + 0.5)}" y="{f(cy0 + 0.5)}" width="{f(cw - 1)}" height="{ch - 1}" rx="9.5" fill="none" '
             f'stroke="#ffffff" stroke-opacity="0.22"/>')
    p.append(f'<text x="{x0 + 14}" y="{cy0 + 21.5}" font-size="13" font-weight="600" fill="{th["btn_text"]}">{cta}</text>')
    reach = 2.6 + 0.95 * (cw - 14) / (cw + 34 + ch * 0.72) - 0.1
    p.append(f'<g>{nudge(reach, 7.0)}{arrow(x0 + cw - 18, cy0 + ch / 2, th["btn_text"])}</g>')
    p.append('</g>')

    # scene: truck on the ground line, route, shelf (right edge on the content edge)
    s = th['line']
    sw_, sh = 116, 100
    sx, sy = x1 - sw_, 61
    ground = sy + sh
    tx = sx - 212
    p.append('<g>' + reveal(0.5, 0.8, 0))
    p.append(f'<g fill="none" stroke="{s}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round">'
             f'<rect x="{tx}" y="{ground - 53}" width="70" height="40" rx="3"/>'
             f'<path d="M{tx + 70} {ground - 41}H{tx + 89}Q{tx + 92} {ground - 41} {tx + 94} {ground - 39}L{tx + 104} {ground - 28}V{ground - 13}H{tx + 70}Z"/>'
             f'<path d="M{tx + 78} {ground - 37}H{tx + 88}L{tx + 96} {ground - 28}H{tx + 78}Z" stroke-width="1.2"/>'
             f'<circle cx="{tx + 18}" cy="{ground - 9}" r="7" fill="{th["stage0"]}"/><circle cx="{tx + 88}" cy="{ground - 9}" r="7" fill="{th["stage0"]}"/>'
             f'<circle cx="{tx + 18}" cy="{ground - 9}" r="1.6" fill="{s}" stroke="none"/><circle cx="{tx + 88}" cy="{ground - 9}" r="1.6" fill="{s}" stroke="none"/>'
             '</g>')
    p.append(f'<line x1="{tx - 8}" y1="{ground}" x2="{tx + 112}" y2="{ground}" stroke="{s}" stroke-width="1" stroke-linecap="round" opacity="0.4"/>')
    r1, r2, ry = tx + 116, sx - 14, ground - 28
    p.append(f'<line x1="{r1}" y1="{ry}" x2="{r2}" y2="{ry}" stroke="{th["accent"]}" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="0.01 5">'
             '<animate attributeName="stroke-dashoffset" values="10.02;0" dur="1.2s" repeatCount="indefinite"/></line>')
    period = 6
    p.append(f'<g opacity="0"><animateTransform attributeName="transform" type="translate" values="{r1} 0;{r2} 0;{r2} 0" '
             f'keyTimes="0;0.2;1" calcMode="spline" keySplines="0.45 0 0.55 1;0 0 1 1" dur="{period}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.18;0.2;1" dur="{period}s" repeatCount="indefinite"/>'
             f'<circle cx="0" cy="{ry}" r="7" fill="url(#pk)" opacity="0.8"/><circle cx="0" cy="{ry}" r="2.4" fill="{th["packet"]}"/></g>')
    p.append(f'<g fill="none" stroke="{s}" stroke-width="1.5" stroke-linejoin="round"><rect x="{sx}" y="{sy}" width="{sw_}" height="{sh}" rx="4"/>'
             f'<line x1="{sx}" y1="{f(sy + sh / 3)}" x2="{sx + sw_}" y2="{f(sy + sh / 3)}"/><line x1="{sx}" y1="{f(sy + 2 * sh / 3)}" x2="{sx + sw_}" y2="{f(sy + 2 * sh / 3)}"/></g>')
    cols = [13, 37, 61, 85]
    for row in range(3):
        for col, ox in enumerate(cols):
            ix, iy = sx + ox, sy + row * sh / 3 + 7
            if (row, col) == (1, 2):
                p.append(f'<g><animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.55;0.65;0.92;1" dur="{period}s" repeatCount="indefinite"/>'
                         f'<circle cx="{ix + 9}" cy="{f(iy + 10)}" r="16" fill="url(#fg)" opacity="0">'
                         f'<animate attributeName="opacity" values="0;0;0.9;0.2;0.9;0" keyTimes="0;0.25;0.33;0.41;0.49;0.55" dur="{period}s" repeatCount="indefinite"/></circle>'
                         f'<rect x="{ix}" y="{f(iy)}" width="18" height="20" rx="2.5" fill="{th["accent"]}" fill-opacity="0.25" stroke="{th["accent"]}" stroke-width="1.4">'
                         f'<animate attributeName="fill-opacity" values="0.25;0.25;0.9;0.25;0.9;0.25" keyTimes="0;0.25;0.33;0.41;0.49;0.55" dur="{period}s" repeatCount="indefinite"/></rect>'
                         f'<path d="M{ix + 5.5} {f(iy + 6.5)}L{ix + 12.5} {f(iy + 13.5)}M{ix + 12.5} {f(iy + 6.5)}L{ix + 5.5} {f(iy + 13.5)}" '
                         f'stroke="{th["bracket"]}" stroke-width="1.6" stroke-linecap="round"/></g>')
            else:
                p.append(f'<rect x="{ix}" y="{f(iy)}" width="18" height="20" rx="2.5" fill="{th["chip1"]}" stroke="{s}" stroke-width="1.1" stroke-opacity="0.75">'
                         f'<animate attributeName="stroke-opacity" values="0.75;0.75;1;0.75" keyTimes="0;0.2;0.24;0.32" dur="{period}s" repeatCount="indefinite"/></rect>')
    p.append('</g>')
    p.append(sedge)
    p.append('</svg>')
    return ''.join(p)


# ------------------------------------------------------------------ pipeline diagram
def pipeline_diagram(theme_name):
    """SafeShelf data flow drawn as a static SVG (GitHub's profile page can't render Mermaid)."""
    th = THEMES[theme_name]
    W, H = 900, 416
    fs, lh = 12, 15

    inputs = [('Store deliveries',), ('Committee shelf', 'checks'), ('Anonymous resident', 'reports'), ('Truck trip updates',)]
    steps = ['extract', 'validate', 'clean', 'load']
    views = [('committee_view', 118), ('store_view', 206), ('community_view', 258), ('police_view', 336)]
    reports = [(('Expired food on', 'shelves'), 0), (('Suppliers delivering', 'near-expiry stock'), 0),
               (('Essentials about', 'to expire'), 1), (('Store scoreboard',), 2),
               (('Late trucks and', 'unexpected stops'), 3), (('Truck GPS: police only,', 'removed after 30 days'), 3)]
    # columns (x, width) laid out on the 24px stage padding with even gutters
    in_x, in_w = 24, 156
    px, pw = 215, 150
    dx_, dw = 401, 92
    vx, vw = 529, 126
    rx, rw = 686, 190
    heads = [('INPUT FILES', in_x), ('PIPELINE', px), ('DATABASE', dx_), ('ROLE VIEWS', vx), ('DAILY REPORTS', rx)]
    texts = ''.join(''.join(t) for t in inputs) + ''.join(steps) + 'SQLite database' + ''.join(v for v, _ in views)
    texts += ''.join(''.join(r) for r, _ in reports)
    css = font_css({500: texts, 600: ''.join(h for h, _ in heads)})
    sdefs, sbody, sedge = stage(th, W, H, key=(0.5, 0.0, 0.7), fill=(0.02, 1.0, 0.6), grain=0.6)

    p = [svg_open(W, H, 'SafeShelf pipeline: four daily input files go through extract, validate, clean and load into a SQLite database. '
                        'Four role views feed the daily reports. Truck GPS is visible to police only and removed after 30 days.'),
         style(css), '<defs>', sdefs,
         f'<marker id="ar" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
         f'<path d="M1.5 1.5L8.5 5L1.5 8.5Z" fill="{th["line"]}" stroke="{th["line"]}" stroke-linejoin="round"/></marker>',
         lin('bx', [(0, '#ffffff', 0.07 if theme_name == 'dark' else 0.9), (0.5, '#ffffff', 0)], 0, 0, 0, 1),
         lin('db', [(0, th['box'], 1), (0.5, th['chip0'], 1), (1, th['box'], 1)], 0, 0, 1, 0),
         rad('pk', [(0, th['line'], 0.8), (1, th['line'], 0)]),
         blur('sh', 4, W, H),
         '</defs>', sbody, '%SHADOWS%']
    shadows = []

    def box(x, y, w, h, lines, stroke, dashed=False, strong=False, r=RADIUS['box']):
        dash = ' stroke-dasharray="4 3"' if dashed else ''
        shadows.append(f'<rect x="{f(x + 4)}" y="{f(y + 6)}" width="{f(w - 8)}" height="{f(h - 4)}" rx="{r}"/>')
        out = [f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{r}" fill="{th["box"]}" fill-opacity="{f(th["box_op"])}"/>',
               f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{r}" fill="url(#bx)"/>',
               f'<rect x="{f(x + 0.5)}" y="{f(y + 0.5)}" width="{f(w - 1)}" height="{f(h - 1)}" rx="{f(r - 0.5)}" fill="none" stroke="{stroke}" '
               f'stroke-opacity="{0.95 if strong else 0.7}" stroke-width="{1.3 if strong else 1}"{dash}/>']
        top = y + h / 2 - (len(lines) - 1) * lh / 2 + 4.2
        for i, line in enumerate(lines):
            out.append(f'<text x="{f(x + w / 2)}" y="{f(top + i * lh)}" font-size="{fs}" font-weight="500" '
                       f'text-anchor="middle" fill="{th["chip_text"]}">{escape(line)}</text>')
        return ''.join(out)

    flows = []

    def link(x1, y1, x2, y2, delay, dashed=False):
        dx = (x2 - x1) * 0.5
        d = f'M{f(x1)} {f(y1)}C{f(x1 + dx)} {f(y1)} {f(x2 - dx)} {f(y2)} {f(x2)} {f(y2)}'
        if dashed:
            return f'<path d="{d}" fill="none" stroke="{th["accent"]}" stroke-width="1.4" stroke-linecap="round" stroke-dasharray="0.01 4.5"/>'
        flows.append((d, delay))
        return f'<path d="{d}" fill="none" stroke="{th["line"]}" stroke-width="1.1" stroke-opacity="0.6" marker-end="url(#ar)"/>'

    for label, x in heads:
        p.append(diamond(x + 3, 41.5, 5, 0.8, fill=th['accent']))
        p.append(f'<text x="{x + 13}" y="45" font-size="10" font-weight="600" letter-spacing="2.2" fill="{th["label"]}" '
                 f'fill-opacity="{f(th["label_op"])}">{label}</text>')

    in_h = 40
    in_ys = [132, 182, 232, 282]
    py, ph = 162, 140
    mid = py + ph / 2
    for i, cy in enumerate(in_ys):
        p.append(link(in_x + in_w, cy, px - 2, mid, 0.15 * i))
    # pipeline box with four steps
    p.append(box(px, py, pw, ph, [], th['line'], strong=True, r=12))
    for i, s in enumerate(steps):
        yy = py + 31 + i * 28
        gx = px + 26
        p.append(diamond(gx, yy - 4, 7.5, 1.2, fill=th['accent'])[:-2]
                 + f'><animate attributeName="opacity" values="0.35;1;0.35" dur="2.8s" begin="{f(i * 0.7)}s" repeatCount="indefinite"/></rect>')
        p.append(f'<text x="{gx + 15}" y="{yy}" font-size="{fs + 1}" font-weight="500" fill="{th["chip_text"]}">{s}</text>')
    p.append(link(px + pw, mid, dx_ - 2, mid, 0.9))
    # database cylinder
    dy_, dh, ry = mid - 38, 76, 9
    p.append(f'<path d="M{dx_} {dy_ + ry}V{dy_ + dh - ry}A{dw / 2} {ry} 0 0 0 {dx_ + dw} {dy_ + dh - ry}V{dy_ + ry}" '
             f'fill="url(#db)" stroke="{th["line"]}" stroke-width="1.3"/>')
    p.append(f'<ellipse cx="{dx_ + dw / 2}" cy="{dy_ + ry}" rx="{dw / 2}" ry="{ry}" fill="{th["chip0"]}" stroke="{th["line"]}" stroke-width="1.3"/>')
    p.append(f'<path d="M{dx_} {dy_ + ry + 12}A{dw / 2} {ry} 0 0 0 {dx_ + dw} {dy_ + ry + 12}" fill="none" stroke="{th["line"]}" stroke-width="1" stroke-opacity="0.35"/>')
    p.append(f'<text x="{dx_ + dw / 2}" y="{dy_ + 46}" font-size="{fs}" font-weight="500" text-anchor="middle" fill="{th["chip_text"]}">SQLite</text>')
    p.append(f'<text x="{dx_ + dw / 2}" y="{dy_ + 61}" font-size="{fs}" font-weight="500" text-anchor="middle" fill="{th["chip_text"]}">database</text>')
    # views
    vh = 34
    for i, (name, cy) in enumerate(views):
        p.append(link(dx_ + dw, mid, vx - 2, cy, 1.5 + 0.12 * i))
        p.append(box(vx, cy - vh / 2, vw, vh, [name], th['accent'], dashed=(name == 'police_view'), strong=True))
    # reports
    rh = 40
    r_ys = [90, 142, 206, 258, 316, 370]
    for i, ((lines, vi), cy) in enumerate(zip(reports, r_ys)):
        vcy = views[vi][1]
        private = lines[0].startswith('Truck GPS')
        p.append(link(vx + vw, vcy, rx - 2, cy, 2.3 + 0.12 * i, dashed=private))
        p.append(box(rx, cy - rh / 2, rw, rh, list(lines), th['accent'] if private else th['line'], dashed=private))
    for lines, cy in zip(inputs, in_ys):
        p.append(box(in_x, cy - in_h / 2, in_w, in_h, list(lines), th['line']))
    # data packets travelling every link, a wave moving left to right
    period = 4.8
    for d, delay in flows:
        p.append(f'<g opacity="0"><animateMotion path="{d}" keyPoints="0;1;1" keyTimes="0;0.2;1" calcMode="spline" '
                 f'keySplines="0.45 0 0.55 1;0 0 1 1" dur="{period}s" begin="{f(delay)}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.17;0.2;1" dur="{period}s" begin="{f(delay)}s" repeatCount="indefinite"/>'
                 f'<circle r="6" fill="url(#pk)" opacity="0.7"/><circle r="2.1" fill="{th["packet"]}"/></g>')
    p[p.index('%SHADOWS%')] = (f'<g filter="url(#sh)" fill="{th["shadow"]}" opacity="{f(th["shadow_small_op"] * 0.8)}">'
                               + ''.join(shadows) + '</g>')
    p.append(sedge)
    p.append('</svg>')
    return ''.join(p)
