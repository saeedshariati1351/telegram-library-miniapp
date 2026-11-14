"""HathiTrust (هاتی‌فایل؛ فارسی/عربی، دسترسی آزاد)، Gallica (SRU؛ فارسی/عربی، آزاد)، Google Books (کتاب‌های رایگان فارسی/عربی)"""
import re, json, gzip, io, time, requests
from hcommon import get, writer, log, OUT
# --- HathiTrust
try:
    fl = requests.get('https://www.hathitrust.org/files/hathifiles/hathi_file_list.json', timeout=60).json()
    full = sorted([f for f in fl if f['full']], key=lambda f: f['filename'])[-1]
    log('hathi file', full['filename'], full.get('size'))
    w = writer('hathitrust.jsonl'); n = 0
    with requests.get(full['url'], stream=True, timeout=600) as r:
        g = gzip.GzipFile(fileobj=r.raw)
        for line in io.TextIOWrapper(g, encoding='utf-8', errors='replace'):
            c = line.rstrip('\n').split('\t')
            if len(c) < 26 or c[18] not in ('per', 'ara') or c[1] != 'allow': continue
            w({'htid': c[0], 'rights': c[2], 'bib': c[3], 'desc': c[4], 'isbn': c[8], 'title': c[11], 'imprint': c[12], 'date': c[16], 'lang': c[18], 'author': c[25]})
            n += 1
    log('hathi rows', n)
except Exception as e:
    log('hathi ERR', e)
# --- Gallica SRU
w = writer('gallica.jsonl')
for lang in ('ara', 'per'):
    start = 1; total = None
    while True:
        q = f'(dc.language all "{lang}") and (dc.type all "monographie")'
        r = get('https://gallica.bnf.fr/SRU', params={'operation': 'searchRetrieve', 'version': '1.2', 'query': q, 'maximumRecords': 50, 'startRecord': start}, tries=4, timeout=120)
        if not r or not r.ok: log('gallica ERR', lang, start); break
        x = r.text
        if total is None:
            m = re.search(r'<srw:numberOfRecords>(\d+)', x); total = int(m.group(1)) if m else 0; log('gallica', lang, total)
        recs = re.findall(r'(?s)<srw:record>(.*?)</srw:record>', x)
        if not recs: break
        for rec in recs:
            d = {}
            for k, v in re.findall(r'(?s)<dc:(\w+)[^>]*>(.*?)</dc:\1>', rec): d.setdefault(k, []).append(re.sub(r'\s+', ' ', v).strip())
            d['lang'] = lang; w(d)
        start += len(recs)
        if start > total or start > 20000: break
        time.sleep(1)
# --- Google Books (free ebooks)
w = writer('googlebooks.jsonl'); seen = set()
QS = {'ar': ['كتاب', 'تاريخ', 'ديوان', 'شرح', 'فقه', 'تفسير', 'حديث', 'رسالة', 'أدب', 'شعر', 'العرب', 'الإسلام', 'مختصر', 'كشف', 'الفوائد', 'مجموعة', 'قصة', 'رحلة', 'لغة', 'نحو'],
      'fa': ['کتاب', 'تاریخ', 'دیوان', 'شرح', 'ایران', 'فارسی', 'رساله', 'شعر', 'تذکره', 'سفرنامه', 'مجموعه', 'داستان', 'فرهنگ', 'نامه', 'کلیات']}
for lang, qs in QS.items():
    for q in qs:
        for si in range(0, 400, 40):
            r = get('https://www.googleapis.com/books/v1/volumes', params={'q': q, 'filter': 'free-ebooks', 'langRestrict': lang, 'maxResults': 40, 'startIndex': si, 'printType': 'books'}, tries=3)
            if not r or not r.ok: break
            items = r.json().get('items') or []
            if not items: break
            for it in items:
                if it['id'] in seen: continue
                seen.add(it['id']); v = it.get('volumeInfo', {}); a = it.get('accessInfo', {})
                if a.get('viewability') != 'ALL_PAGES': continue
                w({'id': it['id'], 't': v.get('title'), 'st': v.get('subtitle'), 'a': v.get('authors'), 'pub': v.get('publisher'), 'y': v.get('publishedDate'),
                   'pg': v.get('pageCount'), 'lang': v.get('language'), 'img': (v.get('imageLinks') or {}).get('thumbnail'), 'link': v.get('canonicalVolumeLink') or v.get('infoLink'),
                   'cat': v.get('categories'), 'pdf': (a.get('pdf') or {}).get('isAvailable')})
            time.sleep(1)
log('google', len(seen))
