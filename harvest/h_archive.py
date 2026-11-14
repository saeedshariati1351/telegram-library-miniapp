"""آرشیو اینترنت: همهٔ متن‌های فارسی + متن‌های عربی پرکاربرد (scrape API)"""
import json
from hcommon import get, writer, log
w = writer('archive.jsonl')
FL = 'identifier,title,creator,date,language,subject,downloads,publisher,collection,imagecount'
def run(q, cap):
    cursor, n = None, 0
    while n < cap:
        u = f'https://archive.org/services/search/v1/scrape?fields={FL}&q={q}&count=10000' + (f'&cursor={cursor}' if cursor else '')
        r = get(u, timeout=180)
        if not r: break
        d = r.json()
        for it in d.get('items', []): w(it); n += 1
        cursor = d.get('cursor')
        if not cursor: break
    log('archive', q, n)
run('language%3A%28per%20OR%20Persian%20OR%20fas%20OR%20Farsi%29%20AND%20mediatype%3Atexts', 60000)
run('language%3A%28ara%20OR%20Arabic%29%20AND%20mediatype%3Atexts%20AND%20downloads%3A%5B300%20TO%20999999999%5D', 150000)
