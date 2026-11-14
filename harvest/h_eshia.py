"""مدرسهٔ فقاهت: ۴ کتابخانه (متنی شیعه/اهل سنت، تصویری شیعه/اهل سنت) — دسته‌ها، شناسنامه، جلد"""
import re, urllib.parse
from hcommon import get, writer, pmap, log, text
SITES = ['lib.eshia.ir', 'lib.efatwa.ir', 'pdf.lib.eshia.ir', 'pdf.lib.efatwa.ir']
cats_w = writer('eshia_cats.jsonl'); shn_w = writer('eshia_shenasnameh.jsonl')
def rows(html):
    out = []
    for tr in re.findall(r'(?is)<tr[^>]*>(.*?)</tr>', html):
        m = re.search(r'href="https?://[^/"]+/(\d+)"', tr)
        if m: out.append(m.group(1))
    return out
for site in SITES:
    home = get(f'https://{site}/')
    if not home: continue
    links = set(re.findall(r'href="https?://%s/([^"/#?]+)"' % re.escape(site), home.text))
    links -= {'all', 'authors', 'help', 'advanced-search', 'activities'}
    for slug in sorted(links):
        if slug.isdigit(): continue
        r = get(f'https://{site}/{slug}')
        if not r: continue
        ids = rows(r.text)
        if len(ids) < 3: continue
        cats_w({'site': site, 'cat': urllib.parse.unquote(slug).replace('_', ' '), 'ids': ids})
    log(site, 'cats done')
# shenasnameh for the two text libraries (+ cover check)
import json
for site in SITES[:2]:
    allp = get(f'https://{site}/all')
    ids = rows(allp.text) if allp else []
    def one(bid):
        r = get(f'https://{site}/shenasnameh/{bid}', tries=3)
        t = ''
        if r and r.ok:
            body = re.search(r'(?is)<body.*', r.text)
            t = text(body.group(0) if body else r.text)
            i = t.find('شناسنامه'); t = t[max(0, i - 50): i + 2500] if i >= 0 else t[:2500]
        c = get(f'https://{site}/images/books/{bid}/01/cover.jpg', tries=2, timeout=30, stream=True)
        cv = bool(c is not None and c.ok and 'image' in c.headers.get('content-type', ''))
        if c is not None: c.close()
        shn_w({'site': site, 'id': bid, 'shn': t, 'cover': cv})
    pmap(one, ids, 8)
    log(site, 'shenasnameh done', len(ids))
