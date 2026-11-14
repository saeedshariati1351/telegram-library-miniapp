"""شبکهٔ رافد: صفحه‌های دسته (اشیای JSON کتاب در صفحه) + صفحهٔ هر کتاب برای پیوند PDF"""
import re, json
from hcommon import get, writer, log, pmap
w = writer('rafed.jsonl'); seen = set()
OBJ = re.compile(r'\{"id":(\d+),"title":"((?:[^"\\]|\\.)*)","link":"/book/\d+","part":"([^"]*)","correction":(\d+),"author":\{"id":\d+,"title":"((?:[^"\\]|\\.)*)"[^}]*\},"image":"([^"]*)","pages":(\d+),"category":\{"id":(\d+),"title":"((?:[^"\\]|\\.)*)"')
def grab(html):
    u = html.replace('\\"', '"').replace('\\\\', '\\')
    for m in OBJ.finditer(u):
        bid = m.group(1)
        if bid in seen: continue
        seen.add(bid)
        w({'id': bid, 't': m.group(2), 'part': m.group(3), 'corr': m.group(4), 'a': m.group(5), 'img': m.group(6),
           'pages': m.group(7), 'catid': m.group(8), 'cat': m.group(9)})
home = get('https://books.rafed.net/').text
grab(home)
cats = sorted(set(re.findall(r'href="/category/(\d+)"', home)), key=int)
for c in cats:
    for page in range(1, 400):
        r = get(f'https://books.rafed.net/category/{c}?page={page}')
        if not r or not r.ok: break
        n0 = len(seen); grab(r.text)
        if len(seen) == n0: break
    log('rafed cat', c, len(seen))
# sweep ids not seen in categories
def one(i):
    if str(i) in seen: return
    r = get(f'https://books.rafed.net/view/{i}', tries=2)
    if r and r.ok: grab(r.text)
pmap(one, range(1, 4700), 8)
log('rafed total', len(seen))
