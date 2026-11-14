#!/usr/bin/env python3
"""ساختن داده‌های کتابخانه‌های آنلاین (نسخهٔ ۵) در مخزنی جدا (telegram-library-online)

    python3 tools/build_online.py <پوشهٔ اکسل‌ها> data/ ../telegram-library-online/

ورودی: یک فایل اکسل برای هر کتابخانه (ستون‌های فهرست تلگرامی؛ «نام کانال» = نام کتابخانه، «لینک تلگرامی PDF» = پیوند وب).
خروجی در مخزن آنلاین (از نو ساخته می‌شود):
  home.json       کتابخانه‌ها (libs)، دسته‌ها، شمار کتاب‌ها، تقسیم نمایهٔ جستجو
  w/<n>.json      کتاب‌ها؛ شناسهٔ کتاب = OBASE + شمارهٔ ردیف (مستقل از شمار کتاب‌های تلگرامی)
  c/<li>/<p>.json فهرست کتاب‌های هر کتابخانه؛ k/<k>/<p>.json دسته‌ها؛ a/<h>.json پدیدآوران؛ s/ نمایهٔ جستجو
  attached.json   کتاب‌های تلگرامی که نسخهٔ آنلاین گرفتند
در مخزن اصلی فقط به کتاب‌های تلگرامیِ هم‌کلید (عنوان، جلد، پدیدآور، مترجم) نسخهٔ وب افزوده می‌شود؛ اجرای دوباره اول
نسخه‌های وب قبلی را برمی‌دارد. شمارهٔ کانالِ نسخهٔ وب = CH_OFF + شمارهٔ کتابخانه.
"""
import collections, glob, json, os, re, shutil, sys
from datetime import datetime
from openpyxl import load_workbook

sys.path.insert(0, os.path.dirname(__file__))
from build_data import norm, fnv, dump, s, STOP  # noqa: E402

# واژه‌های بسیار پرتکرار که در نمایهٔ آنلاین نیستند (برنامه هم آن‌ها را از پرس‌وجوی آنلاین کنار می‌گذارد: home.json → stop)
OSTOP = STOP | set('في من على عن الى ما مع او ثم لا هذا هذه التي الذي بن بنت فى كتاب the of'.split())
OBASE, CH_OFF, SHARD, PAGE, ASH, SEARCH_MAX = 2_000_000, 1000, 500, 60, 512, 6000
HYPER = re.compile(r'=HYPERLINK\("([^"]+)"')
# پیشوندهای نشانی جلد (برای کوچک‌کردن داده؛ برنامه آن‌ها را باز می‌کند: home.json → cup)
CUP = [('ia:', 'https://archive.org/services/img/'), ('ad:', 'https://archive.org/download/'), ('us:', 'https://assets.usul.ai/covers/'),
       ('nr:', 'https://noorlib.ir/file/book/cover/'), ('gh:', 'https://ghaemiyeh.com/storage/sources/28/'), ('ol:', 'https://covers.openlibrary.org/b/id/'),
       ('wm:', 'https://upload.wikimedia.org/wikipedia/commons/thumb/'), ('hd:', 'https://downloads.hindawi.org/covers/'), ('rf:', 'https://lib.rafed.net/Books/'),
       ('kd:', 'https://www.imamkadhim.com/wp-content/uploads/'), ('aq:', 'https://aqaed.net/dl/books/')]


def short_cu(u):
    for k, pre in CUP:
        if u.startswith(pre): return k + u[len(pre):]
    return u
CAT_NAMES = {'f': 'ادبیات داستانی', 'p': 'شعر و دیوان', '8': 'ادبیات', '9': 'تاریخ و جغرافیا', '1': 'فلسفه و روان‌شناسی', '2': 'دین',
             'l': 'فقه و حقوق', '3': 'علوم اجتماعی', '0': 'کلیات', '4': 'زبان', '5': 'علوم پایه', '6': 'فناوری و علوم کاربردی', '7': 'هنر و سرگرمی', 'x': 'بدون رده‌بندی'}
VOLW = {'الاول': 1, 'الأول': 1, 'الثاني': 2, 'الثالث': 3, 'اول': 1, 'دوم': 2, 'سوم': 3}


def url_of(v):
    v = s(v); m = HYPER.match(v)
    return m.group(1) if m else v


def volume(v):
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
    if lib == 'گنجور': return '8' if tag == 'ادبیات' else 'p'
    if tag == 'ادبیات داستانی' or re.search(r'رواية|روايات|قصص|novels|detective|رمان', tag): return 'f'
    if re.search(r'دیوان|ديوان|دواوين|شعر|الشعر|رباعیات|غزلیات|مثنوی|منظومة', t) and not re.search(r'نقد|تاريخ|تاریخ', tag): return 'p'
    if re.search(r'فقه|حقوق|قانون|قوانين|قوانین|الفتاوى|فتاوى|الفرائض|السياسة الشرعية|مسائل فقهية|احکام|أحكام|استفتا|أصول الفقه|اصول فقه|القضاء', t): return 'l'
    if re.search(r'تاریخ|التاريخ|تاريخ|السيرة|السیرة|سیره|التراجم|الأنساب|البلدان|الرحلات|شرح حال|طبقات|رجال|جغرافیا|سفرنامه|خاطرات|history|biograph|geograph', t, re.I): return '9'
    if re.search(r'اللغة|النحو|الصرف|المعاجم|الغريب|البلاغة|العروض|لغت|دستور زبان|فرهنگ لغت|linguistic', t, re.I): return '4'
    if re.search(r'فلسفه|فلسفة|المنطق|منطق|روانشناسی|روان‌شناسی|psycholog|philosoph', t, re.I): return '1'
    if re.search(r'الطب|پزشکی|طب|health|medic', tag, re.I): return '6'
    if re.search(r'عقيدة|العقيدة|العقائد|تفسير|التفسير|تفسیر|قرآن|القرآن|حديث|الحديث|السنة|الرقائق|اخلاق|أخلاق|عرفان|دین|کلام|الكلام|مهدویت|التجويد|القراءات|الفرق|أهل البيت|اهل بیت|الشبهات|المستبصرون|تزکیه|التزكية|التصوف|الدعوة|اوستا|اسلام|الإسلام|إسلام|دعا|زیارت|الأدعية|religio', t, re.I): return '2'
    if re.search(r'اقتصاد|سیاست|السياسة|اجتماع|المجتمع|تربیت|تربية|التعليم|social|econom|politic', t, re.I): return '3'
    if re.search(r'فهرس|فهرست|کتابشناسی|ببليوغرافيا|موسوعة|دائرة المعارف', t): return '0'
    if re.search(r'علوم|ریاضی|رياضيات|فيزياء|کیمیا|science', tag, re.I): return '5'
    if re.search(r'هنر|فنون|الفن|موسیقی|arts', t, re.I): return '7'
    if re.search(r'ادب|الأدب|ادبیات|literature', t, re.I): return '8'
    return 'x'


def main(xdir, main_data, odir):
    mhome = json.load(open(os.path.join(main_data, 'home.json'), encoding='utf-8'))
    mSH = mhome['shard']

    # --- 1. strip web copies attached by an earlier run
    prev = os.path.join(odir, 'attached.json')
    if os.path.exists(prev):
        by = collections.defaultdict(list)
        for wid in json.load(open(prev, encoding='utf-8')): by[wid // mSH].append(wid % mSH)
        for n, idx in by.items():
            p = f'{main_data}/w/{n}.json'; arr = json.load(open(p, encoding='utf-8'))
            for i in idx: arr[i]['c'] = [c for c in arr[i]['c'] if not c.get('web')]
            dump(p, arr)
        print('stripped earlier web copies from', len(by), 'shards')

    # --- 2. read libraries
    libs, rows = [], []
    for f in sorted(glob.glob(os.path.join(xdir, '*.xlsx'))):
        wb = load_workbook(f, read_only=True)
        ws = wb['کتاب‌ها']; it = ws.iter_rows(values_only=True); hdr = [s(h) for h in next(it)]
        col = {h: i for i, h in enumerate(hdr)}
        ch = next(wb['کانال‌ها'].iter_rows(min_row=2, values_only=True))
        li = len(libs)
        libs.append({'name': s(ch[1]), 'handle': s(ch[2]), 'link': url_of(ch[3]), 'n': 0, 'w': 0, 'web': 1, 'src': os.path.basename(f)[:-5]})
        n0 = len(rows)
        for r in it:
            if r and r[col['عنوان کتاب']]: rows.append((li, r, col))
        libs[li]['n'] = len(rows) - n0
        print(f'{libs[li]["name"]}: {libs[li]["n"]}')
    libs_order = sorted(range(len(libs)), key=lambda i: -libs[i]['n'])

    # --- 3. telegram works by key
    exist = {}
    for n in range((mhome['nworks'] + mSH - 1) // mSH):
        for i, w in enumerate(json.load(open(f'{main_data}/w/{n}.json', encoding='utf-8'))):
            exist.setdefault('|'.join([norm(w['t']), norm(w.get('v', '')), norm(w.get('a', '')), norm(w.get('tr', ''))]), n * mSH + i)

    works, wkey, attach = [], {}, collections.defaultdict(list)
    for li, r, col in rows:
        g = lambda n: s(r[col[n]]) if n in col else ''
        title = g('عنوان کتاب'); cover = g('تصویر جلد (لینک تلگرام)')
        c = {'ch': CH_OFF + li, 'l': url_of(g('لینک تلگرامی PDF')), 'sz': g('حجم فایل (MB)'), 'p': g('ناشر'), 'y': g('سال نشر'),
             'pg': g('تعداد صفحات'), 'isbn': g('شابک'), 'ed': g('نوبت چاپ'), 'note': g('توضیحات دیگر (از کپشن)'),
             'cu': short_cu(cover) if cover.startswith('http') else '', 'web': 1}
        vol, nvol = volume(g('جلد'))
        if nvol: c['note'] = '؛ '.join(x for x in [nvol, c['note']] if x)
        c = {k: v for k, v in c.items() if v not in ('', None)}
        author, tr = g('نویسنده / پدیدآورنده'), g('مترجم')
        key = '|'.join([norm(title), norm(vol), norm(author), norm(tr)])
        if key in exist: attach[exist[key]].append(c); continue
        if key in wkey: works[wkey[key]]['c'].append(c); continue
        wkey[key] = len(works)
        tag = g('موضوع / برچسب')
        w = {'t': title, 'st': g('زیرعنوان'), 'v': vol, 'a': author, 'tr': tr, 'e': g('مصحح / ویراستار / گردآورنده'), 'tag': tag,
             'lang': g('زبان'), 'c': [c], 'k': category(tag, title, libs[li]['name']), 'd': ''}
        works.append({k: v for k, v in w.items() if v != '' or k in ('c', 'd')})
    for w in works:
        w['c'].sort(key=lambda c: (bool(c.get('cu')), len(c)), reverse=True)
        w['y'] = w['c'][0].get('y', '')
        for ci in set(c['ch'] for c in w['c']): libs[ci - CH_OFF]['w'] += 1
    for cs in attach.values():
        for ci in set(c['ch'] for c in cs): libs[ci - CH_OFF]['w'] += 1
    print('online works', len(works), '; web copies on', len(attach), 'telegram books')

    def lite(i, w):
        c0 = w['c'][0]
        return [i, w['t'], w.get('a', ''), w.get('tr', ''), w.get('v', ''), len(w['c']), w.get('y', ''), (c0.get('p') or '')[:50],
                w.get('k', ''), c0['ch'], c0.get('cu', '')]

    # --- 4. attach web copies in the main repo (after the main copy, so they show among «نسخه‌های دیگر»)
    by = collections.defaultdict(dict)
    for wid, cs in attach.items(): by[wid // mSH][wid % mSH] = cs
    att_lite = {}
    for n, m in by.items():
        p = f'{main_data}/w/{n}.json'; arr = json.load(open(p, encoding='utf-8'))
        for i, cs in m.items():
            arr[i]['c'][1:1] = cs
            w = arr[i]; L = lite(n * mSH + i, w); L[10] = cs[0].get('cu', ''); att_lite[n * mSH + i] = (L, cs)
        dump(p, arr)

    # --- 5. online repo (rebuilt)
    for d in ('w', 'c', 'k', 'a', 's'): shutil.rmtree(os.path.join(odir, d), ignore_errors=True)
    for n in range(0, len(works), SHARD): dump(f'{odir}/w/{n // SHARD}.json', works[n:n + SHARD])
    lites = [lite(OBASE + i, w) for i, w in enumerate(works)]

    per_lib = collections.defaultdict(list)
    for L, w in zip(lites, works):
        for ci in sorted(set(c['ch'] for c in w['c'])): per_lib[ci - CH_OFF].append(L)
    for wid, (L, cs) in att_lite.items():
        for ci in set(c['ch'] for c in cs): per_lib[ci - CH_OFF].append(L)
    for li, ls in per_lib.items():
        for p in range(0, len(ls), PAGE): dump(f'{odir}/c/{li}/{p // PAGE}.json', ls[p:p + PAGE])

    # categories: interleave libraries so one large library does not fill the first pages
    per_cat = collections.defaultdict(lambda: collections.defaultdict(list))
    for L in lites: per_cat[L[8] or 'x'][L[9]].append(L)
    cats = []
    for k in list(CAT_NAMES):
        q = per_cat.get(k)
        if not q: continue
        lists = sorted(q.values(), key=len, reverse=True); out = []
        idx = [0] * len(lists); total = sum(map(len, lists))
        while len(out) < total:
            for j, ls in enumerate(lists):
                if idx[j] < len(ls): out.append(ls[idx[j]]); idx[j] += 1
        for p in range(0, len(out), PAGE): dump(f'{odir}/k/{k}/{p // PAGE}.json', out[p:p + PAGE])
        cats.append({'k': k, 'name': CAT_NAMES[k], 'n': len(out)})

    people = collections.defaultdict(lambda: {'n': '', 'o': [], 'r': []})
    for L, w in zip(lites, works):
        for fld, role in (('a', 'o'), ('tr', 'r')):
            for part in re.split(r'\s*[،,؛;]\s*|\s+و\s+(?=\S+\s+\S+)', w.get(fld) or ''):
                nn = norm(part)
                if len(nn) < 3: continue
                pp = people[nn]; pp['n'] = pp['n'] or part.strip(); pp[role].append(L)
    ash = collections.defaultdict(dict)
    for nn, pp in people.items():
        ash[fnv(nn) % ASH][nn] = {'n': pp['n'], 'o': pp['o'][:400], 'r': pp['r'][:400], 'no': len(pp['o']), 'nr': len(pp['r'])}
    for h, d in ash.items(): dump(f'{odir}/a/{h}.json', d)

    toks_of = []
    for w in works:
        toks = set()
        for fld in ('t', 'a', 'tr'):
            toks.update(tk for tk in norm(w.get(fld, '')).split() if len(tk) >= 2 and tk not in OSTOP and not tk.isdigit())
        toks_of.append(toks)
    by2 = collections.defaultdict(set)
    for i, toks in enumerate(toks_of):
        for tk in toks: by2[tk[:2]].add(i)
    shards = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, toks in enumerate(toks_of):
        for tk in toks:
            p2 = tk[:2]
            shards[p2 if len(by2[p2]) <= SEARCH_MAX or len(tk) == 2 else tk[:3]][tk].append(OBASE + i)
    def slite(L):   # ردیف کوتاه برای نتیجهٔ جستجو (حجم نمایه)
        return [L[0], L[1][:60], L[2][:30], '', L[4], L[5], '', '', L[8], L[9]]
    for key, tmap in shards.items():
        ids = sorted(set(i for v in tmap.values() for i in v))
        dump(f'{odir}/s/x' + ''.join(f'{ord(ch):x}-' for ch in key) + '.json', {'t': tmap, 'w': [slite(lites[i - OBASE]) for i in ids]})
    split = sorted(p for p, v in by2.items() if len(v) > SEARCH_MAX)
    dump(f'{odir}/s/manifest.json', {'split': split})

    dump(f'{odir}/attached.json', sorted(attach))
    dump(f'{odir}/home.json', {'built': datetime.now().strftime('%Y-%m-%d'), 'base': OBASE, 'choff': CH_OFF, 'nworks': len(works),
                               'nfiles': len(rows), 'attached': len(attach), 'shard': SHARD, 'page': PAGE, 'ashards': ASH,
                               'libs': libs, 'order': libs_order, 'cats': cats, 'cup': dict(CUP), 'stop': sorted(OSTOP)})
    print('done:', len(works), 'works,', len(shards), 'search shards,', len(people), 'people')


if __name__ == '__main__':
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(*sys.argv[1:])
