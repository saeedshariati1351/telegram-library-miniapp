"""کتابخانهٔ دیجیتال نور: صفحهٔ هر کتاب (schema.org Book + جعبهٔ مشخصات)؛ بازهٔ شناسه از آرگومان"""
import re, sys, json
from hcommon import get, writer, log, pmap, text
a, b = int(sys.argv[1]), int(sys.argv[2])
w = writer(f'noor_{a}.jsonl')
LAB = ['نویسنده', 'مترجم', 'محقق', 'مصحح', 'زبان', 'ناشر', 'سال نشر', 'کد کنگره', 'نمایش متنی', 'نمایش تصویری', 'تعداد جلد', 'موضوع', 'دانلود', 'معرفی کتاب', 'گفتگوی هوشمند']
def get_f(t, l):
    i = t.find(' ' + l + ' ')
    if i < 0: return ''
    r = t[i + len(l) + 2:]; e = len(r)
    for o in LAB:
        j = r.find(' ' + o + ' ')
        if 0 <= j < e: e = j
    return r[:e].strip()[:160]
def one(i):
    r = get(f'https://noorlib.ir/book/info/{i}', tries=3, timeout=45)
    if not r or not r.ok: return
    h = r.text
    m = re.search(r'(?s)<script type="application/ld\+json">(.*?)</script>', h)
    if not m: return
    try: j = json.loads(m.group(1))
    except Exception: return
    if not j.get('name'): return
    t = text(h); s = t.find('بزرگ‌نمایی تصویر کتاب'); tt = t[s:] if s >= 0 else t
    au = j.get('author') or []
    w({'id': i, 't': j['name'], 'au': [x.get('name') for x in au if isinstance(x, dict)] if isinstance(au, list) else [],
       'img': j.get('image', ''), 'lang': j.get('inLanguage'), 'free': 'مطالعه رایگان' in t, 'text': 'نمایش متنی' in tt, 'scan': 'نمایش تصویری' in tt,
       'dl': ' دانلود ' in tt[:600], **{k: get_f(tt, l) for k, l in [('a', 'نویسنده'), ('tr', 'مترجم'), ('ed', 'محقق'), ('ed2', 'مصحح'), ('lg', 'زبان'), ('pub', 'ناشر'), ('y', 'سال نشر'), ('vol', 'تعداد جلد')]}})
pmap(one, range(a, b), 8)
log('noor', a, b)
