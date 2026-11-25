#!/usr/bin/env python3
"""Static checks for the site: balanced HTML tags, internal links and sitemap entries exist,
no network calls or third-party scripts. Run: python3 tools/check_site.py (exit 1 on error)."""
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://schweizer-rechner.ch'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
# Elements whose end tag may be omitted in valid HTML; we still write them closed, so check them too.
errors = []


class Checker(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.stack = []
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            if a['id'] in self.ids:
                errors.append(f'{self.path}: duplicate id "{a["id"]}"')
            self.ids.add(a['id'])
        for k in ('href', 'src'):
            if a.get(k):
                self.links.append((tag, k, a[k]))
        if tag == 'script' and a.get('src') and urlparse(a['src']).netloc:
            errors.append(f'{self.path}: external script {a["src"]}')
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            errors.append(f'{self.path}:{self.getpos()[0]}: stray </{tag}>')
            return
        open_tag, pos = self.stack.pop()
        if open_tag != tag:
            errors.append(f'{self.path}:{self.getpos()[0]}: </{tag}> closes <{open_tag}> opened at line {pos[0]}')


def resolve(url):
    """Internal URL -> file path, or None for external / special links."""
    u = urlparse(url)
    if u.scheme in ('mailto', 'data', 'tel') or url.startswith('#'):
        return None
    if u.netloc and u.netloc != urlparse(BASE).netloc:
        return None
    p = u.path
    if not p.startswith('/'):
        return 'RELATIVE'
    f = ROOT / p.lstrip('/')
    return f / 'index.html' if p.endswith('/') else f


pages = sorted(p for p in ROOT.rglob('*.html') if '.git' not in p.parts)
count_links = 0
for page in pages:
    rel = page.relative_to(ROOT)
    text = page.read_text(encoding='utf-8')
    c = Checker(rel)
    c.feed(text)
    c.close()
    for tag, pos in c.stack:
        errors.append(f'{rel}:{pos[0]}: <{tag}> never closed')
    for tag, attr, url in c.links:
        target = resolve(url)
        if target is None:
            continue
        count_links += 1
        if target == 'RELATIVE':
            errors.append(f'{rel}: relative link {url}')
        elif not target.exists():
            errors.append(f'{rel}: broken internal link {url}')
        if '#' in url and target not in (None, 'RELATIVE') and target.exists():
            frag = url.split('#', 1)[1]
            t2 = Checker(target)
            t2.feed(target.read_text(encoding='utf-8'))
            if frag and frag not in t2.ids:
                errors.append(f'{rel}: missing anchor {url}')

# Sitemap entries must exist, and every page in a language folder must be in the sitemap.
sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
locs = re.findall(r'<loc>([^<]+)</loc>', sitemap) + re.findall(r'href="([^"]+)"', sitemap)
for loc in set(locs):
    t = resolve(loc)
    if t is None or t == 'RELATIVE' or not t.exists():
        errors.append(f'sitemap.xml: {loc} does not exist')
in_map = {resolve(loc) for loc in re.findall(r'<loc>([^<]+)</loc>', sitemap)}
for page in pages:
    if page.parts[len(ROOT.parts)] in ('de', 'fr') and page not in in_map:
        errors.append(f'sitemap.xml: {page.relative_to(ROOT)} missing')

# No network calls or storage in the JavaScript.
for js in (ROOT / 'js').glob('*.js'):
    src = js.read_text(encoding='utf-8')
    for bad in ('fetch(', 'XMLHttpRequest', 'sendBeacon', 'WebSocket', 'localStorage', 'sessionStorage', 'document.cookie', 'http://', 'https://'):
        if bad in src:
            errors.append(f'{js.relative_to(ROOT)}: contains {bad}')

print(f'{len(pages)} HTML files, {count_links} internal links, {len(set(locs))} sitemap URLs checked')
if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('OK: no errors')
