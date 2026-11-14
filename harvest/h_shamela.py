"""المكتبة الشاملة: همهٔ صفحه‌های دسته (کارت هر کتاب با ناشر و چاپ)"""
import re
from hcommon import get, writer, log
w = writer('shamela.jsonl')
home = get('https://shamela.ws/').text
cats = sorted(set(re.findall(r'href="https://shamela.ws/category/(\d+)"', home)), key=int)
for c in cats:
    r = get(f'https://shamela.ws/category/{c}')
    if not r: continue
    name = re.search(r'(?s)<h1[^>]*>(.*?)</h1>', r.text)
    for blk in re.findall(r'(?s)<div class="book_item.*?</p>', r.text):
        m = re.search(r'href="https://shamela.ws/book/(\d+)">(.*?)</a>', blk)
        if not m: continue
        a = re.search(r'href="https://shamela.ws/author/(\d+)">(.*?)</a>', blk)
        des = re.search(r'(?s)<p[^>]*class="[^"]*des[^"]*"[^>]*>(.*)</p>', blk)
        w({'cat': re.sub(r'<[^>]+>|\s+', ' ', name.group(1)).strip() if name else c, 'catid': c, 'id': m.group(1), 't': m.group(2),
           'aid': a.group(1) if a else '', 'a': a.group(2) if a else '',
           'des': re.sub(r'\s*<br\s*/?>\s*', '\n', des.group(1)).strip() if des else ''})
    log('shamela cat', c)
