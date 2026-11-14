"""مكتبة الإمام موسى الكاظم: wp-json (نوع book) با جلد"""
from hcommon import get, writer, log
w = writer('kadhim.jsonl'); p = 1
while True:
    r = get(f'https://www.imamkadhim.com/wp-json/wp/v2/book?per_page=100&page={p}&_embed=1')
    if not r or not r.ok: break
    arr = r.json()
    if not arr: break
    for b in arr:
        emb = b.get('_embedded', {})
        fm = (emb.get('wp:featuredmedia') or [{}])[0]
        terms = [t.get('name') for grp in emb.get('wp:term', []) for t in grp]
        w({'id': b['id'], 'link': b['link'], 'title': b['title']['rendered'], 'acf': b.get('acf'), 'cover': fm.get('source_url'),
           'terms': terms, 'content': (b.get('content') or {}).get('rendered', '')[:3000]})
    p += 1
log('kadhim pages', p)
