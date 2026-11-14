"""عقائدیة (آهسته)، حوزه‌نت (همهٔ صفحه‌ها)، ویکی‌نبشته (فهرست‌ها، با تلاش دوباره)"""
import re, json, time, requests
from hcommon import get, writer, log, pmap, text
# --- aqaed: slow, one worker
aq = writer('aqaed.jsonl')
for i in range(9900, 10600):
    r = get(f'https://dashboard.aqaed.net/api/v1/singleBooks/{i}', tries=5)
    if r is not None and r.ok:
        try:
            d = r.json().get('data')
            if d and d.get('title'): d.pop('listComments', None); d.pop('body', None); aq(d)
        except Exception: pass
    time.sleep(0.8)
log('aqaed done')
# --- hawzah
hz = writer('hawzah.jsonl'); links = []
for p in range(0, 40):
    r = get(f'https://hawzah.net/fa/Book/List?pN={p}')
    if not r: break
    new = [x for x in dict.fromkeys(re.findall(r'href="(/fa/Book/View/\d+/[^"]*)"', r.text)) if x not in links]
    if not new: break
    links += new
LAB = ['نویسنده :', 'مترجم :', 'تعداد صفحه :', 'تعداد جلد :', 'ناشر :', 'سال انتشار :', 'مکان انتشار :', 'تعداد بازدید :', 'تاریخ درج :']
def field(t, l):
    i = t.find(l)
    if i < 0: return ''
    r = t[i + len(l):]; e = len(r)
    for o in LAB:
        j = r.find(o)
        if 0 <= j < e: e = j
    return r[:e].strip()[:120]
def hone(l):
    r = get('https://hawzah.net' + l, tries=3)
    if not r: return
    h = r.text
    img = re.search(r'src="(/Image/Book/[^"]+)"', h)
    h1 = re.search(r'(?s)<h1[^>]*>(.*?)</h1>', h)
    t = text(h); n = t.find('نویسنده :'); s = t.rfind('کتاب / ', 0, n) if n > 0 else -1
    rec = {'id': re.search(r'View/(\d+)', l).group(1), 't': text(h1.group(1)) if h1 else '', 'img': img.group(1) if img else '',
           'head': t[s + 7:n].strip()[:300] if s >= 0 else ''}
    for k, lab in zip(['a', 'tr', 'pg', 'vol', 'pub', 'y', 'place'], LAB[:7]): rec[k] = field(t[s:] if s >= 0 else t, lab)
    hz(rec)
pmap(hone, links, 4)
log('hawzah', len(links))
# --- wikisource index pages (scanned books)
ws = writer('wikisource.jsonl')
API = 'https://fa.wikisource.org/w/api.php'; H = {'User-Agent': 'library-miniapp/1.0 (telegram mini app catalog)'}
allp, c = [], ''
while True:
    d = requests.get(API, params={'action': 'query', 'list': 'allpages', 'apnamespace': 106, 'aplimit': 500, 'format': 'json', **({'apcontinue': c} if c else {})}, headers=H, timeout=60).json()
    allp += [p['title'] for p in d['query']['allpages']]
    c = d.get('continue', {}).get('apcontinue', '')
    if not c: break
for i in range(0, len(allp), 50):
    for k in range(5):
        try:
            r = requests.post(API, data={'action': 'query', 'prop': 'revisions|imageinfo', 'rvprop': 'content', 'rvslots': 'main', 'iiprop': 'url|size',
                                         'iiurlwidth': 500, 'format': 'json', 'formatversion': '2', 'titles': '|'.join(allp[i:i + 50])}, headers=H, timeout=120)
            pages = r.json()['query']['pages']; break
        except Exception:
            time.sleep(5 * (k + 1)); pages = []
    for p in pages:
        ws({'title': p['title'], 'content': (p.get('revisions') or [{}])[0].get('slots', {}).get('main', {}).get('content', '')[:3000]})
    time.sleep(0.5)
log('wikisource', len(allp))
