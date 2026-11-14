"""هنداوی/صفحات: فهرست صفحه‌به‌صفحه + صفحهٔ هر کتاب"""
import re
from hcommon import get, writer, log, pmap, text
w = writer('safahat.jsonl'); ids = []
for p in range(1, 400):
    r = get(f'https://www.safahat.org/books/{p}/')
    if not r or not r.ok: break
    new = [x for x in dict.fromkeys(re.findall(r'href="/books/(\d{6,})/"', r.text)) if x not in ids]
    if not new: break
    ids += new
log('safahat ids', len(ids))
def one(bid):
    r = get(f'https://www.safahat.org/books/{bid}/', tries=3)
    if not r or not r.ok: return
    h = r.text
    t = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    au = re.findall(r'href="/contributors/[^"]+"[^>]*>(.*?)</a>', h)
    cat = re.findall(r'href="/books/categories/[^"]+"[^>]*>(.*?)</a>', h)
    og = re.search(r'property="og:image" content="([^"]+)"', h)
    desc = re.search(r'name="description" content="([^"]*)"', h)
    body = text(re.search(r'(?is)<body.*', h).group(0))
    i = body.find('تاريخ'); 
    w({'id': bid, 't': text(t.group(1)) if t else '', 'au': [text(x) for x in au][:6], 'cat': [text(x) for x in cat][:4],
       'og': og.group(1) if og else '', 'desc': desc.group(1) if desc else '', 'txt': body[:1500]})
pmap(one, ids, 6)
