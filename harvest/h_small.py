"""کتابخانه‌های کوچک: حوزه‌نت (همهٔ صفحه‌ها)، عقائدیة (همهٔ شناسه‌ها)، ویکی‌نبشته (همهٔ فهرست‌ها)"""
import re, json, html as H
from hcommon import get, writer, log, pmap, text
hz = writer('hawzah.jsonl'); links = []
for p in range(0, 40):
    r = get(f'https://hawzah.net/fa/Book/List?pN={p}')
    if not r: break
    new = [x for x in dict.fromkeys(re.findall(r'href="(/fa/Book/View/\d+/[^"]*)"', r.text)) if x not in links]
    if not new: break
    links += new
def hone(l):
    r = get('https://hawzah.net' + l, tries=3)
    if not r: return
    h = r.text
    img = re.search(r'src="(/Image/Book/[^"]+)"', h)
    hz({'id': re.search(r'View/(\d+)', l).group(1), 'h1': text((re.search(r'(?s)<h1[^>]*>(.*?)</h1>', h) or [None, ''])[1] if re.search(r'(?s)<h1[^>]*>(.*?)</h1>', h) else ''),
        'img': img.group(1) if img else '', 'txt': text(h)[:4000]})
pmap(hone, links, 6)
log('hawzah', len(links))
aq = writer('aqaed.jsonl')
def aone(i):
    r = get(f'https://dashboard.aqaed.net/api/v1/singleBooks/{i}', tries=2)
    if r is not None and r.ok:
        d = r.json().get('data')
        if d and d.get('title'): d.pop('listComments', None); d.pop('body', None); aq(d)
pmap(aone, range(9000, 10700), 8)
ws = writer('wikisource.jsonl')
API = 'https://fa.wikisource.org/w/api.php'
allp, c = [], ''
while True:
    r = get(API + '?action=query&list=allpages&apnamespace=106&aplimit=500&format=json' + (f'&apcontinue={c}' if c else ''))
    d = r.json(); allp += [p['title'] for p in d['query']['allpages']]
    c = d.get('continue', {}).get('apcontinue', '')
    if not c: break
import requests
for i in range(0, len(allp), 50):
    r = requests.post(API, data={'action': 'query', 'prop': 'revisions|imageinfo', 'rvprop': 'content', 'rvslots': 'main', 'format': 'json', 'formatversion': '2',
                                 'titles': '|'.join(allp[i:i + 50])}, timeout=120, headers={'User-Agent': 'library-miniapp'})
    for p in r.json()['query']['pages']:
        ws({'title': p['title'], 'content': (p.get('revisions') or [{}])[0].get('slots', {}).get('main', {}).get('content', '')[:3000]})
log('wikisource', len(allp))
