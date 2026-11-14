"""المكتبة الشاملة: کارت کتاب‌ها در صفحه‌های دسته (عنوان، مؤلف، شرح چاپ)"""
import re
from hcommon import get, writer, log, text
w = writer('shamela.jsonl')
home = get('https://shamela.ws/').text
cats = sorted(set(re.findall(r'shamela\.ws/category/(\d+)', home)), key=int) or [str(i) for i in range(1, 41)]
n = 0
for c in cats:
    r = get(f'https://shamela.ws/category/{c}')
    if not r: continue
    name = re.search(r'(?s)<h1[^>]*>(.*?)</h1>', r.text)
    for blk in re.findall(r'(?s)<div class="book_item.*?</div>', r.text):
        m = re.search(r'href="https://shamela\.ws/book/(\d+)"[^>]*>(.*?)</a>', blk)
        if not m: continue
        a = re.search(r'href="https://shamela\.ws/author/(\d+)"[^>]*>(.*?)</a>', blk)
        des = re.search(r'(?s)<p[^>]*class="[^"]*des[^"]*"[^>]*>(.*?)</p>', blk)
        w({'cat': text(name.group(1)) if name else c, 'catid': c, 'id': m.group(1), 't': text(m.group(2)),
           'aid': a.group(1) if a else '', 'a': text(a.group(2)) if a else '',
           'des': re.sub(r'<[^>]+>', '', re.sub(r'\s*<br\s*/?>\s*', '\n', des.group(1))).strip() if des else ''})
        n += 1
    log('shamela cat', c, n)
