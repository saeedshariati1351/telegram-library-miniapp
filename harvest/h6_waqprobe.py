"""وقفیه: یافتن شیوهٔ صفحه‌بندی فهرست"""
import re, json
from hcommon import get, log
def first(u):
    r = get(u)
    if not r: return None, ''
    t = r.text
    m = re.findall(r'\\"_id\\":\\"([0-9a-f]{24})', t)
    return (m[:2], len(t)), t
base, h = first('https://waqfeya.net/books')
log('base', base)
for u in ['https://waqfeya.net/books?page=2', 'https://waqfeya.net/books?p=2', 'https://waqfeya.net/books/page/2', 'https://waqfeya.net/books?pageNumber=2',
          'https://waqfeya.net/books?skip=30', 'https://waqfeya.net/books?offset=30', 'https://waqfeya.net/api/books?page=2', 'https://waqfeya.net/api/books?page=2&limit=100',
          'https://api.waqfeya.net/books?page=2', 'https://waqfeya.net/books?sort=new&page=2']:
    x, _ = first(u); log(u, x)
for m in sorted(set(re.findall(r'(?:totalPages|totalCount|total|count|limit|perPage|pageSize)\\?"?:\s*\\?"?\d+', h)))[:20]: log('kv', m)
chunks = sorted(set(re.findall(r'/_next/static/chunks/[^"\\]+\.js', h)))
log('chunks', len(chunks))
for c in chunks:
    r = get('https://waqfeya.net' + c)
    if not r: continue
    for m in set(re.findall(r'["\'`](https?://[^"\'`]{5,80}|/api/[^"\'`]{1,80})["\'`]', r.text)): log('url', c[-30:], m)
    for m in set(re.findall(r'.{60}[?&]page=.{60}', r.text)): log('pg', m)
