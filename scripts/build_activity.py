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
from svgkit import THEMES, chamfer_path, escape, f, font_css, tw, uniq  # noqa: E402

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


LEVELS = {'dark': ['#2a0f30', '#4a044e', '#86198f', '#c026d3', '#e879f9'],
          'light': ['#f3e3f8', '#f5d0fe', '#e879f9', '#c026d3', '#86198f']}
LANG_COLORS = {'dark': ['#e879f9', '#c026d3', '#a21caf', '#86198f', '#4a044e'],
               'light': ['#86198f', '#a21caf', '#c026d3', '#e879f9', '#f5d0fe']}


def card(theme_name, stats):
    """stats: None (no data yet) or dict(total, current, longest, repos, days, langs)."""
    th = THEMES[theme_name]
    W, H = 900, 236
    pending = stats is None
    total = '—' if pending else f"{stats['total']:,}"
    current = '—' if pending else str(stats['current'])
    longest = '—' if pending else str(stats['longest'])
    repos_label = 'LAST 12 MONTHS' if pending else f"{stats['repos']} PUBLIC REPOS · LAST 12 MONTHS"
    langs = [] if pending else stats['langs']
    legend = [f'{name} {share * 100:.1f}%' for name, share in langs]
    labels = ['CONTRIBUTIONS', 'CURRENT STREAK', 'LONGEST STREAK']
    note = 'Fills in after the first daily sync' if pending else ''
    css = font_css({600: total + current + longest,
                    500: 'ACTIVITY' + ''.join(labels) + repos_label + 'TOP LANGUAGES' + 'days' + 'last 26 weeks' + ''.join(legend) + note})
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">',
         f'<title id="t">GitHub activity for {LOGIN}</title>',
         f"<style>{css}text{{font-family:'FC',ui-monospace,monospace}}</style>",
         '<defs>',
         f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{th["panel0"]}"/><stop offset="1" stop-color="{th["panel1"]}"/></linearGradient>',
         f'<radialGradient id="gl" cx="0.15" cy="0.1" r="0.7"><stop offset="0" stop-color="{th["glow"]}" stop-opacity="0.3"/><stop offset="1" stop-color="{th["glow"]}" stop-opacity="0"/></radialGradient>',
         f'<linearGradient id="nm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{th["name0"]}"/><stop offset="1" stop-color="{th["name2"]}"/></linearGradient>',
         f'<linearGradient id="dv" gradientUnits="userSpaceOnUse" x1="124" y1="0" x2="640" y2="0"><stop offset="0" stop-color="{th["accent"]}" stop-opacity="0.9"/><stop offset="1" stop-color="{th["accent"]}" stop-opacity="0"/></linearGradient>',
         f'<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>',
         '</defs>',
         f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#gl)"/></g>']
    frame = chamfer_path(20, 16, 860, 204, 12)
    p.append(f'<path d="{frame}" fill="none" stroke="{th["line"]}" stroke-width="1.2" stroke-opacity="0.7"/>')
    for (cx, cy, dx, dy) in [(16, 12, 1, 1), (884, 12, -1, 1), (16, 224, 1, -1), (884, 224, -1, -1)]:
        p.append(f'<path d="M{cx} {cy + dy * 16}V{cy}H{cx + dx * 16}" fill="none" stroke="{th["bracket"]}" stroke-width="2.2"/>')
    p.append(f'<text x="44" y="44" font-size="11" font-weight="500" letter-spacing="4" fill="{th["label"]}">ACTIVITY</text>')
    p.append('<line x1="124" y1="40" x2="640" y2="40" stroke="url(#dv)" stroke-width="1"/>')
    p.append(f'<text x="856" y="44" font-size="10.5" font-weight="500" letter-spacing="2" text-anchor="end" fill="{th["muted"]}">{escape(repos_label)}</text>')

    def appear(i):
        b = 0.2 + i * 0.12
        return (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{f(b / (b + 0.5))};1" dur="{f(b + 0.5)}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" values="0 8;0 8;0 0" keyTimes="0;{f(b / (b + 0.5))};1" '
                f'calcMode="spline" keySplines="0 0 1 1;0.2 0.8 0.2 1" dur="{f(b + 0.5)}s" fill="freeze"/>')
    for i, (value, label) in enumerate(zip([total, current, longest], labels)):
        x = 44 + i * 166
        p.append(f'<g>{appear(i)}<text x="{x}" y="96" font-size="34" font-weight="600" fill="url(#nm)">{escape(value)}</text>')
        if i > 0 and not pending:
            p.append(f'<text x="{f(x + tw(value, 34) + 8)}" y="96" font-size="13" font-weight="500" fill="{th["muted"]}">{'day' if value == '1' else 'days'}</text>')
        p.append(f'<text x="{x}" y="118" font-size="10.5" font-weight="500" letter-spacing="2" fill="{th["label"]}">{label}</text></g>')

    # contribution heatmap, last 26 weeks, one column per week (Sunday on top)
    levels = LEVELS[theme_name]
    days = [] if pending else stats['days'][-26 * 7:]
    nonzero = sorted(c for _, c in days if c > 0)
    cuts = [nonzero[int(len(nonzero) * q)] for q in (0.25, 0.5, 0.75)] if nonzero else []

    def level(c):
        if c <= 0:
            return 0
        return 1 + sum(c > cut for cut in cuts)
    x0, y0, step, size = 548, 58, 12, 9
    first_weekday = 0
    if days:
        first_weekday = (dt.date.fromisoformat(days[0][0]).weekday() + 1) % 7  # Sunday = 0
    for col in range(26):
        b = 0.5 + col * 0.03
        p.append(f'<g><animate attributeName="opacity" values="0;0;1" keyTimes="0;{f(b / (b + 0.3))};1" dur="{f(b + 0.3)}s" fill="freeze"/>')
        for row in range(7):
            idx = col * 7 + row - first_weekday
            c = days[idx][1] if days and 0 <= idx < len(days) else 0
            fill = levels[level(c)]
            p.append(f'<rect x="{x0 + col * step}" y="{y0 + row * step}" width="{size}" height="{size}" rx="1.5" fill="{fill}"/>')
        p.append('</g>')
    p.append(f'<text x="857" y="156" font-size="10" font-weight="500" text-anchor="end" fill="{th["muted"]}">last 26 weeks</text>')

    # languages
    p.append(f'<text x="44" y="158" font-size="10.5" font-weight="500" letter-spacing="2" fill="{th["label"]}">TOP LANGUAGES</text>')
    bar_x, bar_w, bar_y = 44, 812, 170
    p.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="8" rx="2" fill="{levels[0]}"/>')
    colors = LANG_COLORS[theme_name]
    x = bar_x
    for i, (name, share) in enumerate(langs):
        w = bar_w * share
        p.append(f'<rect x="{f(x)}" y="{bar_y}" width="{f(max(w - 2, 1))}" height="8" rx="1.5" fill="{colors[i % len(colors)]}">'
                 f'<animate attributeName="width" values="0;0;{f(max(w - 2, 1))}" keyTimes="0;0.4;1" calcMode="spline" '
                 f'keySplines="0 0 1 1;0.2 0.8 0.2 1" dur="1.6s" fill="freeze"/></rect>')
        x += w
    lx = 44
    for i, text in enumerate(legend):
        p.append(f'<rect x="{lx}" y="193" width="9" height="9" rx="1.5" fill="{colors[i % len(colors)]}"/>')
        p.append(f'<text x="{lx + 15}" y="202" font-size="12" font-weight="500" fill="{th["chip_text"]}">{escape(text)}</text>')
        lx += 15 + tw(text, 12) + 26
    if pending:
        p.append(f'<text x="44" y="202" font-size="12" font-weight="500" fill="{th["muted"]}">{note}</text>')
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
