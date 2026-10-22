"""Rebuild the profile's static SVG assets: python scripts/build_assets.py"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import svgkit
from svgkit import uniq
R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
H = {'how-i-got-started': 'How I Got Started', 'featured-project': 'Featured Project: SafeShelf Tembisa',
     'languages-and-data': 'Languages & Data', 'tools-and-workflow': 'Tools & Workflow',
     'what-im-working-on': "What I'm Working On", 'outside-of-code': 'Outside of Code', 'connect-with-me': 'Connect with Me'}
for d in ('headings', 'skills', 'connect'):
    os.makedirs(f'{R}/{d}', exist_ok=True)
for th in ('dark', 'light'):
    open(f'{R}/header-{th}.svg', 'w').write(uniq(svgkit.header(th)))
    open(f'{R}/divider-{th}.svg', 'w').write(uniq(svgkit.divider(th)))
    for slug, t in H.items():
        open(f'{R}/headings/{slug}-{th}.svg', 'w').write(uniq(svgkit.heading(t, th)))
    open(f'{R}/skills/languages-{th}.svg', 'w').write(uniq(svgkit.chips(['Python', 'SQL', 'SQLite'], th)))
    open(f'{R}/skills/tools-{th}.svg', 'w').write(uniq(svgkit.chips(['Git', 'GitHub Actions', 'pytest', 'IntelliJ IDEA'], th)))
    open(f'{R}/safeshelf-card-{th}.svg', 'w').write(uniq(svgkit.project_card(th)))
    open(f'{R}/safeshelf-pipeline-{th}.svg', 'w').write(uniq(svgkit.pipeline_diagram(th)))
    buttons = {'github': ('GitHub', None), 'linkedin': ('LinkedIn', 'Connect'), 'email': ('Email', 'banelechakuma@gmail.com')}
    for i, (slug, (l, v)) in enumerate(buttons.items()):
        open(f'{R}/connect/{slug}-{th}.svg', 'w').write(uniq(svgkit.button(l, v, th, delay=i * 0.35)))
print('built')
