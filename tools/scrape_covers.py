#!/usr/bin/env python3
"""دانلود خودکار جلد کتاب‌ها از پیش‌نمایش عمومی کانال‌ها (t.me/s/…) — بدون نیاز به حساب تلگرام.

روی GitHub Actions اجرا می‌شود (.github/workflows/covers.yml). فقط کانال‌های عمومی.
  covers/<id // 1000>/<id>.webp   جلد کوچک
  covers/failed.txt               کتاب‌هایی که هیچ گزینه‌شان جلد نداشت
  data/cv.json                    بیت‌مپ کتاب‌های دارای جلد (برای مینی‌اپ)
اجرای دوباره از جای قبلی ادامه می‌دهد.
"""
import base64, csv, io, json, os, re, subprocess, sys, threading, time, collections
from concurrent.futures import ThreadPoolExecutor
import requests
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'covers')
WIDTH, QUALITY = 200, 62
BUDGET = float(os.environ.get('BUDGET_MIN', '320')) * 60
LIMIT = int(os.environ.get('LIMIT', '0'))
UA = {'User-Agent': 'Mozilla/5.0 (compatible; library-covers/1.0)'}
T0 = time.time()
lock = threading.Lock()
stats = collections.Counter()

def out_path(wid): return os.path.join(OUT, str(wid // 1000), f'{wid}.webp')

def git(*a):
    return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True)

def commit(msg):
    with lock:
        git('add', 'covers', 'data/cv.json')
        if git('diff', '--cached', '--quiet').returncode == 0:
            return
        git('commit', '-qm', msg)
        for _ in range(5):
            if git('push', '-q').returncode == 0:
                return
            git('pull', '-q', '--rebase', '-X', 'theirs')
        print('push failed', flush=True)

def write_bitmap():
    home = json.load(open(os.path.join(ROOT, 'data/home.json'), encoding='utf-8'))
    n = home['nworks']; bits = bytearray((n + 7) // 8)
    for d in os.listdir(OUT):
        if d.isdigit():
            for f in os.listdir(os.path.join(OUT, d)):
                if f.endswith('.webp'):
                    i = int(f[:-5]); bits[i >> 3] |= 1 << (i & 7)
    json.dump({'n': n, 'b': base64.b64encode(bytes(bits)).decode()}, open(os.path.join(ROOT, 'data/cv.json'), 'w'))
    return sum(bin(b).count('1') for b in bits)

MSG_RE = re.compile(r'data-post="([^"/]+)/(\d+)"')
IMG_RE = re.compile(r'class="(?:tgme_widget_message_photo_wrap|tgme_widget_message_document_thumb|tgme_widget_message_video_thumb)[^"]*"[^>]*?background-image:url\(\'([^\']+)\'\)')

session = requests.Session(); session.headers.update(UA)

def get(url, tries=6):
    for k in range(tries):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 429:
                time.sleep(int(r.headers.get('Retry-After', 30)) + 5); continue
            if r.status_code == 200:
                return r
            if r.status_code in (404, 403):
                return None
        except requests.RequestException:
            pass
        time.sleep(3 * (k + 1))
    return None

OG_RE = re.compile(r'<meta property="og:image" content="([^"]+)"')
avatars = {}

def avatar(ch):
    if ch not in avatars:
        r = get(f'https://t.me/{ch}')
        m = OG_RE.search(r.text) if r is not None else None
        avatars[ch] = m.group(1) if m else ''
    return avatars[ch]

def post_image(ch, mid):
    """تصویر پست (عکس یا پیش‌نمایش PDF) از برچسب og:image صفحهٔ تک‌پست؛ تصویر نمایهٔ کانال حساب نمی‌شود."""
    r = get(f'https://t.me/{ch}/{mid}')
    stats['pages'] += 1
    if r is None: return None
    m = OG_RE.search(r.text)
    if not m: return None
    url = m.group(1).replace('&amp;', '&')
    if url == avatar(ch) or 'telegram.org/img' in url: return None
    return url

def fetch_img(url, wid):
    r = get(url, tries=3)
    if r is None: return False
    try:
        im = Image.open(io.BytesIO(r.content)).convert('RGB')
        if im.width < 60 or im.height < 60: return False
        if im.width > WIDTH: im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
        os.makedirs(os.path.dirname(out_path(wid)), exist_ok=True)
        im.save(out_path(wid), 'WEBP', quality=QUALITY, method=6)
        return True
    except Exception:
        return False

def main():
    os.makedirs(OUT, exist_ok=True)
    fpath = os.path.join(OUT, 'failed.txt')
    failed = set(open(fpath).read().split()) if os.path.exists(fpath) else set()
    rows = list(csv.reader(open(os.path.join(ROOT, 'tools/covers_todo.csv'), encoding='utf-8')))[1:]
    todo = []
    for r in rows:
        wid = int(r[0])
        if os.path.exists(out_path(wid)) or str(wid) in failed: continue
        c = [(r[i], int(r[i + 1])) for i in range(1, len(r) - 2, 3) if r[i] and not r[i].lstrip('-').isdigit()]
        if c: todo.append((wid, c))
        else: failed.add(str(wid))
    if LIMIT: todo = todo[:LIMIT]
    print(f'total {len(rows)} | todo {len(todo)}', flush=True)
    rnd = 0
    while todo and time.time() - T0 < BUDGET:
        rnd += 1
        for ch in set(c[0][0] for _, c in todo): avatar(ch)
        with ThreadPoolExecutor(8) as ex:
            urls = list(ex.map(lambda t: post_image(*t[1][0]) if time.time() - T0 < BUDGET else None, todo))
        jobs, nxt = [], []
        for (wid, c), url in zip(todo, urls):
            if url: jobs.append((wid, url, c))
            elif len(c) > 1: nxt.append((wid, c[1:]))
            elif time.time() - T0 < BUDGET: failed.add(str(wid))
        print(f'round {rnd}: pages {stats["pages"]} | images found {len(jobs)}', flush=True)
        done = 0
        with ThreadPoolExecutor(16) as ex:
            for (wid, url, c), ok in zip(jobs, ex.map(lambda j: fetch_img(j[1], j[0]), jobs)):
                if ok:
                    done += 1
                    if done % 3000 == 0:
                        write_bitmap(); commit(f'جلد کتاب‌ها: +{done}'); print(f'  saved {done}', flush=True)
                elif len(c) > 1: nxt.append((wid, c[1:]))
                else: failed.add(str(wid))
        print(f'round {rnd}: saved {done}', flush=True)
        todo = nxt
    open(fpath, 'w').write('\n'.join(sorted(failed, key=int)))
    have = write_bitmap()
    commit(f'جلد کتاب‌ها: {have} جلد')
    left = len(todo)
    print(f'done. covers: {have} | failed: {len(failed)} | left: {left}', flush=True)
    with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
        f.write(f'left={left}\n')

if __name__ == '__main__':
    main()
