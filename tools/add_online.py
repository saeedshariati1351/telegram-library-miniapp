#!/usr/bin/env python3
"""افزودن کتاب‌های کتابخانه‌های آنلاین (نسخهٔ ۴) به داده‌های ساخته‌شدهٔ مینی‌اپ.

    python3 tools/add_online.py merged.xlsx data/ ../telegram-library-search/s/

ورودی فایل ادغام‌شدهٔ نسخهٔ ۴ است (merge.py) با همان ستون‌های فهرست تلگرامی؛ «نام کانال» نام کتابخانه
و «لینک تلگرامی PDF» پیوند وب کتاب است. داده‌های موجود بازسازی نمی‌شوند؛ فقط افزوده می‌شوند:

  - هر کتابخانه یک «کانال» تازه در home.json با web: 1 (و پیوند صفحهٔ اصلی کتابخانه)
  - کتابی که دقیقاً با یک کتاب تلگرامی هم‌کلید باشد (عنوان، جلد، پدیدآور، مترجم) نسخهٔ دیگرِ همان کتاب
    می‌شود؛ بقیه کتاب تازه با شناسهٔ پس از آخرین کتاب موجود
  - صفحه‌های کانال (c/) و دسته (k/)، صفحهٔ پدیدآوران (a/) و نمایهٔ جستجو (مخزن search) به‌روز می‌شوند
  - ردیف خلاصه یک ستون یازدهم دارد: نشانی وب جلد (اگر کتابخانه جلد داشته باشد)

اجرای دوباره روی همان داده‌ها پذیرفته نمی‌شود (home.json نشانهٔ online دارد)؛ برای به‌روزرسانی، داده‌ها را
اول با build_data.py از نو بسازید و بعد این را اجرا کنید.
"""
import json, os, re, sys, collections
from openpyxl import load_workbook

sys.path.insert(0, os.path.dirname(__file__))
from build_data import norm, fnv, dump, s, STOP  # noqa: E402

HYPER = re.compile(r'=HYPERLINK\("([^"]+)"')


def url_of(v):
    v = s(v)
    m = HYPER.match(v)
    return m.group(1) if m else v


VOLW = {'الاول': 1, 'الأول': 1, 'الثاني': 2, 'الثالث': 3, 'اول': 1, 'دوم': 2, 'سوم': 3}


def volume(v):
    """'جلد 3' / 'ج1' / 'مج2' / 'الجزء الثاني' -> '3'..؛ '4 جلد' (شمار جلدهای مجموعه) -> ('', '4 جلد')"""
    v = s(v)
    if not v: return '', ''
    if re.fullmatch(r'\d+\s*جلد', v): return '', v
    m = re.search(r'(\d+(?:\s*-\s*\d+)*)', v)
    if m: return m.group(1).replace(' ', ''), ''
    for k, n in VOLW.items():
        if k in v: return str(n), ''
    return v, ''


def category(tag, title, lib):
    t = f'{tag} {title}'.replace('‌', ' ')
    if lib == 'گنجور':
        return '8' if 'ادبیات' == tag else 'p'
    if tag == 'ادبیات داستانی': return 'f'
    if re.search(r'دیوان|ديوان|دواوين|شعر|الشعر|رباعیات|غزلیات|مثنوی', t) and not re.search(r'نقد|تاريخ|تاریخ', tag): return 'p'
    if re.search(r'فقه|حقوق|قانون|قوانين|قوانین|الفتاوى|فتاوى|الفرائض|السياسة الشرعية|مسائل فقهية|احکام|أحكام|استفتا|آیین‌نامه|آیین نامه|اعلامیه', t): return 'l'
    if re.search(r'تاریخ|التاريخ|تاريخ|السيرة|السیرة|سیره|التراجم|الأنساب|البلدان|الرحلات|شرح حال|طبقات|رجال|جغرافیا|سفرنامه|خاطرات|نفوس|سرشماری', t): return '9'
    if re.search(r'اللغة|اللغه|النحو|الصرف|المعاجم|الغريب|البلاغة|العروض|لغت|دستور زبان|فرهنگ لغت', t): return '4'
    if re.search(r'فلسفه|فلسفة|المنطق|منطق|روانشناسی|روان‌شناسی|خرد و اندیشه', t): return '1'
    if re.search(r'الطب|پزشکی|طب', tag): return '6'
    if re.search(r'عقيدة|العقيدة|العقائد|تفسير|التفسير|تفسیر|قرآن|القرآن|حديث|الحديث|السنة|الرقائق|اخلاق|عرفان|دین|کلام|مهدویت|التجويد|القراءات|الفرق|أهل البيت|اهل بیت|الشبهات|المستبصرون|تزکیه|التزكية|میراث مخطوط|اوستا|ویسپرد|اسلام', t): return '2'
    if re.search(r'ادب|الأدب|ادبیات', t): return '8'
    return 'x'


def main(xlsx, out, search_dir):
    home_path = os.path.join(out, 'home.json')
    home = json.load(open(home_path, encoding='utf-8'))
    if home.get('online'):
        sys.exit('این داده‌ها کتابخانه‌های آنلاین را دارند؛ اول build_data.py را دوباره اجرا کنید.')
    SH, PAGE, AS = home['shard'], home['page'], home['ashards']
    base = home['nworks']
    chans = home['channels']

    # --- read v4 rows
    wb = load_workbook(xlsx, read_only=True)
    ws = wb['کتاب‌ها']
    it = ws.iter_rows(values_only=True)
    hdr = [s(h) for h in next(it)]
    col = {h: i for i, h in enumerate(hdr)}
    def g(r, n): return s(r[col[n]]) if n in col else ''
    libs = {}
    for r in wb['کانال‌ها'].iter_rows(min_row=2, values_only=True):
        if r and r[1]: libs[s(r[1])] = (s(r[2]), url_of(r[3]))
    rows = [r for r in it if r and any(v is not None for v in r)]
    print('v4 rows', len(rows))

    # --- library channels
    chidx = {}
    for name, (domain, link) in libs.items():
        chidx[name] = len(chans)
        chans.append({'name': name, 'handle': domain, 'link': link, 'n': 0, 'w': 0, 'web': 1})

    # --- existing works by key (to attach a web copy to a Telegram book)
    exist = {}
    nshards = (base + SH - 1) // SH
    for n in range(nshards):
        for i, w in enumerate(json.load(open(f'{out}/w/{n}.json', encoding='utf-8'))):
            exist.setdefault('|'.join([norm(w['t']), norm(w.get('v', '')), norm(w.get('a', '')), norm(w.get('tr', ''))]), n * SH + i)
    print('existing works', len(exist))

    new, newkey, attach = [], {}, collections.defaultdict(list)
    for r in rows:
        title = g(r, 'عنوان کتاب')
        if not title: continue
        lib = g(r, 'نام کانال'); ci = chidx[lib]; chans[ci]['n'] += 1
        cover = g(r, 'تصویر جلد (لینک تلگرام)')
        c = {'ch': ci, 'l': url_of(g(r, 'لینک تلگرامی PDF')), 'sz': g(r, 'حجم فایل (MB)'), 'p': g(r, 'ناشر'),
             'y': g(r, 'سال نشر'), 'pg': g(r, 'تعداد صفحات'), 'isbn': g(r, 'شابک'), 'ed': g(r, 'نوبت چاپ'),
             'note': g(r, 'توضیحات دیگر (از کپشن)'), 'cu': cover if cover.startswith('http') else '', 'web': 1}
        c = {k: v for k, v in c.items() if v not in ('', None)}
        vol, nvol = volume(g(r, 'جلد'))
        author, tr = g(r, 'نویسنده / پدیدآورنده'), g(r, 'مترجم')
        if nvol: c['note'] = '؛ '.join(x for x in [nvol, c.get('note')] if x)
        key = '|'.join([norm(title), norm(vol), norm(author), norm(tr)])
        if key in exist:
            attach[exist[key]].append(c); continue
        if key in newkey:
            new[newkey[key]]['c'].append(c); continue
        newkey[key] = len(new)
        tag = g(r, 'موضوع / برچسب')
        w = {'t': title, 'st': g(r, 'زیرعنوان'), 'v': vol, 'a': author, 'tr': tr, 'e': g(r, 'مصحح / ویراستار / گردآورنده'),
             'tag': tag, 'lang': g(r, 'زبان'), 'c': [c], 'k': category(tag, title, lib), 'd': ''}
        new.append({k: v for k, v in w.items() if v not in ('',) or k in ('c', 'd')})
    for w in new:
        w['c'].sort(key=lambda c: (bool(c.get('cu')), len(c)), reverse=True)   # نسخهٔ دارای جلد اول
        w['y'] = w['c'][0].get('y', '')
        if w.get('k') == 'x': w['k'] = ''
        for ci in set(c['ch'] for c in w['c']): chans[ci]['w'] += 1
    for wid, cs in attach.items():
        for ci in set(c['ch'] for c in cs): chans[ci]['w'] += 1
    print('new works', len(new), 'attached to existing', sum(len(v) for v in attach.values()), 'in', len(attach))

    def lite(i, w):
        c0 = w['c'][0]
        return [i, w['t'], w.get('a', ''), w.get('tr', ''), w.get('v', ''), len(w['c']), w.get('y', ''),
                (c0.get('p') or '')[:50], w.get('k', ''), c0['ch'], c0.get('cu', '')]

    # --- work shards: attach copies, then append new works
    touched = collections.defaultdict(dict)
    for wid, cs in attach.items():
        touched[wid // SH][wid % SH] = cs
    for n, m in touched.items():
        p = f'{out}/w/{n}.json'; arr = json.load(open(p, encoding='utf-8'))
        for i, cs in m.items(): arr[i]['c'][1:1] = cs       # پس از نسخهٔ اصلی تا در فهرست نسخه‌ها دیده شود
        dump(p, arr)
    last = (base - 1) // SH
    arr = json.load(open(f'{out}/w/{last}.json', encoding='utf-8'))
    for k, w in enumerate(new):
        i = base + k
        if i // SH != last:
            dump(f'{out}/w/{last}.json', arr); last = i // SH; arr = []
        arr.append(w)
    dump(f'{out}/w/{last}.json', arr)
    lites = [lite(base + k, w) for k, w in enumerate(new)]

    # --- channel pages (new channels): new works + attached Telegram books
    per_ch = collections.defaultdict(list)
    for L, w in zip(lites, new):
        for ci in sorted(set(c['ch'] for c in w['c'])): per_ch[ci].append(L)
    for wid, cs in attach.items():
        w = json.load(open(f'{out}/w/{wid // SH}.json', encoding='utf-8'))[wid % SH]
        L = lite(wid, w); L[10] = cs[0].get('cu', '')
        for ci in set(c['ch'] for c in cs): per_ch[ci].append(L)
    for ci, ls in per_ch.items():
        for p in range(0, len(ls), PAGE): dump(f'{out}/c/{ci}/{p // PAGE}.json', ls[p:p + PAGE])

    # --- category pages: append after the existing ones
    cats = {c['k']: c for c in home['cats']}
    per_cat = collections.defaultdict(list)
    for L in lites: per_cat[L[8] or 'x'].append(L)
    for k, ls in per_cat.items():
        n0 = cats[k]['n']; p = n0 // PAGE
        path = f'{out}/k/{k}/{p}.json'
        cur = json.load(open(path, encoding='utf-8')) if n0 % PAGE and os.path.exists(path) else []
        for L in ls:
            cur.append(L)
            if len(cur) == PAGE: dump(f'{out}/k/{k}/{p}.json', cur); p += 1; cur = []
        if cur: dump(f'{out}/k/{k}/{p}.json', cur)
        cats[k]['n'] = n0 + len(ls)

    # --- authors / translators
    ash = collections.defaultdict(dict)
    for L, w in zip(lites, new):
        for fld, role in (('a', 'o'), ('tr', 'r')):
            name = w.get(fld)
            if not name: continue
            for part in re.split(r'\s*[،,؛;]\s*|\s+و\s+(?=\S+\s+\S+)', name):
                nn = norm(part)
                if len(nn) < 3: continue
                ash[fnv(nn) % AS].setdefault(nn, {'n': part.strip(), 'o': [], 'r': []})[role].append(L)
    for h, people in ash.items():
        p = f'{out}/a/{h}.json'
        d = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
        for nn, x in people.items():
            e = d.setdefault(nn, {'n': x['n'], 'o': [], 'r': [], 'no': 0, 'nr': 0})
            for role, cnt in (('o', 'no'), ('r', 'nr')):
                e[role] = (e[role] + x[role])[:400]; e[cnt] += len(x[role])
        dump(p, d)
    print('author shards touched', len(ash))

    # --- search index (only new works; attached books are already indexed)
    split = set(json.load(open(f'{search_dir}/manifest.json', encoding='utf-8'))['split'])
    shards = collections.defaultdict(lambda: collections.defaultdict(list))
    rows_for = collections.defaultdict(dict)
    for L, w in zip(lites, new):
        toks = set()
        for fld in ('t', 'st', 'a', 'tr', 'e'):
            toks.update(tk for tk in norm(w.get(fld, '')).split() if len(tk) >= 2 and tk not in STOP)
        toks.update(tk for tk in norm(w['c'][0].get('p', '')).split() if len(tk) >= 2 and tk not in STOP)
        for tk in toks:
            key = tk[:3] if tk[:2] in split and len(tk) > 2 else tk[:2]
            shards[key][tk].append(L[0]); rows_for[key][L[0]] = L
    for key, tmap in shards.items():
        p = f'{search_dir}/x' + ''.join(f'{ord(ch):x}-' for ch in key) + '.json'
        d = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {'t': {}, 'w': []}
        for tk, ids in tmap.items(): d['t'].setdefault(tk, []).extend(ids)
        d['w'].extend(rows_for[key].values())
        dump(p, d)
    print('search shards touched', len(shards))

    # --- home
    home['nworks'] = base + len(new)
    home['nfiles'] += len(rows)
    home['online'] = {'base': base, 'n': len(new), 'attached': len(attach), 'libs': [chidx[n] for n in libs]}
    dump(home_path, home)
    print('done: works', home['nworks'])


if __name__ == '__main__':
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(*sys.argv[1:])
