"""قائمیه: آزمون روش فهرست (جست‌وجوی multi، دسته‌ها) + برداشت انبوه با جست‌وجوی حروف"""
import re, json, os
from hcommon import get, writer, log, OUT, pmap
os.makedirs(os.path.join(OUT, 'ghaem_probe'), exist_ok=True)
B = 'https://ghaemiyeh.com/index.php/library/search/multi'
for name, q in [('empty', ''), ('star', '*'), ('alef_p2', 'ا&page=2'), ('alef_size', 'ا&per_page=100'), ('alef', 'ا')]:
    r = get(f'{B}?q={q}')
    open(os.path.join(OUT, 'ghaem_probe', name + '.json'), 'wb').write(r.content if r is not None else b'')
r = get('https://ghaemiyeh.com/category-page?page=2')
open(os.path.join(OUT, 'ghaem_probe', 'catpage2.html'), 'wb').write(r.content if r is not None else b'')
# brute: show-book ids in the observed range (sparse); sample density first
w = writer('ghaem_probe_ids.jsonl')
def one(i):
    r = get(f'https://ghaemiyeh.com/show-book/{i}', tries=2, timeout=30)
    w({'id': i, 'st': r.status_code if r is not None else 0})
pmap(one, range(682000, 683000, 7), 6)
