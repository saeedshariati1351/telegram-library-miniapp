"""اوپن‌لایبرری (فارسی/عربی با متن کامل)، گوتنبرگ (فهرست CSV)، گنجور (همهٔ شاعران)، OpenITI (فراداده)"""
import json, os, re, time
from hcommon import get, writer, log, OUT
w = writer('openlibrary.jsonl')
for lang in ('per', 'ara'):
    for p in range(1, 200):
        r = get(f'https://openlibrary.org/search.json?q=language:{lang}&has_fulltext=true&ebook_access=public&limit=100&page={p}&fields=key,title,author_name,first_publish_year,publisher,language,ia,cover_i,ebook_access,subject')
        if not r: break
        docs = r.json().get('docs', [])
        if not docs: break
        for d in docs: d['_lang'] = lang; w(d)
        time.sleep(1)
    log('openlibrary', lang, p)
r = get('https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv', timeout=180)
if r: open(os.path.join(OUT, 'gutenberg_catalog.csv'), 'wb').write(r.content)
g = writer('ganjoor.jsonl')
poets = get('https://api.ganjoor.net/api/ganjoor/poets').json()
for p in poets:
    d = get(f"https://api.ganjoor.net/api/ganjoor/poet/{p['id']}?catPoems=false")
    cat = (d.json() if d else {}).get('cat') or {}
    g({'poet': p, 'children': [{'title': c.get('title'), 'fullUrl': c.get('fullUrl')} for c in cat.get('children') or []], 'root': cat.get('fullUrl')})
    time.sleep(0.2)
r = get('https://raw.githubusercontent.com/OpenITI/kitab-metadata-automation/master/releases/OpenITI_metadata_2025-1-9.csv', timeout=180)
if not r or not r.ok:
    r = get('https://raw.githubusercontent.com/OpenITI/kitab-metadata-automation/master/output/OpenITI_Github_clone_metadata_light.csv', timeout=180)
if r and r.ok: open(os.path.join(OUT, 'openiti_metadata.csv'), 'wb').write(r.content)
log('misc done')
