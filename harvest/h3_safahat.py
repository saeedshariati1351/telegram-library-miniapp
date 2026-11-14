"""هنداوی (safahat.org): فهرست صفحه‌به‌صفحه + صفحهٔ هر کتاب (نویسنده، مترجم، دسته، جلد)"""
import re
from hcommon import get, writer, log, pmap, text
w = writer('safahat.jsonl'); ids = []
for p in range(1, 400):
    r = get(f'https://www.safahat.org/books/{p}/')
    if not r or not r.ok: break
    new = [x for x in dict.fromkeys(re.findall(r'books/(\d{5,})/', r.text)) if x not in ids]
    if not new: break
    ids += new
log('safahat ids', len(ids))
def one(bid):
    r = get(f'https://www.safahat.org/books/{bid}/', tries=3)
    if not r or not r.ok: return
    h = r.text
    og = lambda k: (re.search(r'property="og:%s" content="([^"]*)"' % k, h) or [None, ''])[1]
    contrib = re.findall(r'href="(?:https://www\.safahat\.org)?/contributors/[^"]+"[^>]*>(.*?)</a>', h, re.S)
    cat = re.findall(r'href="(?:https://www\.safahat\.org)?/books/categories/[^"]+"[^>]*>(.*?)</a>', h, re.S)
    t = text(h); i = t.find('تاريخ إصدارات')
    w({'id': bid, 't': og('title'), 'img': og('image'), 'contrib': [text(x) for x in contrib][:8],
       'cat': [text(x) for x in cat][:6], 'hist': t[i:i + 300] if i >= 0 else '', 'pdf': 'تحميل بهيئة PDF' in t})
pmap(one, ids, 6)
log('safahat done', len(ids))
