"""قائمیه (ghaemiyeh.com): فهرست کامل از مؤلفهٔ Livewire صفحهٔ موضوعات (category-page)، ۱۰۰۰ کتاب در هر درخواست"""
import re, json, html as H, time
from hcommon import S, writer, log
w = writer('ghaem_list.jsonl')
r = S.get('https://ghaemiyeh.com/category-page', timeout=60)
h = r.text
csrf = re.search(r'data-csrf="([^"]+)"', h) or re.search(r'name="csrf-token" content="([^"]+)"', h)
upd = re.search(r'data-update-uri="([^"]+)"', h)
uri = H.unescape(upd.group(1)) if upd else '/livewire/update'
if uri.startswith('/'): uri = 'https://ghaemiyeh.com' + uri
snap = None
for m in re.finditer(r'wire:snapshot="([^"]+)"', h):
    s = H.unescape(m.group(1))
    if 'components.category-page' in json.loads(s)['memo']['name']: snap = s; break
log('ghaem init', bool(csrf), uri, bool(snap))
def call(snapshot, updates, calls):
    body = {'_token': csrf.group(1), 'components': [{'snapshot': snapshot, 'updates': updates, 'calls': calls}]}
    for k in range(4):
        try:
            x = S.post(uri, json=body, headers={'X-Livewire': '1', 'Content-Type': 'application/json', 'Referer': 'https://ghaemiyeh.com/category-page'}, timeout=300)
            if x.ok: return x.json()['components'][0]['snapshot']
            log('ghaem http', x.status_code, x.text[:200])
        except Exception as e:
            log('ghaem err', e)
        time.sleep(10 * (k + 1))
def books(snapshot):
    d = json.loads(snapshot)['data']
    out = []
    def walk(x):
        if isinstance(x, dict):
            if 'id' in x and 'title' in x: out.append(x); return
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(d.get('books'))
    return out, d.get('hasMore'), d.get('page')
seen = set()
snap = call(snap, {'perPage': 1000}, [{'path': '', 'method': 'changeCategory', 'params': [48949]}])
for it in range(200):
    if not snap: break
    bs, more, page = books(snap)
    new = [b for b in bs if b['id'] not in seen]
    for b in new:
        seen.add(b['id']); w(b)
    log('ghaem page', page, len(seen), more)
    if not more or not new: break
    snap = call(snap, {'books': []}, [{'path': '', 'method': 'loadMore', 'params': []}])
    time.sleep(2)
log('ghaem total', len(seen))
