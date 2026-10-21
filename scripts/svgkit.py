"""SVG asset generator for the BaneleChakuma profile README.

All assets are self-contained SVGs (embedded Fira Code subset, SMIL animation)
so they render inside GitHub's <img> sandbox with no outside services.
Every animation's resting/default state is the finished design, so renderers
that skip animation still show the full content.
"""
import base64
import io
import os
import math
import random
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
ADV = 0.6  # Fira Code advance width, in em

THEMES = {
    'dark': {
        'panel0': '#0a0a0a', 'panel1': '#16051c', 'glow': '#86198f',
        'line': '#e879f9', 'bracket': '#f5d0fe', 'accent': '#c026d3', 'deep': '#86198f',
        'name0': '#fdf4ff', 'name1': '#f0abfc', 'name2': '#e879f9',
        'title': '#f0abfc', 'text': '#f5d0fe', 'label': '#f0abfc', 'heading': '#e879f9',
        'dot': '#e879f9', 'chip_fill': '#1a0620', 'chip_text': '#fae8ff', 'btn_fill': '#86198f',
        'btn_text': '#fdf4ff', 'muted': '#d8a8e3',
    },
    'light': {
        'panel0': '#fdf4ff', 'panel1': '#f5e1fb', 'glow': '#f0abfc',
        'line': '#c026d3', 'bracket': '#86198f', 'accent': '#c026d3', 'deep': '#86198f',
        'name0': '#701a75', 'name1': '#86198f', 'name2': '#a21caf',
        'title': '#86198f', 'text': '#701a75', 'label': '#a21caf', 'heading': '#a21caf',
        'dot': '#c026d3', 'chip_fill': '#fdf4ff', 'chip_text': '#701a75', 'btn_fill': '#a21caf',
        'btn_text': '#ffffff', 'muted': '#86198f',
    },
}


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


def chamfer_path(x, y, w, h, c):
    """Rectangle with the top-left and bottom-right corners cut."""
    return (f'M{f(x + c)} {f(y)}H{f(x + w)}V{f(y + h - c)}L{f(x + w - c)} {f(y + h)}'
            f'H{f(x)}V{f(y + c)}Z')


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

    css = font_css({600: name, 500: title + label + '>' + ''.join(PIPE_STEPS), 400: ''.join(lines)})
    rnd = random.Random(7)
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">')
    parts.append(f'<title id="t">Banele Chakuma, Aspiring Data Engineer</title>')
    parts.append(f'<style>{css}text{{font-family:\'FC\',ui-monospace,monospace}}</style>')
    parts.append('<defs>')
    parts.append(f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{th["panel0"]}"/><stop offset="1" stop-color="{th["panel1"]}"/></linearGradient>')
    parts.append(f'<radialGradient id="gl" cx="0.72" cy="0.2" r="0.6"><stop offset="0" stop-color="{th["glow"]}" stop-opacity="0.42"/><stop offset="1" stop-color="{th["glow"]}" stop-opacity="0"/></radialGradient>')
    parts.append(f'<linearGradient id="nm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{th["name0"]}"/><stop offset="0.55" stop-color="{th["name1"]}"/><stop offset="1" stop-color="{th["name2"]}"/></linearGradient>')
    parts.append(f'<linearGradient id="dv" gradientUnits="userSpaceOnUse" x1="58" y1="0" x2="842" y2="0"><stop offset="0" stop-color="{th["accent"]}" stop-opacity="0.9"/><stop offset="1" stop-color="{th["accent"]}" stop-opacity="0"/></linearGradient>')
    parts.append(f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{th["dot"]}"/></pattern>')
    parts.append('<radialGradient id="fade" cx="0.5" cy="0.5" r="0.6"><stop offset="0" stop-color="#fff" stop-opacity="0.9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>')
    parts.append('<mask id="dm"><rect width="900" height="250" fill="url(#fade)"/></mask>')
    parts.append('<filter id="blur" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>')
    parts.append('<filter id="soft" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="2.2"/></filter>')
    parts.append(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>')
    for i, _ in enumerate(lines):
        w0 = tw(lines[0], fs_tag) if i == 0 else 0
        parts.append(f'<clipPath id="ty{i}"><rect x="80" y="176" width="{f(w0)}" height="30">'
                     + discrete(tracks[i][1], tracks[i][0], cycle) + '</rect></clipPath>')
    parts.append('</defs>')

    parts.append('<g clip-path="url(#card)">')
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#gl)"/>')
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity="0.16" mask="url(#dm)"/>')
    # drifting particles
    for i in range(26):
        x = rnd.uniform(40, 860)
        y = rnd.uniform(60, 240)
        r = rnd.choice([0.8, 1.1, 1.4, 1.8])
        dur = rnd.uniform(6, 11)
        beg = -rnd.uniform(0, dur)
        rise = rnd.uniform(40, 90)
        op = rnd.uniform(0.35, 0.8)
        parts.append(
            f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{th["line"]}" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{f(rnd.uniform(-8, 8))} {f(-rise)}" dur="{f(dur)}s" begin="{f(beg)}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;{f(op)};0" dur="{f(dur)}s" begin="{f(beg)}s" repeatCount="indefinite"/>'
            '</circle>')
    parts.append('</g>')

    # window frame: opens as a line, then to full height
    fx, fy, fw, fh = 34, 30, 832, 190
    frame = chamfer_path(fx, fy, fw, fh, 12)
    parts.append('<g transform="translate(450 125)"><g>')
    parts.append('<animateTransform attributeName="transform" type="scale" values="0.001 0.02;1 0.02;1 1" keyTimes="0;0.45;1" calcMode="spline" keySplines="0.2 0.8 0.2 1;0.25 1 0.35 1" dur="0.95s" fill="freeze"/>')
    parts.append('<g transform="translate(-450 -125)">')
    parts.append(f'<path d="{frame}" fill="none" stroke="{th["line"]}" stroke-width="3" opacity="0.45" filter="url(#soft)"/>')
    parts.append(f'<path d="{frame}" fill="{th["panel0"]}" fill-opacity="0.35" stroke="{th["line"]}" stroke-width="1.2" stroke-opacity="0.75"/>')
    b = 18
    for (cx, cy, dx, dy) in [(fx - 4, fy - 4, 1, 1), (fx + fw + 4, fy - 4, -1, 1), (fx - 4, fy + fh + 4, 1, -1), (fx + fw + 4, fy + fh + 4, -1, -1)]:
        parts.append(f'<path d="M{f(cx)} {f(cy + dy * b)}V{f(cy)}H{f(cx + dx * b)}" fill="none" stroke="{th["bracket"]}" stroke-width="2.4"/>')
    parts.append('</g></g></g>')

    def fade(begin, dur=0.5):
        return (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{f(begin / (begin + dur))};1" '
                f'dur="{f(begin + dur)}s" fill="freeze"/>')

    # top strip
    parts.append('<g>' + fade(0.8))
    parts.append(f'<text x="58" y="55" font-size="11" font-weight="500" letter-spacing="4" fill="{th["label"]}">{label}</text>')
    parts.append(f'<line x1="124" y1="51" x2="826" y2="51" stroke="url(#dv)" stroke-width="1"/>')
    parts.append(f'<rect x="836" y="47" width="8" height="8" fill="{th["accent"]}">'
                 '<animate attributeName="opacity" values="1;0.25;1" dur="2.4s" repeatCount="indefinite"/></rect>')
    parts.append('</g>')
    # name with glow
    parts.append('<g>' + fade(0.95))
    parts.append(f'<text x="58" y="112" font-size="40" font-weight="600" letter-spacing="3" fill="{th["line"]}" opacity="0.55" filter="url(#blur)">{name}</text>')
    parts.append(f'<text x="58" y="112" font-size="40" font-weight="600" letter-spacing="3" fill="url(#nm)">{name}</text>')
    parts.append('</g>')
    parts.append('<g>' + fade(1.15))
    parts.append(f'<text x="60" y="143" font-size="14" font-weight="500" letter-spacing="5.2" fill="{th["title"]}">{title}</text>')
    parts.append(f'<line x1="58" y1="161" x2="842" y2="161" stroke="url(#dv)" stroke-width="1"/>')
    parts.append('</g>')
    # typing taglines
    parts.append('<g>' + fade(1.3, 0.3))
    parts.append(f'<text x="58" y="196" font-size="{fs_tag}" font-weight="500" fill="{th["accent"]}">&gt;</text>')
    for i, line in enumerate(lines):
        parts.append(f'<text x="80" y="196" font-size="{fs_tag}" font-weight="400" fill="{th["text"]}" clip-path="url(#ty{i})">{escape(line)}</text>')
    cx0 = 80 + tw(lines[0], fs_tag) + 2
    cursor_vals = [80 + v + 2 for v in cvals]
    parts.append(f'<rect x="{f(cx0)}" y="181" width="9" height="19" fill="{th["line"]}">'
                 + discrete(cursor_vals, ctimes, cycle, attr='x')
                 + '<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" calcMode="discrete" dur="1s" repeatCount="indefinite"/>'
                 + '</rect>')
    parts.append('</g>')
    parts.append(pipeline_motif(th, fade(1.25)))
    parts.append('</svg>')
    return ''.join(parts)


PIPE_STEPS = ['extract', 'validate', 'clean', 'load']


def pipeline_motif(th, fade_anim):
    """Small animated extract -> validate -> clean -> load pipeline (words from the README)."""
    xs = [568, 654, 740, 826]
    y = 112
    period = 3.6
    out = ['<g>' + fade_anim]
    for i in range(3):
        out.append(f'<line x1="{xs[i] + 13}" y1="{y}" x2="{xs[i + 1] - 13}" y2="{y}" stroke="{th["accent"]}" '
                   f'stroke-width="1.2" stroke-dasharray="3 4" opacity="0.7">'
                   f'<animate attributeName="stroke-dashoffset" values="14;0" dur="1.2s" repeatCount="indefinite"/></line>')
    for i, x in enumerate(xs):
        out.append(f'<rect x="{x - 11}" y="{y - 11}" width="22" height="22" transform="rotate(45 {x} {y})" fill="{th["panel0"]}" '
                   f'fill-opacity="0.6" stroke="{th["line"]}" stroke-width="1.3"/>')
        arrive = (i * 0.9) % period
        out.append(f'<rect x="{x - 4}" y="{y - 4}" width="8" height="8" transform="rotate(45 {x} {y})" fill="{th["line"]}" opacity="0.35">'
                   f'<animate attributeName="opacity" values="0.35;1;0.35;0.35" keyTimes="0;0.08;0.3;1" dur="{period}s" '
                   f'begin="{f(arrive + 1.4)}s" repeatCount="indefinite"/></rect>')
        out.append(f'<text x="{x}" y="{y + 34}" font-size="10.5" font-weight="500" letter-spacing="0.6" '
                   f'text-anchor="middle" fill="{th["muted"]}">{PIPE_STEPS[i]}</text>')
    for i in range(3):
        x1, x2 = xs[i] + 13, xs[i + 1] - 13
        b0 = 1.4 + i * 0.9
        out.append(f'<rect x="-3" y="{y - 3}" width="6" height="6" fill="{th["bracket"]}" opacity="0">'
                   f'<animateTransform attributeName="transform" type="translate" values="{x1} 0;{x2} 0;{x2} 0" '
                   f'keyTimes="0;0.25;1" dur="{period}s" begin="{f(b0)}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.03;0.22;0.25;1" dur="{period}s" '
                   f'begin="{f(b0)}s" repeatCount="indefinite"/></rect>')
    out.append('</g>')
    return ''.join(out)


def heading(text, theme_name, width=None):
    """Section heading: diamond glyph + text typed once + rule that draws in after typing.

    The image is sized to its text (plus a short rule) so it stays legible when phones scale it down.
    """
    th = THEMES[theme_name]
    H = 44
    fs, ls = 20, 0.4
    adv = ADV * fs + ls
    x0, base = 34, 29
    n = len(text)
    if width is None:
        width = int(math.ceil(x0 + n * adv + 22 + 160))
    start, per = 0.25, 0.055
    t_end = start + n * per
    full = n * adv
    css = font_css({600: text})
    times = [0.0] + [start + k * per for k in range(1, n + 1)]
    widths = [0.0] + [k * adv for k in range(1, n + 1)]
    cur_x = [x0 + w + 3 for w in widths]
    line_x1 = x0 + full + 22
    blink = [0.0, t_end + 0.45, t_end + 0.9, t_end + 1.35, t_end + 1.8, t_end + 2.25, t_end + 2.7]
    blink_v = [1, 0, 1, 0, 1, 0, 0]
    total_blink = blink[-1] + 0.01
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{H}" viewBox="0 0 {width} {H}" role="img" aria-labelledby="t">',
         f'<title id="t">{escape(text)}</title>',
         f'<style>{css}text{{font-family:\'FC\',ui-monospace,monospace}}</style>',
         '<defs>',
         f'<linearGradient id="r" gradientUnits="userSpaceOnUse" x1="{f(line_x1)}" y1="0" x2="{width - 6}" y2="0"><stop offset="0" stop-color="{th["accent"]}" stop-opacity="0.85"/>'
         f'<stop offset="1" stop-color="{th["accent"]}" stop-opacity="0"/></linearGradient>',
         f'<clipPath id="c"><rect x="{x0 - 2}" y="0" width="{f(full + 4)}" height="{H}">'
         + discrete([0.0] + [w + 4 for w in widths[1:]], times, t_end + 0.01, repeat=None) + '</rect></clipPath>',
         '</defs>']
    # glyph
    gx, gy = 14, 22
    p.append(f'<rect x="{gx - 7}" y="{gy - 7}" width="14" height="14" transform="rotate(45 {gx} {gy})" fill="none" stroke="{th["heading"]}" stroke-width="1.6"/>')
    p.append(f'<rect x="{gx - 3}" y="{gy - 3}" width="6" height="6" transform="rotate(45 {gx} {gy})" fill="{th["heading"]}">'
             '<animate attributeName="opacity" values="1;0.3;1" dur="2.6s" repeatCount="indefinite"/></rect>')
    p.append(f'<text x="{x0}" y="{base}" font-size="{fs}" font-weight="600" letter-spacing="{ls}" fill="{th["heading"]}" clip-path="url(#c)">{escape(text)}</text>')
    p.append(f'<rect x="{f(x0 + full + 3)}" y="{base - 17}" width="10" height="21" fill="{th["line"]}" opacity="0">'
             + discrete(cur_x, times, t_end + 0.01, attr='x', repeat=None)
             + discrete(blink_v, blink, total_blink, attr='opacity', repeat=None) + '</rect>')
    a = t_end / (t_end + 0.7)
    p.append(f'<line x1="{f(line_x1)}" y1="{base - 7}" x2="{width - 6}" y2="{base - 7}" stroke="url(#r)" stroke-width="1.3">'
             f'<animate attributeName="x2" values="{f(line_x1)};{f(line_x1)};{width - 6}" keyTimes="0;{f(a)};1" '
             f'calcMode="spline" keySplines="0 0 1 1;0.2 0.8 0.2 1" dur="{f(t_end + 0.7)}s" fill="freeze"/></line>')
    p.append('</svg>')
    return ''.join(p)


def chips(items, theme_name):
    """Row of chamfered skill chips that settle in one by one, with a periodic light sweep."""
    th = THEMES[theme_name]
    fs = 15
    h, gap, pad = 36, 12, 14
    widths = [pad + 8 + 10 + tw(t, fs) + pad for t in items]
    W = int(math.ceil(sum(widths) + gap * (len(items) - 1) + 4))
    H = h + 10
    css = font_css({500: ''.join(items)})
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">',
         f'<title id="t">{escape(", ".join(items))}</title>',
         f'<style>{css}text{{font-family:\'FC\',ui-monospace,monospace}}</style>']
    x = 2
    shapes = []
    for w in widths:
        shapes.append(chamfer_path(x, 5, w, h, 8))
        x += w + gap
    sweep_col = '#ffffff' if theme_name == 'dark' else th['accent']
    sweep_op = '0.16' if theme_name == 'dark' else '0.14'
    p.append('<defs><clipPath id="u">' + ''.join(f'<path d="{d}"/>' for d in shapes) + '</clipPath>'
             f'<linearGradient id="sw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{sweep_col}" stop-opacity="0"/>'
             f'<stop offset="0.5" stop-color="{sweep_col}" stop-opacity="1"/><stop offset="1" stop-color="{sweep_col}" stop-opacity="0"/></linearGradient></defs>')
    x = 2
    for i, (t, w) in enumerate(zip(items, widths)):
        b = 0.15 + i * 0.12
        tot = b + 0.45
        a = b / tot
        p.append(f'<g opacity="1">'
                 f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{f(a)};1" dur="{f(tot)}s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="translate" values="0 7;0 7;0 0" keyTimes="0;{f(a)};1" '
                 f'calcMode="spline" keySplines="0 0 1 1;0.2 0.8 0.2 1" dur="{f(tot)}s" fill="freeze"/>')
        p.append(f'<path d="{shapes[i]}" fill="{th["chip_fill"]}" fill-opacity="0.9" stroke="{th["line"]}" stroke-width="1.2" stroke-opacity="0.8"/>')
        gx, gy = x + pad + 4, 5 + h / 2
        p.append(f'<rect x="{f(gx - 3.2)}" y="{f(gy - 3.2)}" width="6.4" height="6.4" transform="rotate(45 {f(gx)} {f(gy)})" fill="{th["accent"]}"/>')
        p.append(f'<text x="{f(x + pad + 18)}" y="{f(5 + h / 2 + 5.2)}" font-size="{fs}" font-weight="500" fill="{th["chip_text"]}">{escape(t)}</text>')
        p.append('</g>')
        x += w + gap
    p.append(f'<g clip-path="url(#u)"><rect x="-80" y="0" width="70" height="{H}" fill="url(#sw)" opacity="{sweep_op}">'
             f'<animateTransform attributeName="transform" type="translate" values="0 0;{W + 160} 0;{W + 160} 0" keyTimes="0;0.3;1" '
             f'dur="7s" begin="1.2s" repeatCount="indefinite"/></rect></g>')
    p.append('</svg>')
    return ''.join(p)


def button(label, value, theme_name):
    """Two-part link button: filled label segment + outlined value segment with an arrow."""
    th = THEMES[theme_name]
    h = 40
    fs_l, fs_v = 13.5, 14
    lw = 16 + tw(label, fs_l, 0.6) + 16
    vw = (14 + tw(value, fs_v) + 12 + 12 + 10) if value else 0
    arrow_only = not value
    if arrow_only:
        lw += 22
    W = int(math.ceil(lw + vw + 4))
    H = h + 4
    css = font_css({600: label, 500: value or ''})
    alt = label + (f' {value}' if value else '')
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">',
         f'<title id="t">{escape(alt)}</title>',
         f'<style>{css}text{{font-family:\'FC\',ui-monospace,monospace}}</style>']
    outer = chamfer_path(2, 2, lw + vw, h, 9)
    p.append(f'<defs><clipPath id="o"><path d="{outer}"/></clipPath></defs>')
    p.append(f'<g clip-path="url(#o)"><rect x="0" y="0" width="{f(lw + 2)}" height="{H}" fill="{th["btn_fill"]}"/>'
             f'<rect x="{f(lw + 2)}" y="0" width="{f(vw + 2)}" height="{H}" fill="{th["chip_fill"]}" fill-opacity="0.9"/></g>')
    p.append(f'<path d="{outer}" fill="none" stroke="{th["line"]}" stroke-width="1.3"/>')
    p.append(f'<text x="18" y="{2 + h / 2 + 4.8}" font-size="{fs_l}" font-weight="600" letter-spacing="0.6" fill="{th["btn_text"]}">{escape(label)}</text>')

    def arrow(cx, cy, col):
        return (f'<path d="M{f(cx - 4.5)} {f(cy + 4.5)}L{f(cx + 4.5)} {f(cy - 4.5)}M{f(cx - 2)} {f(cy - 4.5)}H{f(cx + 4.5)}V{f(cy + 2)}" '
                f'fill="none" stroke="{col}" stroke-width="1.7" stroke-linecap="square"/>')
    if value:
        p.append(f'<text x="{f(lw + 16)}" y="{2 + h / 2 + 5}" font-size="{fs_v}" font-weight="500" fill="{th["chip_text"]}">{escape(value)}</text>')
        p.append(arrow(lw + vw - 14, 2 + h / 2, th['line']))
    else:
        p.append(arrow(lw - 18, 2 + h / 2, th['btn_text']))
    p.append('</svg>')
    return ''.join(p)


import hashlib
import re as _re


def uniq(svg):
    """Prefix every id (and its references) with a per-file hash so inlined copies never collide."""
    pre = 'b' + hashlib.md5(svg.encode()).hexdigest()[:6] + '-'
    ids = set(_re.findall(r'id="([^"]+)"', svg))
    for i in sorted(ids, key=len, reverse=True):
        svg = svg.replace(f'id="{i}"', f'id="{pre}{i}"').replace(f'url(#{i})', f'url(#{pre}{i})') \
                 .replace(f'aria-labelledby="{i}"', f'aria-labelledby="{pre}{i}"')
    return svg


def project_card(theme_name):
    """SafeShelf Tembisa card: title, one-liner, stack and a small animated truck-to-shelf scene."""
    th = THEMES[theme_name]
    W, H = 840, 210
    label, title = 'FEATURED PROJECT', 'SafeShelf Tembisa'
    sub = 'From the delivery truck to the shelf'
    stack = 'Python · SQLite · pytest · GitHub Actions'
    cta = 'View the repo'
    css = font_css({600: title, 500: label + stack + cta, 400: sub})
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">',
         '<title id="t">SafeShelf Tembisa: tracking food from the delivery truck to the shelf. View the repository.</title>',
         f"<style>{css}text{{font-family:'FC',ui-monospace,monospace}}</style>",
         '<defs>',
         f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{th["panel0"]}"/><stop offset="1" stop-color="{th["panel1"]}"/></linearGradient>',
         f'<radialGradient id="gl" cx="0.8" cy="0.3" r="0.6"><stop offset="0" stop-color="{th["glow"]}" stop-opacity="0.38"/><stop offset="1" stop-color="{th["glow"]}" stop-opacity="0"/></radialGradient>',
         f'<linearGradient id="nm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{th["name0"]}"/><stop offset="1" stop-color="{th["name2"]}"/></linearGradient>',
         f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>',
         '</defs>',
         f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#gl)"/></g>']
    p.append(f'<path d="{chamfer_path(14, 14, W - 28, H - 28, 10)}" fill="none" stroke="{th["line"]}" stroke-width="1.2" stroke-opacity="0.7"/>')
    for (cx, cy, dx, dy) in [(10, 10, 1, 1), (W - 10, 10, -1, 1), (10, H - 10, 1, -1), (W - 10, H - 10, -1, -1)]:
        p.append(f'<path d="M{cx} {cy + dy * 14}V{cy}H{cx + dx * 14}" fill="none" stroke="{th["bracket"]}" stroke-width="2.2"/>')
    p.append(f'<text x="38" y="48" font-size="10.5" font-weight="500" letter-spacing="3" fill="{th["label"]}">{label}</text>')
    p.append(f'<text x="38" y="88" font-size="28" font-weight="600" fill="url(#nm)">{title}</text>')
    p.append(f'<text x="38" y="115" font-size="14.5" font-weight="400" fill="{th["text"]}">{escape(sub)}</text>')
    p.append(f'<text x="38" y="141" font-size="12" font-weight="500" fill="{th["muted"]}">{escape(stack)}</text>')
    cw = 14 + tw(cta, 13) + 12 + 12 + 12
    p.append(f'<path d="{chamfer_path(38, 156, cw, 32, 7)}" fill="{th["btn_fill"]}"/>')
    p.append(f'<text x="52" y="177" font-size="13" font-weight="500" fill="{th["btn_text"]}">{cta}</text>')
    ax, ay = 38 + cw - 18, 172
    p.append(f'<path d="M{f(ax - 4.5)} {f(ay + 4.5)}L{f(ax + 4.5)} {f(ay - 4.5)}M{f(ax - 2)} {f(ay - 4.5)}H{f(ax + 4.5)}V{f(ay + 2)}" '
             f'fill="none" stroke="{th["btn_text"]}" stroke-width="1.7" stroke-linecap="square"/>')

    # truck (left of scene)
    s = th['line']
    p.append(f'<g fill="none" stroke="{s}" stroke-width="1.6" stroke-linejoin="round">'
             f'<rect x="478" y="102" width="70" height="40"/>'
             f'<path d="M548 114H568L582 128V142H548Z"/>'
             f'<path d="M556 118H566L574 128H556Z" stroke-width="1.2"/>'
             f'<circle cx="496" cy="146" r="7" fill="{th["panel0"]}"/><circle cx="566" cy="146" r="7" fill="{th["panel0"]}"/>'
             '</g>')
    p.append(f'<line x1="478" y1="155" x2="584" y2="155" stroke="{s}" stroke-width="1" opacity="0.4"/>')
    # route
    p.append(f'<line x1="594" y1="136" x2="676" y2="136" stroke="{th["accent"]}" stroke-width="1.3" stroke-dasharray="3 4">'
             '<animate attributeName="stroke-dashoffset" values="14;0" dur="1.1s" repeatCount="indefinite"/></line>')
    period = 6
    p.append(f'<rect x="-3" y="133" width="6" height="6" fill="{th["bracket"]}" opacity="0">'
             f'<animateTransform attributeName="transform" type="translate" values="596 0;674 0;674 0" keyTimes="0;0.2;1" dur="{period}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.18;0.2;1" dur="{period}s" repeatCount="indefinite"/></rect>')
    # shelf
    sx, sy, sw, sh = 690, 62, 116, 100
    p.append(f'<g fill="none" stroke="{s}" stroke-width="1.6"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}"/>'
             f'<line x1="{sx}" y1="{sy + 33}" x2="{sx + sw}" y2="{sy + 33}"/><line x1="{sx}" y1="{sy + 66}" x2="{sx + sw}" y2="{sy + 66}"/></g>')
    items = [(0, [10, 34, 58, 82]), (1, [10, 34, 58, 82]), (2, [10, 34, 58, 82])]
    flagged = (1, 58)
    for row, xs in items:
        for x in xs:
            ix, iy = sx + x, sy + row * 33 + 10
            if (row, x) == flagged:
                p.append(f'<g><animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.55;0.65;0.92;1" dur="{period}s" repeatCount="indefinite"/>'
                         f'<rect x="{ix}" y="{iy}" width="18" height="20" fill="{th["accent"]}" fill-opacity="0.25" stroke="{th["accent"]}" stroke-width="1.4">'
                         f'<animate attributeName="fill-opacity" values="0.25;0.25;0.9;0.25;0.9;0.25" keyTimes="0;0.25;0.33;0.41;0.49;0.55" dur="{period}s" repeatCount="indefinite"/></rect>'
                         f'<path d="M{ix + 5} {iy + 6}L{ix + 13} {iy + 14}M{ix + 13} {iy + 6}L{ix + 5} {iy + 14}" stroke="{th["bracket"]}" stroke-width="1.6"/></g>')
            else:
                p.append(f'<rect x="{ix}" y="{iy}" width="18" height="20" fill="{th["chip_fill"]}" stroke="{s}" stroke-width="1.1" stroke-opacity="0.75">'
                         f'<animate attributeName="stroke-opacity" values="0.75;0.75;1;0.75" keyTimes="0;0.2;0.24;0.32" dur="{period}s" repeatCount="indefinite"/></rect>')
    p.append('</svg>')
    return ''.join(p)


def pipeline_diagram(theme_name):
    """SafeShelf data flow drawn as a static SVG (GitHub's profile page can't render Mermaid)."""
    th = THEMES[theme_name]
    W, H = 900, 388
    fs, lh = 12, 15
    cw = ADV * fs

    inputs = [('Store deliveries',), ('Committee shelf', 'checks'), ('Anonymous resident', 'reports'), ('Truck trip updates',)]
    steps = ['extract', 'validate', 'clean', 'load']
    views = [('committee_view', 82), ('store_view', 170), ('community_view', 222), ('police_view', 300)]
    reports = [(('Expired food on', 'shelves'), 0), (('Suppliers delivering', 'near-expiry stock'), 0),
               (('Essentials about', 'to expire'), 1), (('Store scoreboard',), 2),
               (('Late trucks and', 'unexpected stops'), 3), (('Truck GPS: police only,', 'removed after 30 days'), 3)]
    heads = [('INPUT FILES', 10), ('PIPELINE', 215), ('DATABASE', 410), ('ROLE VIEWS', 545), ('DAILY REPORTS', 700)]
    texts = ''.join(''.join(t) for t in inputs) + ''.join(steps) + 'SQLite database' + ''.join(v for v, _ in views)
    texts += ''.join(''.join(r) for r, _ in reports) + ''.join(h for h, _ in heads)
    css = font_css({500: texts})

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">',
         '<title id="t">SafeShelf pipeline: four daily input files go through extract, validate, clean and load into a SQLite database. '
         'Four role views feed the daily reports. Truck GPS is visible to police only and removed after 30 days.</title>',
         f"<style>{css}text{{font-family:'FC',ui-monospace,monospace}}</style>",
         '<defs>',
         f'<marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         f'<path d="M0 0L8 4L0 8Z" fill="{th["line"]}"/></marker>',
         '</defs>']

    def box(x, y, w, h, lines, stroke, dashed=False, strong=False):
        d = chamfer_path(x, y, w, h, 6)
        dash = ' stroke-dasharray="5 4"' if dashed else ''
        out = [f'<path d="{d}" fill="{th["chip_fill"]}" fill-opacity="0.92" stroke="{stroke}" stroke-width="{1.6 if strong else 1.2}"{dash}/>']
        top = y + h / 2 - (len(lines) - 1) * lh / 2 + 4.2
        for i, line in enumerate(lines):
            out.append(f'<text x="{f(x + w / 2)}" y="{f(top + i * lh)}" font-size="{fs}" font-weight="500" '
                       f'text-anchor="middle" fill="{th["chip_text"]}">{escape(line)}</text>')
        return ''.join(out)

    def link(x1, y1, x2, y2, dashed=False, flow=True):
        dx = (x2 - x1) * 0.5
        d = f'M{f(x1)} {f(y1)}C{f(x1 + dx)} {f(y1)} {f(x2 - dx)} {f(y2)} {f(x2)} {f(y2)}'
        if dashed:
            return f'<path d="{d}" fill="none" stroke="{th["accent"]}" stroke-width="1.3" stroke-dasharray="2 4"/>'
        anim = ('<animate attributeName="stroke-dashoffset" values="16;0" dur="1.4s" repeatCount="indefinite"/>' if flow else '')
        return (f'<path d="{d}" fill="none" stroke="{th["line"]}" stroke-width="1.2" stroke-opacity="0.85" '
                f'stroke-dasharray="5 3" marker-end="url(#ar)">{anim}</path>')

    for label, x in heads:
        p.append(f'<text x="{x}" y="18" font-size="9.5" font-weight="500" letter-spacing="2" fill="{th["label"]}">{label}</text>')

    # inputs -> pipeline
    in_x, in_w, in_h = 10, 170, 40
    in_ys = [96, 146, 196, 246]
    for lines, cy in zip(inputs, in_ys):
        p.append(link(in_x + in_w, cy, 215, 196))
    # pipeline box with four steps
    px, py, pw, ph = 215, 126, 160, 140
    p.append(f'<path d="{chamfer_path(px, py, pw, ph, 8)}" fill="{th["chip_fill"]}" fill-opacity="0.92" stroke="{th["line"]}" stroke-width="1.6"/>')
    for i, s in enumerate(steps):
        yy = py + 30 + i * 28
        gx = px + 26
        p.append(f'<rect x="{gx - 3.5}" y="{yy - 7.5}" width="7" height="7" transform="rotate(45 {gx} {yy - 4})" fill="{th["accent"]}">'
                 f'<animate attributeName="opacity" values="0.35;1;0.35" dur="2.8s" begin="{f(i * 0.7)}s" repeatCount="indefinite"/></rect>')
        p.append(f'<text x="{gx + 14}" y="{yy}" font-size="{fs + 1}" font-weight="500" fill="{th["chip_text"]}">{s}</text>')
    p.append(link(px + pw, 196, 410, 196))
    # database cylinder
    dx_, dy_, dw, dh, ry = 410, 158, 100, 76, 9
    p.append(f'<path d="M{dx_} {dy_ + ry}V{dy_ + dh - ry}A{dw / 2} {ry} 0 0 0 {dx_ + dw} {dy_ + dh - ry}V{dy_ + ry}" '
             f'fill="{th["chip_fill"]}" fill-opacity="0.92" stroke="{th["line"]}" stroke-width="1.4"/>')
    p.append(f'<ellipse cx="{dx_ + dw / 2}" cy="{dy_ + ry}" rx="{dw / 2}" ry="{ry}" fill="{th["chip_fill"]}" stroke="{th["line"]}" stroke-width="1.4"/>')
    p.append(f'<text x="{dx_ + dw / 2}" y="{dy_ + 44}" font-size="{fs}" font-weight="500" text-anchor="middle" fill="{th["chip_text"]}">SQLite</text>')
    p.append(f'<text x="{dx_ + dw / 2}" y="{dy_ + 59}" font-size="{fs}" font-weight="500" text-anchor="middle" fill="{th["chip_text"]}">database</text>')
    # views
    vx, vw, vh = 545, 125, 34
    for name, cy in views:
        p.append(link(dx_ + dw, 196, vx, cy))
        p.append(box(vx, cy - vh / 2, vw, vh, [name], th['accent'], dashed=(name == 'police_view'), strong=True))
    # reports
    rx, rw, rh = 700, 190, 40
    r_ys = [54, 106, 170, 222, 280, 334]
    for (lines, vi), cy in zip(reports, r_ys):
        vcy = views[vi][1]
        private = lines[0].startswith('Truck GPS')
        p.append(link(vx + vw, vcy, rx, cy, dashed=private))
        p.append(box(rx, cy - rh / 2, rw, rh, list(lines), th['accent'] if private else th['line'], dashed=private))
    for lines, cy in zip(inputs, in_ys):
        p.append(box(in_x, cy - in_h / 2, in_w, in_h, list(lines), th['line']))
    p.append('</svg>')
    return ''.join(p)
