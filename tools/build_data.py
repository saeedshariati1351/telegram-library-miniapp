#!/usr/bin/env python3
"""ساخت داده‌های تکه‌تکهٔ مینی‌اپ از فایل اکسل فهرست کتابخانه.

    pip install openpyxl
    python3 tools/build_data.py catalog.xlsx data/

خروجی (همه JSON):
  data/home.json                 آمار، کانال‌ها، دسته‌ها، تازه‌ها، پیشنهادها
  data/w/<n>.json                جزئیات کامل کتاب‌ها، هر فایل SHARD کتاب (شناسهٔ کتاب = n*SHARD + i)
  data/s/manifest.json           کلیدهای نمایهٔ جستجو
  data/s/<prefix>.json           نمایهٔ جستجو: واژه ← شناسه‌ها، به‌همراه ردیف خلاصهٔ کتاب‌ها
  data/a/<h>.json                صفحهٔ پدیدآوران (تألیف و ترجمه) — h = FNV-1a(نام نرمال) % A_SHARDS
  data/c/<ch>/<p>.json           کتاب‌های هر کانال، صفحه‌به‌صفحه
  data/k/<cat>/<p>.json          کتاب‌های هر دسته (ردهٔ دیویی)، صفحه‌به‌صفحه
  data/qa.json                   گزارش اشکالات داده برای نسخهٔ نهایی

ردیف خلاصه (lite) = [شناسه، عنوان، پدیدآور، مترجم، جلد، تعداد نسخه، سال، ناشر، دسته، کانال اصلی]
"""
import json, os, re, sys, shutil, collections, unicodedata
from openpyxl import load_workbook

SHARD = 500          # کتاب در هر فایل جزئیات
A_SHARDS = 512       # تعداد فایل‌های پدیدآوران
PAGE = 60            # ردیف در هر صفحهٔ کانال/دسته
SEARCH_MAX = 6000    # اگر یک پیشوند دوحرفی بیش از این کتاب داشت، سه‌حرفی می‌شود

DEWEY = {'0': 'کلیات', '1': 'فلسفه و روان‌شناسی', '2': 'دین', '3': 'علوم اجتماعی', '4': 'زبان',
         '5': 'علوم پایه', '6': 'فناوری و علوم کاربردی', '7': 'هنر و سرگرمی',
         'f': 'ادبیات داستانی', 'p': 'شعر و دیوان', '8': 'ادبیات', '9': 'تاریخ و جغرافیا', 'l': 'فقه و حقوق'}
CAT_ORDER = ['f', 'p', '8', '9', '1', '2', 'l', '3', '0', '4', '5', '6', '7']
LAW_S = re.compile(r'^(فقه|اصول فقه|حقوق|قوانین|قانون|آیین دادرسی|احکام|حدود و تعزیرات|قضا|دادرسی|جرم ?شناسی)')
LAW_T = re.compile(r'(^|\s)(حقوق|فقه|فقهی|قوانین|آیین دادرسی|کیفری|جزای|جزایی|داوری تجاری|ثبت اسناد|اصول فقه|رساله توضیح المسائل|استفتائات|مکاسب|جواهر الکلام|شرح لمعه|حقوقی)(\s|$)')
LAW_NOT = re.compile(r'قانون جذب|حقوق بگیر|فقه اللغه')
LAW_CH = {'@ketabedarsihoqoq'}

def is_law(w, dw, subj, chans):
    d = (dw or '').translate(FA_DIGITS).replace(' ', '').lstrip('[')
    if re.match(r'34\d', d) or d.startswith('297/3') or d.startswith('297.3'): return True
    s0 = re.split(r'\s*--\s*', subj or '')[0].replace('\u200c', ' ').strip()
    if LAW_S.match(s0): return True
    if dw or subj: return False       # رده‌بندی معتبر دارد و حقوقی نیست
    t = norm(w['t'])
    if LAW_NOT.search(t): return False
    tag = (w.get('tag') or '').replace('\u200c', ' ')
    if LAW_T.search(t) or re.search(r'(^|[#\s،,])(حقوق|فقه)', tag): return True
    return any(chans[c['ch']]['handle'] in LAW_CH for c in w['c'])
POEM_T = re.compile(r'^(دیوان|کلیات اشعار|گزیده اشعار|منتخب اشعار|مجموعه شعر|مجموعه اشعار)|غزلیات|رباعیات|دوبیتی|مثنوی|منظومه|اشعار|شعرهای|دفتر شعر')
FIC_T = re.compile(r'(^|\s)رمان(\s|$)|مجموعه داستان|داستان کوتاه|داستان‌های کوتاه')

def lit_kind(w, dw, subj):
    """'p' شعر، 'f' داستانی، '' نامعلوم — بر پایهٔ موضوع فیپا، ردهٔ دیویی، عنوان و برچسب کپشن."""
    s0 = re.split(r'\s*--\s*', subj or '')[0].replace('\u200c', ' ')
    if re.search(r'نقد|تفسیر|تاریخ و|سرگذشتنامه|کتابشناسی|واژه‌نامه|واژه نامه', (subj or '').replace('\u200c', ' ')) and not s0.startswith('داستان'):
        return ''                      # نقد و تحقیق ادبی ← «ادبیات»
    if s0.startswith('شعر'): return 'p'
    if s0.startswith('داستان') or s0.startswith('رمان'): return 'f'
    d = (dw or '').translate(FA_DIGITS).replace(' ', '')
    m = re.match(r'\[?8فا(\d)', d)
    if m: return {'1': 'p', '3': 'f'}.get(m.group(1), '')
    m = re.match(r'\[?8([1-8])([13])(?!\d)|\[?8([1-8])([13])[/.]', d)
    if m: return 'p' if (m.group(2) or m.group(4)) == '1' else 'f'
    t = norm(w['t']); tag = (w.get('tag') or '').replace('\u200c', ' ')
    if POEM_T.search(t) or re.search(r'(^|[#\s،,])شعر', tag): return 'p'
    if FIC_T.search(t) or re.search(r'(^|[#\s،,])(رمان|داستان)', tag): return 'f'
    return ''
STOP = set('و در از به با را که این آن یک یا تا بر برای های ها the of and a an in to on for'.split())
FA_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')

def s(v):
    if v is None: return ''
    if isinstance(v, float) and v.is_integer(): v = int(v)
    return str(v).strip()

def norm(t):
    t = unicodedata.normalize('NFC', s(t)).lower()
    t = t.replace('ي', 'ی').replace('ى', 'ی').replace('ك', 'ک').replace('ۀ', 'ه').replace('ة', 'ه')
    t = re.sub('[أإآ]', 'ا', t).replace('ؤ', 'و').replace('ئ', 'ی')
    t = re.sub('[ً-ْٰٔـ]', '', t)          # اعراب، تطویل
    t = re.sub('[‌‍‎‏]', ' ', t)               # نیم‌فاصله
    t = t.translate(FA_DIGITS)
    t = re.sub(r'[^\w]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def fnv(t):
    h = 0x811c9dc5
    for b in t.encode('utf-8'):
        h ^= b; h = (h * 0x01000193) & 0xffffffff
    return h

def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))

def main(src, out):
    wb = load_workbook(src, read_only=True, data_only=True)
    sheets = [wb[n] for n in wb.sheetnames if n.startswith('کتاب‌ها')] or [wb.worksheets[0]]
    hdr = [s(h) for h in next(sheets[0].iter_rows(values_only=True))]
    col = {h: i for i, h in enumerate(hdr)}
    def g(r, name):
        i = col.get(name)
        return s(r[i]) if i is not None and i < len(r) else ''
    nrows = [0]
    def rows_iter():
        for ws in sheets:
            it = ws.iter_rows(values_only=True)
            next(it, None)                      # سرستون هر برگه
            for r in it:
                if r and any(v is not None for v in r):
                    nrows[0] += 1
                    if nrows[0] % 200000 == 0: print('  rows', nrows[0], flush=True)
                    yield r
    rows = rows_iter()

    # channels
    chans, chidx = [], {}
    if 'کانال‌ها' in wb.sheetnames:
        for r in list(wb['کانال‌ها'].iter_rows(values_only=True))[1:]:
            if not r or not r[1] or s(r[1]) == 'جمع کل' or r[0] is None: continue
            chidx[s(r[1])] = len(chans)
            link = s(r[3]) if s(r[3]).startswith('https://') else ''
            chans.append({'name': s(r[1]), 'handle': s(r[2]), 'link': link, 'n': 0, 'w': 0})

    qa = collections.Counter(); qa_ex = collections.defaultdict(list)
    def flag(k, ex):
        qa[k] += 1
        if len(qa_ex[k]) < 15: qa_ex[k].append(ex)

    works, wkey = [], {}
    for r in rows:
        title = g(r, 'عنوان کتاب')
        if not title:
            flag('بدون عنوان', g(r, 'نام فایل PDF')); continue
        vol, author, tr = g(r, 'جلد'), g(r, 'نویسنده / پدیدآورنده'), g(r, 'مترجم')
        if re.match(r'^\s*(جلد|ج\.?)\s*\d', author):
            flag('جلد در ستون نویسنده', f'{title} | {author}'); vol = vol or author; author = ''
        if re.search(r'صفحه', vol):
            flag('تعداد صفحه در ستون جلد', f'{title} | {vol}')
        ch = g(r, 'نام کانال')
        if ch not in chidx:
            chidx[ch] = len(chans); chans.append({'name': ch, 'handle': '', 'link': '', 'n': 0, 'w': 0})
        ci = chidx[ch]; chans[ci]['n'] += 1
        link = g(r, 'لینک تلگرامی PDF')
        if not link.startswith('https://t.me/'):
            flag('بدون لینک عمومی', f'{title} | {ch} | {link}'); link = ''
        match = g(r, 'وضعیت تطبیق با کتابخانه ملی')
        m = 2 if 'قطعی' in match else 1 if 'محتمل' in match else 0   # «احتمالی» = فقط عنوان
        cover = g(r, 'تصویر جلد (لینک تلگرام)')
        copy = {'ch': ci, 'l': link, 'sz': g(r, 'حجم فایل (MB)'), 'd': g(r, 'تاریخ ارسال در کانال'),
                'p': g(r, 'ناشر'), 'y': g(r, 'سال نشر'), 'pg': g(r, 'تعداد صفحات'), 'isbn': g(r, 'شابک'),
                'ed': g(r, 'نوبت چاپ'), 'note': g(r, 'توضیحات دیگر (از کپشن)'), 'm': m,
                'cv': cover if cover.startswith('https://t.me/') else ''}
        copy = {k: v for k, v in copy.items() if v not in ('', None)}
        if m >= 1 or 'احتمالی' in match:
            f = {'h': g(r, 'سرشناسه (فیپا)'), 'ta': g(r, 'عنوان و پدیدآور (فیپا)'), 'pub': g(r, 'مشخصات نشر (فیپا)'),
                 'phys': g(r, 'مشخصات ظاهری (فیپا)'), 'isbn': g(r, 'شابک (فیپا)'), 'subj': g(r, 'موضوع (فیپا)'),
                 'dw': g(r, 'رده‌بندی دیویی'), 'lc': g(r, 'رده‌بندی کنگره'), 'nl': g(r, 'شماره کتابشناسی ملی'),
                 'add': g(r, 'شناسه‌های افزوده (فیپا)'), 'orig': g(r, 'عنوان اصلی (فیپا)'), 'edn': g(r, 'وضعیت ویراست (فیپا)')}
            f = {k: v for k, v in f.items() if v}
            if f: copy['f'] = f
        key = '|'.join([norm(title), norm(vol), norm(author), norm(tr)])
        wid = wkey.get(key)
        if wid is None:
            wid = wkey[key] = len(works)
            works.append({'t': title, 'st': g(r, 'زیرعنوان'), 'v': vol, 'a': author, 'tr': tr,
                          'e': g(r, 'مصحح / ویراستار / گردآورنده'), 'tag': g(r, 'موضوع / برچسب'),
                          'lang': g(r, 'زبان'), 'c': []})
        works[wid]['c'].append(copy)

    print('rows', nrows[0]); print('works', len(works))
    # main copy, category, date
    def score(c):
        return (1 if c.get('l') else 0, c.get('m', 0) if 'f' in c else -1, len(c), c.get('d', ''))
    for w in works:
        w['c'].sort(key=score, reverse=True)
        main = w['c'][0]
        best = next((c for c in w['c'] if c.get('m', 0) >= 1 and 'f' in c), None)
        cat = ''
        if best:
            dw = best['f'].get('dw', '').translate(FA_DIGITS)
            mm = re.match(r'\[?\s*(\d)', dw)
            if mm: cat = mm.group(1)
        bf = (best or {}).get('f', {})
        if cat in ('2', '3') and is_law(w, bf.get('dw'), bf.get('subj'), chans):
            cat = 'l'
        elif cat == '' and is_law(w, '', '', chans):
            cat = 'l'
        if cat == '8':
            cat = lit_kind(w, bf.get('dw'), bf.get('subj')) or '8'
        elif cat == '':
            lk = lit_kind(w, '', '')
            if lk: cat = lk
            elif re.search(r'(^|[#\s،,])ادبیات', (w.get('tag') or '')): cat = '8'
        w['k'] = cat
        wf = (best or next((c for c in w['c'] if 'f' in c), {})).get('f')
        if wf:
            w['f'] = wf
            w['fm'] = (best or {}).get('m', 0)          # 2 قطعی، 1 محتمل، 0 احتمالی
            for c in w['c']:
                if c.get('f') == wf: del c['f']
        for c in w['c']:
            if c.get('cv') == c.get('l'): c['cv'] = 1   # جلد = پیش‌نمایش همان پست PDF
        w['d'] = max((c.get('d', '') for c in w['c']), default='')
        w['y'] = main.get('y', '')
        for k in ('st', 'v', 'a', 'tr', 'e', 'tag', 'lang'):
            if not w[k]: del w[k]
        chs = set(c['ch'] for c in w['c'])
        for ci in chs: chans[ci]['w'] += 1
        if len(w['c']) > 1 and len(chs) == 1:
            flag('نسخهٔ تکراری در یک کانال', f"{w['t']} | {chans[main['ch']]['name']} | {len(w['c'])}")

    def lite(i):
        w = works[i]; c0 = w['c'][0]
        return [i, w['t'], w.get('a', ''), w.get('tr', ''), w.get('v', ''), len(w['c']), w.get('y', ''),
                (c0.get('p') or '')[:50], w.get('k', ''), c0['ch']]

    if os.path.isdir(out):
        for d in ('w', 's', 'a', 'c', 'k'):
            shutil.rmtree(os.path.join(out, d), ignore_errors=True)

    # work shards
    for n in range(0, len(works), SHARD):
        dump(f'{out}/w/{n // SHARD}.json', works[n:n + SHARD])

    # search index
    tokens_of = []
    for w in works:
        toks = set()
        for fld in ('t', 'st', 'a', 'tr', 'e'):
            for tk in norm(w.get(fld, '')).split():
                if len(tk) >= 2 and tk not in STOP: toks.add(tk)
        for c in w['c'][:1]:
            for tk in norm(c.get('p', '')).split():
                if len(tk) >= 2 and tk not in STOP: toks.add(tk)
        tokens_of.append(toks)
    by2 = collections.defaultdict(set)
    for i, toks in enumerate(tokens_of):
        for tk in toks: by2[tk[:2]].add(i)
    shards = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, toks in enumerate(tokens_of):
        for tk in toks:
            p2 = tk[:2]
            key = p2 if len(by2[p2]) <= SEARCH_MAX or len(tk) == 2 else tk[:3]
            shards[key][tk].append(i)
    keys = []
    for key, tmap in shards.items():
        ids = set(i for v in tmap.values() for i in v)
        fname = 'x' + ''.join(f'{ord(ch):x}-' for ch in key)
        dump(f'{out}/s/{fname}.json', {'t': tmap, 'w': [lite(i) for i in sorted(ids)]})
        keys.append(key)
    split = sorted(p for p, v in by2.items() if len(v) > SEARCH_MAX)
    dump(f'{out}/s/manifest.json', {'split': split})
    print('search shards', len(keys), 'split prefixes', len(split))

    # authors / translators
    people = collections.defaultdict(lambda: {'n': '', 'o': [], 'r': []})
    for i, w in enumerate(works):
        for fld, role in (('a', 'o'), ('tr', 'r')):
            name = w.get(fld)
            if not name: continue
            for part in re.split(r'\s*[،,؛;]\s*|\s+و\s+(?=\S+\s+\S+)', name):
                nn = norm(part)
                if len(nn) < 3: continue
                p = people[nn]; p['n'] = p['n'] or part.strip(); p[role].append(i)
    ash = collections.defaultdict(dict)
    for nn, p in people.items():
        ash[fnv(nn) % A_SHARDS][nn] = {'n': p['n'], 'o': [lite(i) for i in p['o'][:400]], 'r': [lite(i) for i in p['r'][:400]],
                                       'no': len(p['o']), 'nr': len(p['r'])}
    for h, d in ash.items(): dump(f'{out}/a/{h}.json', d)
    print('people', len(people))

    # channels & categories (newest first)
    order = sorted(range(len(works)), key=lambda i: works[i]['d'], reverse=True)
    per_ch = collections.defaultdict(list); per_cat = collections.defaultdict(list)
    for i in order:
        for ci in sorted(set(c['ch'] for c in works[i]['c'])): per_ch[ci].append(i)
        per_cat[works[i]['k'] or 'x'].append(i)
    for ci, ids in per_ch.items():
        for p in range(0, len(ids), PAGE): dump(f'{out}/c/{ci}/{p // PAGE}.json', [lite(i) for i in ids[p:p + PAGE]])
    for k, ids in per_cat.items():
        for p in range(0, len(ids), PAGE): dump(f'{out}/k/{k}/{p // PAGE}.json', [lite(i) for i in ids[p:p + PAGE]])

    # home
    featured = [i for i in order if works[i]['c'][0].get('m', 0) == 2 and works[i].get('a') and works[i]['c'][0].get('l')][:60]
    cats = [{'k': k, 'name': DEWEY[k], 'n': len(per_cat.get(k, []))} for k in CAT_ORDER]
    cats.append({'k': 'x', 'name': 'بدون رده‌بندی', 'n': len(per_cat.get('x', []))})
    dump(f'{out}/home.json', {
        'sample': False, 'built': wb['راهنما و آمار']['B2'].value if 'راهنما و آمار' in wb.sheetnames else '',
        'nfiles': nrows[0], 'nworks': len(works), 'shard': SHARD, 'ashards': A_SHARDS, 'page': PAGE,
        'channels': chans, 'cats': cats, 'recent': [lite(i) for i in order[:40]],
        'featured': [lite(i) for i in featured]})
    dump(f'{out}/qa.json', {k: {'n': n, 'examples': qa_ex[k]} for k, n in qa.most_common()})
    print('qa', dict(qa))

if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
