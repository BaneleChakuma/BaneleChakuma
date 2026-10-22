"""Builds the activity card (assets/activity/*.svg) and the latest-commit line in README.md.

Runs once a day in GitHub Actions (.github/workflows/activity.yml) with the built-in
GITHUB_TOKEN and only reads public data. Run locally without a token and it writes the
"waiting for the first sync" card instead of guessing any numbers.

    python scripts/build_activity.py                     # needs GITHUB_TOKEN for real data
    python scripts/build_activity.py --fixture data.json  # render from a saved API response
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgkit import (EXPO_OUT, RADIUS, THEMES, brackets, escape, f, font_css, glass, lin, rad,  # noqa: E402
                    reveal, stage, style, svg_open, tw, uniq)

ROOT = Path(__file__).resolve().parent.parent
LOGIN = os.environ.get('GH_LOGIN', 'BaneleChakuma')
README = ROOT / 'README.md'
OUT = ROOT / 'assets' / 'activity'
START, END = '<!-- latest-commit:start -->', '<!-- latest-commit:end -->'

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name
        url
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 15) {
                nodes { oid url messageHeadline committedDate parents { totalCount } author { user { login } } }
              }
            }
          }
        }
      }
    }
  }
}
"""


def fetch(token):
    body = json.dumps({'query': QUERY, 'variables': {'login': LOGIN}}).encode()
    req = urllib.request.Request('https://api.github.com/graphql', data=body, headers={
        'Authorization': f'bearer {token}', 'User-Agent': f'{LOGIN}-profile-activity',
        'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get('errors'):
        raise SystemExit(f"GitHub API error: {payload['errors']}")
    return payload['data']['user']


def calendar_days(user):
    weeks = user['contributionsCollection']['contributionCalendar']['weeks']
    return [(d['date'], d['contributionCount']) for w in weeks for d in w['contributionDays']]


def streaks(days, today):
    """Longest run of active days, and the run that ends today (or yesterday, if today is still empty)."""
    longest = run = 0
    for _, count in days:
        run = run + 1 if count > 0 else 0
        longest = max(longest, run)
    counts = {d: c for d, c in days}
    day = today if counts.get(today.isoformat(), 0) > 0 else today - dt.timedelta(days=1)
    current = 0
    while counts.get(day.isoformat(), 0) > 0:
        current += 1
        day -= dt.timedelta(days=1)
    return current, longest


def top_languages(repos, limit=4):
    totals = {}
    for repo in repos:
        if repo['name'] == LOGIN:
            continue
        for edge in repo['languages']['edges']:
            totals[edge['node']['name']] = totals.get(edge['node']['name'], 0) + edge['size']
    grand = sum(totals.values())
    if not grand:
        return []
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    top = [(name, size / grand) for name, size in ranked[:limit]]
    rest = 1 - sum(share for _, share in top)
    if rest > 0.005:
        top.append(('Other', rest))
    return top


def latest_commit(repos):
    """Newest non-merge commit by me on a default branch, skipping this profile repo."""
    for repo in repos:
        if repo['name'] == LOGIN or not repo.get('defaultBranchRef'):
            continue
        for c in repo['defaultBranchRef']['target']['history']['nodes']:
            author = (c.get('author') or {}).get('user') or {}
            if c['parents']['totalCount'] == 1 and author.get('login') == LOGIN:
                return {'repo': repo['name'], 'repo_url': repo['url'], 'message': c['messageHeadline'],
                        'url': c['url'], 'date': c['committedDate'][:10]}
    return None


def md_escape(text):
    return re.sub(r'([\\`*_\[\]<>|#])', r'\\\1', text)


def latest_line(commit):
    day = dt.date.fromisoformat(commit['date'])
    when = f'{day.day} {day.strftime("%b %Y")}'
    return (f"**Latest commit:** [{md_escape(commit['message'])}]({commit['url']}) "
            f"in [{commit['repo']}]({commit['repo_url']}) · {when}")


def update_readme(commit):
    text = README.read_text(encoding='utf-8')
    if START not in text or END not in text or commit is None:
        return False
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    new = f'{head}{START}\n{latest_line(commit)}\n{END}{tail}'
    if new != text:
        README.write_text(new, encoding='utf-8')
        return True
    return False


LEVELS = {'dark': [('#f0abfc', 0.09), ('#701a75', 1), ('#a21caf', 1), ('#d946ef', 1), ('#f5d0fe', 1)],
          'light': [('#86198f', 0.08), ('#f5d0fe', 1), ('#e879f9', 1), ('#c026d3', 1), ('#86198f', 1)]}
LANG_COLORS = {'dark': ['#f0abfc', '#d946ef', '#a21caf', '#86198f', '#5b1a63'],
               'light': ['#86198f', '#a21caf', '#c026d3', '#e879f9', '#f5d0fe']}


def card(theme_name, stats):
    """stats: None (no data yet) or dict(total, current, longest, repos, days, langs)."""
    th = THEMES[theme_name]
    W, H = 900, 240
    pending = stats is None
    total = '—' if pending else f"{stats['total']:,}"
    current = '—' if pending else str(stats['current'])
    longest = '—' if pending else str(stats['longest'])
    repos_label = 'LAST 12 MONTHS' if pending else f"{stats['repos']} PUBLIC REPOS · LAST 12 MONTHS"
    langs = [] if pending else stats['langs']
    legend = [f'{name} {share * 100:.1f}%' for name, share in langs]
    labels = ['CONTRIBUTIONS', 'CURRENT STREAK', 'LONGEST STREAK']
    note = 'Fills in after the first daily sync' if pending else ''
    css = font_css({700: total + current + longest,
                    600: 'ACTIVITY' + ''.join(labels) + 'TOP LANGUAGES',
                    500: repos_label + 'days' + 'last 26 weeks' + ''.join(legend) + note})
    levels = LEVELS[theme_name]
    colors = LANG_COLORS[theme_name]
    px, py, pw, ph, pr = 16, 16, 868, 208, RADIUS['panel']
    x0, x1 = px + 26, px + pw - 26          # content edges: 42 .. 858
    sdefs, sbody, sedge = stage(th, W, H, key=(0.12, 0.04, 0.7), fill=(0.96, 1.05, 0.6), dots=False)
    gdefs, gbody = glass(th, px, py, pw, ph, W, H, pr)
    p = [svg_open(W, H, f'GitHub activity for {LOGIN}'), style(css), '<defs>', sdefs, gdefs,
         lin('nm', [(0, th['name0'], 1), (0.55, th['name1'], 1), (1, th['name2'], 1)], 0, 0, 0.9, 1),
         lin('dv', [(0, th['accent'], 0.75), (1, th['accent'], 0)], x0 + 91, 0, 640, 0, user=True),
         rad('hg', [(0, levels[4][0], 0.6), (1, levels[4][0], 0)]),
         '</defs>', sbody, gbody, brackets(th, px, py, pw, ph, pr)]
    p.append(f'<text x="{x0}" y="45" font-size="11" font-weight="600" letter-spacing="4" fill="{th["label"]}" '
             f'fill-opacity="{f(th["label_op"])}">ACTIVITY</text>')
    p.append(f'<line x1="{x0 + 91}" y1="41" x2="640" y2="41" stroke="url(#dv)" stroke-width="1"/>')
    p.append(f'<text x="{x1}" y="45" font-size="10.5" font-weight="500" letter-spacing="2" text-anchor="end" fill="{th["muted"]}">{escape(repos_label)}</text>')

    for i, (value, label) in enumerate(zip([total, current, longest], labels)):
        x = x0 + i * 166
        p.append('<g>' + reveal(0.2 + i * 0.12, 0.6, 8)
                 + f'<text x="{x}" y="97" font-size="34" font-weight="700" fill="url(#nm)">{escape(value)}</text>')
        if i > 0 and not pending:
            unit = 'day' if value == '1' else 'days'
            p.append(f'<text x="{f(x + tw(value, 34) + 8)}" y="97" font-size="13" font-weight="500" fill="{th["muted"]}">{unit}</text>')
        p.append(f'<text x="{x}" y="119" font-size="10.5" font-weight="600" letter-spacing="2" fill="{th["label"]}" '
                 f'fill-opacity="{f(th["label_op"])}">{label}</text></g>')

    # contribution heatmap, last 26 weeks, one column per week (Sunday on top)
    days = [] if pending else stats['days'][-26 * 7:]
    nonzero = sorted(c for _, c in days if c > 0)
    cuts = [nonzero[int(len(nonzero) * q)] for q in (0.25, 0.5, 0.75)] if nonzero else []

    def level(c):
        if c <= 0:
            return 0
        return 1 + sum(c > cut for cut in cuts)
    step, size = 12, 9
    hx, hy = x1 - (26 * step - (step - size)), 59
    first_weekday = 0
    if days:
        first_weekday = (dt.date.fromisoformat(days[0][0]).weekday() + 1) % 7  # Sunday = 0
    for col in range(26):
        p.append('<g>' + reveal(0.5 + col * 0.03, 0.35, 0))
        for row in range(7):
            idx = col * 7 + row - first_weekday
            c = days[idx][1] if days and 0 <= idx < len(days) else 0
            lv = level(c)
            color, op = levels[lv]
            cx, cy = hx + col * step, hy + row * step
            if lv == 4:
                p.append(f'<circle cx="{f(cx + size / 2)}" cy="{f(cy + size / 2)}" r="10" fill="url(#hg)"/>')
            alpha = '' if op == 1 else f' fill-opacity="{f(op)}"'
            p.append(f'<rect x="{cx}" y="{cy}" width="{size}" height="{size}" rx="{RADIUS["cell"]}" fill="{color}"{alpha}/>')
        p.append('</g>')
    p.append(f'<text x="{x1}" y="157" font-size="10" font-weight="500" text-anchor="end" fill="{th["muted"]}">last 26 weeks</text>')

    # languages
    p.append(f'<text x="{x0}" y="159" font-size="10.5" font-weight="600" letter-spacing="2" fill="{th["label"]}" '
             f'fill-opacity="{f(th["label_op"])}">TOP LANGUAGES</text>')
    bar_x, bar_w, bar_y = x0, x1 - x0, 171
    p.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="8" rx="4" fill="{levels[0][0]}" fill-opacity="{f(levels[0][1])}"/>')
    x = bar_x
    for i, (name, share) in enumerate(langs):
        w = max(bar_w * share - 2, 1.5)
        p.append(f'<rect x="{f(x)}" y="{bar_y}" width="{f(w)}" height="8" rx="{f(min(4, w / 2))}" fill="{colors[i % len(colors)]}">'
                 f'<animate attributeName="width" values="0;0;{f(w)}" keyTimes="0;0.4;1" calcMode="spline" '
                 f'keySplines="0 0 1 1;{EXPO_OUT}" dur="1.6s" fill="freeze"/></rect>')
        x += bar_w * share
    lx = x0
    for i, text in enumerate(legend):
        p.append(f'<rect x="{f(lx)}" y="194" width="9" height="9" rx="2.5" fill="{colors[i % len(colors)]}"/>')
        p.append(f'<text x="{f(lx + 15)}" y="203" font-size="12" font-weight="500" fill="{th["chip_text"]}">{escape(text)}</text>')
        lx += 15 + tw(text, 12) + 26
    if pending:
        p.append(f'<text x="{x0}" y="203" font-size="12" font-weight="500" fill="{th["muted"]}">{note}</text>')
    p.append(sedge)
    p.append('</svg>')
    return uniq(''.join(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fixture', help='JSON file holding a saved `user` object from the GraphQL API')
    ap.add_argument('--today', help='override today (YYYY-MM-DD), for tests')
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(dt.timezone.utc).date()
    token = os.environ.get('GITHUB_TOKEN')
    if args.fixture:
        user = json.loads(Path(args.fixture).read_text(encoding='utf-8'))
    elif token:
        user = fetch(token)
    else:
        user = None

    OUT.mkdir(parents=True, exist_ok=True)
    if user is None:
        stats, commit = None, None
    else:
        days = calendar_days(user)
        current, longest = streaks(days, today)
        repos = user['repositories']['nodes']
        stats = {'total': user['contributionsCollection']['contributionCalendar']['totalContributions'],
                 'current': current, 'longest': longest, 'repos': user['repositories']['totalCount'],
                 'days': days, 'langs': top_languages(repos)}
        commit = latest_commit(repos)
    for theme in ('dark', 'light'):
        (OUT / f'activity-{theme}.svg').write_text(card(theme, stats), encoding='utf-8')
    changed = update_readme(commit)
    print('activity card:', 'waiting for first sync' if stats is None else f"{stats['total']} contributions",
          '| README latest commit:', 'updated' if changed else 'unchanged')


if __name__ == '__main__':
    main()
