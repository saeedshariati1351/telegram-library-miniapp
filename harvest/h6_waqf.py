"""وقفیه: فهرست کامل از پشتیبان (waqfeya-backend …/books?page=&pageSize=)"""
import json
from hcommon import get, writer, log
B = 'https://waqfeya-backend-r9rw8.ondigitalocean.app'
w = writer('waqfeya.jsonl')
def arr(j):
    if isinstance(j, list): return j
    if isinstance(j, dict):
        for k in ('books', 'data', 'items', 'results', 'docs'):
            v = j.get(k)
            if isinstance(v, list): return v
            if isinstance(v, dict):
                a = arr(v)
                if a: return a
    return []
ep = None
for e in ['/books?page={p}&pageSize=100', '/book?page={p}&pageSize=100', '/books/search?page={p}&pageSize=100', '/books/all?page={p}&pageSize=100', '/api/books?page={p}&pageSize=100']:
    r = get(B + e.format(p=1), tries=2)
    log('try', e, r.status_code if r is not None else None, (r.text[:300] if r is not None else ''))
    if r is not None and r.ok:
        try:
            a = arr(r.json())
            if a: ep = e; break
        except Exception: pass
seen = set()
if ep:
    for p in range(1, 400):
        r = get(B + ep.format(p=p), tries=4)
        if not r or not r.ok: log('stop', p); break
        a = arr(r.json())
        new = [b for b in a if (b.get('_id') or b.get('id')) not in seen]
        for b in new: seen.add(b.get('_id') or b.get('id')); w(b)
        if not new: break
log('waqfeya', ep, len(seen))
