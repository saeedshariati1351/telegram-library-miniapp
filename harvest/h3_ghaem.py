"""قائمیه (ghaemiyeh.com): فهرست از category-page (۲۰ کتاب در هر صفحه) + شناسنامهٔ فیپا و جلد از show-book"""
import re, html as H
from hcommon import get, writer, log, pmap, text
w = writer('ghaem.jsonl'); ids = []
miss = 0
for p in range(1, 4000):
    r = get(f'https://ghaemiyeh.com/category-page?page={p}', tries=3)
    if not r: miss += 1; continue
    new = [x for x in dict.fromkeys(re.findall(r'show-book/(\d+)', r.text)) if x not in ids]
    if not new:
        miss += 1
        if miss >= 3: break
        continue
    miss = 0; ids += new
    if p % 100 == 0: log('ghaem page', p, len(ids))
log('ghaem ids', len(ids))
F = ['سرشناسه', 'عنوان و نام پديدآور', 'عنوان و نام پدیدآور', 'مشخصات نشر', 'مشخصات ظاهری', 'شابک', 'وضعیت فهرست نویسی', 'موضوع', 'رده بندی کنگره', 'رده بندی دیویی', 'شماره کتابشناسی ملی', 'یادداشت', 'شناسه افزوده']
def one(i):
    r = get(f'https://ghaemiyeh.com/show-book/{i}', tries=3, timeout=60)
    if not r or not r.ok: return
    h = r.text
    og = lambda k: (re.search(r'property="og:%s" content="([^"]*)"' % k, h) or [None, ''])[1]
    t = text(h)
    j = t.find('سرشناسه')
    fipa = t[j:j + 2500] if j >= 0 else ''
    dl = re.findall(r'href="(https://ghaemiyeh.com/library/download/\d+)"[^>]*>(.*?)</a>', h, re.S)
    w({'id': i, 't': H.unescape(og('title')), 'img': og('image'), 'fipa': fipa,
       'dl': [[u, text(x)[:40]] for u, x in dl][:12]})
pmap(one, ids, 8)
log('ghaem done', len(ids))
