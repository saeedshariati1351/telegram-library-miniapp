#!/usr/bin/env python3
"""دانلود جلد کتاب‌ها از کانال‌های تلگرام (با حساب تلگرام خودتان)

پیش‌نیاز (یک بار):
    pip install telethon pillow
    در https://my.telegram.org  ← API development tools یک برنامه بسازید و api_id و api_hash را بردارید.

اجرا (از پوشهٔ مخزن):
    python tools/fetch_covers.py --api-id 123456 --api-hash abcdef...

بار نخست شمارهٔ تلفن و کد ورود تلگرام را خودتان در همین پنجره وارد می‌کنید
(نشست در فایل tools/covers.session ذخیره می‌شود و دفعه‌های بعد لازم نیست).

خروجی:
    covers/<id // 1000>/<id>.webp   جلد کوچک (عرض ۲۰۰ پیکسل)
    covers/index.txt                شناسهٔ کتاب‌هایی که جلد دارند (برای ساخت داده‌ها)
    covers/failed.txt               کتاب‌هایی که جلدشان پیدا نشد

اگر اجرا قطع شد، دوباره همان فرمان را بزنید: از جای قبلی ادامه می‌دهد.
"""
import argparse, asyncio, csv, io, os, sys, time, collections
from telethon import TelegramClient, errors
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, PhotoSize, PhotoSizeProgressive, PhotoCachedSize, PhotoStrippedSize
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WIDTH, QUALITY = 200, 62

def out_path(out, wid):
    return os.path.join(out, str(wid // 1000), f'{wid}.webp')

def pick_size(sizes):
    """کوچک‌ترین اندازه‌ای که عرضش دست‌کم ۳۰۰ پیکسل است، وگرنه بزرگ‌ترین."""
    good = [s for s in sizes if isinstance(s, (PhotoSize, PhotoSizeProgressive)) and getattr(s, 'w', 0)]
    if not good:
        return None
    good.sort(key=lambda s: s.w)
    for s in good:
        if s.w >= 300:
            return s
    return good[-1]

def save_webp(data, path):
    im = Image.open(io.BytesIO(data)).convert('RGB')
    if im.width < 60 or im.height < 60:
        return False
    if im.width > WIDTH:
        im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, 'WEBP', quality=QUALITY, method=6)
    return True

async def grab(client, msg, kind):
    if msg is None or msg.media is None:
        return None
    m = msg.media
    if isinstance(m, MessageMediaPhoto) and m.photo:
        size = pick_size(m.photo.sizes)
        return await client.download_media(msg, file=bytes, thumb=size) if size else None
    if isinstance(m, MessageMediaDocument) and m.document:
        thumbs = m.document.thumbs or []
        size = pick_size(thumbs)
        if size:
            return await client.download_media(msg, file=bytes, thumb=size)
        mime = m.document.mime_type or ''
        if mime.startswith('image/') and m.document.size < 3_000_000:
            return await client.download_media(msg, file=bytes)
    return None

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--api-id', type=int, required=True)
    ap.add_argument('--api-hash', required=True)
    ap.add_argument('--todo', default=os.path.join(HERE, 'covers_todo.csv'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'covers'))
    ap.add_argument('--limit', type=int, default=0, help='فقط این تعداد کتاب (برای آزمایش)')
    a = ap.parse_args()

    rows = list(csv.reader(open(a.todo, encoding='utf-8')))[1:]
    failed_path = os.path.join(a.out, 'failed.txt')
    os.makedirs(a.out, exist_ok=True)
    failed = set(open(failed_path).read().split()) if os.path.exists(failed_path) else set()
    todo = []
    for r in rows:
        wid = int(r[0])
        if os.path.exists(out_path(a.out, wid)) or str(wid) in failed:
            continue
        cands = [(r[i], int(r[i + 1]), r[i + 2]) for i in range(1, len(r) - 2, 3) if r[i]]
        todo.append((wid, cands))
    if a.limit:
        todo = todo[:a.limit]
    total, done0 = len(rows), len(rows) - len(todo)
    print(f'کل: {total} | انجام‌شده: {done0} | مانده: {len(todo)}', flush=True)

    client = TelegramClient(os.path.join(HERE, 'covers'), a.api_id, a.api_hash, flood_sleep_threshold=300)
    await client.start()
    entities = {}

    async def entity(peer):
        if peer not in entities:
            try:
                entities[peer] = await client.get_entity(int(peer) if peer.lstrip('-').isdigit() else peer)
            except Exception as e:
                print(f'  کانال در دسترس نیست: {peer} ({type(e).__name__})', flush=True)
                entities[peer] = None
        return entities[peer]

    # پیام‌ها را دسته‌ای (۱۰۰تایی) از هر کانال می‌گیریم
    pending = collections.deque(todo)
    ok = fail = 0
    t0 = time.time()
    ff = open(failed_path, 'a')
    while pending:
        # گروه‌بندی بر اساس نخستین گزینهٔ مانده
        batch = collections.defaultdict(list)
        while pending and sum(len(v) for v in batch.values()) < 300:
            wid, cands = pending.popleft()
            batch[cands[0][0]].append((wid, cands))
        for peer, items in batch.items():
            ent = await entity(peer)
            msgs = {}
            if ent is not None:
                ids = [c[0][1] for _, c in items]
                for k in range(0, len(ids), 100):
                    try:
                        got = await client.get_messages(ent, ids=ids[k:k + 100])
                    except errors.FloodWaitError as e:
                        print(f'  مکث اجباری تلگرام: {e.seconds} ثانیه', flush=True)
                        await asyncio.sleep(e.seconds + 2)
                        got = await client.get_messages(ent, ids=ids[k:k + 100])
                    except Exception as e:
                        print(f'  خطا در {peer}: {type(e).__name__}', flush=True)
                        got = []
                    for msg in got or []:
                        if msg is not None:
                            msgs[msg.id] = msg
            for wid, cands in items:
                data = None
                try:
                    data = await grab(client, msgs.get(cands[0][1]), cands[0][2])
                except errors.FloodWaitError as e:
                    print(f'  مکث اجباری تلگرام: {e.seconds} ثانیه', flush=True)
                    await asyncio.sleep(e.seconds + 2)
                except Exception:
                    data = None
                if data and save_webp(data, out_path(a.out, wid)):
                    ok += 1
                elif len(cands) > 1:
                    pending.append((wid, cands[1:]))      # گزینهٔ بعدی همین کتاب
                else:
                    fail += 1; ff.write(f'{wid}\n'); ff.flush()
        n = ok + fail
        if n:
            rate = n / (time.time() - t0)
            left = len(pending) / rate / 60 if rate else 0
            print(f'جلد ذخیره‌شده: {done0 + ok} | ناموفق: {fail} | مانده: {len(pending)} | حدود {left:.0f} دقیقهٔ دیگر', flush=True)
    ff.close()
    # فهرست جلدها
    have = sorted(int(f[:-5]) for d in os.listdir(a.out) if d.isdigit() for f in os.listdir(os.path.join(a.out, d)) if f.endswith('.webp'))
    with open(os.path.join(a.out, 'index.txt'), 'w') as f:
        f.write('\n'.join(map(str, have)))
    print(f'تمام شد. {len(have)} جلد در {a.out}', flush=True)
    await client.disconnect()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nمتوقف شد. با اجرای دوباره از همین‌جا ادامه می‌دهد.')
