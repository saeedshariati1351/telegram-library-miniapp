"""إسلام‌ويب المكتبة: فهرست موضوع‌ها و کتاب‌ها (صفحه‌های bookslist) و بخش PDF"""
import re, os
from hcommon import get, writer, log, OUT, pmap
os.makedirs(os.path.join(OUT, 'iweb'), exist_ok=True)
r = get('https://www.islamweb.net/ar/library/index.php?page=bookslist')
open(os.path.join(OUT, 'iweb', 'bookslist.html'), 'wb').write(r.content)
subs = sorted(set(re.findall(r'href="(index\.php\?page=bookslist[^"]+)"', r.text)))
log('iweb subjects', len(subs))
def one(i_s):
    i, s = i_s
    x = get('https://www.islamweb.net/ar/library/' + s.replace('&amp;', '&'))
    if x is not None: open(os.path.join(OUT, 'iweb', f'sub{i}.html'), 'wb').write(x.content)
pmap(one, list(enumerate(subs)), 4)
for p in range(1, 60):
    x = get(f'https://www.islamweb.net/ar/library/index.php?page=pdf&pg={p}')
    if x is None: break
    open(os.path.join(OUT, 'iweb', f'pdf{p}.html'), 'wb').write(x.content)
