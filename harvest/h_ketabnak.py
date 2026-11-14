"""کتابناک: نقشهٔ سایت کتاب‌ها و تصاویر + صفحهٔ هر کتاب (نویسنده، مترجم، ناشر، دسته)"""
import re
from hcommon import get, writer, log, pmap, text
w = writer('ketabnak.jsonl')
idx = get('https://www.ketabnak.com/sitemap.xml').text
maps = re.findall(r'<loc>([^<]+)</loc>', idx)
imgs = {}
for m in maps:
    if 'images-books' in m:
        x = get(m).text
        for u, img in re.findall(r'<loc>(https://www.ketabnak.com/book/[^<]+)</loc>\s*<image:image>\s*<image:loc>([^<]+)</image:loc>', x):
            imgs[re.search(r'/book/(\d+)', u).group(1)] = img
urls = []
for m in maps:
    if 'sitemap-books' in m:
        urls += re.findall(r'<loc>(https://www.ketabnak.com/book/[^<]+)</loc>', get(m).text)
log('ketabnak urls', len(urls), 'imgs', len(imgs))
def one(u):
    bid = re.search(r'/book/(\d+)', u).group(1)
    r = get(u, tries=3)
    if not r or not r.ok: return
    h = r.text
    title = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    meta = {}
    for k, v in re.findall(r'(?s)<(?:span|div|li)[^>]*class="[^"]*(?:label|key|title)[^"]*"[^>]*>\s*([^<]{2,30}?)\s*:?\s*</(?:span|div|li)>\s*<[^>]+>(.*?)</', h):
        meta[text(k)] = text(v)
    t = text(re.search(r'(?is)<body.*', h).group(0))
    i = t.find('نویسنده')
    w({'id': bid, 'url': u, 't': text(title.group(1)) if title else '', 'img': imgs.get(bid, ''), 'meta': meta, 'txt': t[max(0, i - 400): i + 1200]})
pmap(one, urls, 6)
log('ketabnak done')
