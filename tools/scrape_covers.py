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

def scan_channel(ch, ids):
    """برگشتی: {msg_id: image_url} برای همهٔ پیام‌های خواسته‌شده که تصویر دارند."""
    found = {}
    want = sorted(set(ids), reverse=True)
    i = 0
    while i < len(want):
        if time.time() - T0 > BUDGET: break
        top = want[i]
        r = get(f'https://t.me/s/{ch}?before={top + 1}')
        if r is None:
            i += 1; continue
        html = r.text
        parts = MSG_RE.split(html)        # [pre, ch, id, body, ch, id, body, ...]
        page = {}
        for k in range(1, len(parts) - 2, 3):
            mid = int(parts[k + 1]); m = IMG_RE.search(parts[k + 2][:6000])
            page[mid] = m.group(1) if m else None
        stats['pages'] += 1
        if stats['pages'] <= 2:
            print(f'[debug] {ch} before={top+1}: {len(page)} msgs, imgs={sum(1 for v in page.values() if v)}, html={len(html)}', flush=True)
            if not any(page.values()):
                t = re.search(r'<title>(.*?)</title>', html, re.S)
                print('[debug-title]', t.group(1).strip() if t else '-', '| final url', r.url, flush=True)
                b = html.find('<body'); print('[debug-body]', re.sub(r'\s+', ' ', re.sub(r'<script.*?</script>', '', html[b:], flags=re.S))[:1500], flush=True)
                r2 = get(f'https://t.me/s/{ch}/{top}')
                if r2 is not None:
                    print('[debug-alt]', r2.url, len(r2.text), len(MSG_RE.findall(r2.text)), 'imgs', len(IMG_RE.findall(r2.text)), flush=True)
        if not page:
            i += 1; continue
        lo = min(page)
        for mid, url in page.items():
            if url: found[mid] = url
        while i < len(want) and want[i] >= lo: i += 1
        if top not in page and lo > top:     # پیام پاک شده یا بیرون از بازه
            pass
        time.sleep(0.7)
    return found

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
        by_ch = collections.defaultdict(list)
        for wid, c in todo: by_ch[c[0][0]].append(c[0][1])
        with ThreadPoolExecutor(12) as ex:
            res = dict(zip(by_ch, ex.map(lambda kv: scan_channel(*kv), by_ch.items())))
        jobs, nxt = [], []
        for wid, c in todo:
            url = res.get(c[0][0], {}).get(c[0][1])
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
