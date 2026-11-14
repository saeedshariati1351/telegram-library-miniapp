"""مکتبة الثقلین (thaqalaynlibrary.com): فهرس الكتب صفحه‌به‌صفحه (عنوان، مؤلف)"""
import re, time
from hcommon import get, writer, log, text
w = writer('thaqalayn.jsonl'); seen = set()
for p in range(1, 1000):
    r = get(f'https://thaqalaynlibrary.com/books?page={p}')
    if not r or not r.ok: break
    items = re.findall(r'<li><a href="/book/(\d+)">(.*?)</a>(?:\s*—\s*(.*?))?</li>', r.text, re.S)
    new = [x for x in items if x[0] not in seen]
    if not new: break
    for i, t, a in new:
        seen.add(i); w({'id': i, 't': text(t), 'a': text(a or '')})
    time.sleep(0.5)
log('thaqalayn', len(seen))
cat = get('https://thaqalaynlibrary.com/books')
cats = sorted(set(re.findall(r'href="/books\?category=([^"]+)"', cat.text))) if cat else []
cw = writer('thaqalayn_cats.jsonl')
import urllib.parse
for c in cats:
    for p in range(1, 400):
        r = get(f'https://thaqalaynlibrary.com/books?category={c}&page={p}')
        if not r or not r.ok: break
        ids = re.findall(r'<li><a href="/book/(\d+)">', r.text)
        if not ids: break
        cw({'cat': urllib.parse.unquote_plus(c), 'p': p, 'ids': ids})
        time.sleep(0.3)
log('thaqalayn cats', len(cats))
