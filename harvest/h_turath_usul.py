"""تراث (فهرست کامل JSON) و أصول (API جست‌وجو، همهٔ صفحه‌ها)"""
import json, os, time
from hcommon import get, writer, log, OUT
r = get('https://files.turath.io/data-v3.json', timeout=180)
if r: open(os.path.join(OUT, 'turath_data-v3.json'), 'wb').write(r.content)
w = writer('usul.jsonl')
p = 1
while True:
    r = get(f'https://api.usul.ai/search/books?limit=100&page={p}')
    if not r: break
    hits = r.json().get('results', {}).get('hits', [])
    if not hits: break
    for h in hits: w(h)
    p += 1; time.sleep(0.2)
log('usul pages', p)
