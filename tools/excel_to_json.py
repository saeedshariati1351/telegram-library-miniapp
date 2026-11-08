#!/usr/bin/env python3
"""تبدیل فایل اکسل فهرست کتابخانه به data/books.json

    pip install openpyxl
    python3 tools/excel_to_json.py catalog.xlsx data/books.json

هر سطر اکسل = یک فایل PDF در یک کانال. سطرهایی که عنوان، پدیدآور و مترجمِ یکسان
(یا شابکِ یکسان) دارند یک کتاب حساب می‌شوند: نخستین سطر (یا سطری که ستون «اصلی»
آن پر است) پیوند اصلی است و بقیه «نسخه‌های دیگر در کانال‌ها» می‌شوند.
نام ستون‌ها را در COLUMNS می‌شود با سرستون‌های اکسل هماهنگ کرد.
"""
import json, sys, datetime
from openpyxl import load_workbook

# کلید JSON  ←  نام‌های ممکن سرستون در اکسل
COLUMNS = {
    "title":      ["عنوان", "نام کتاب", "title"],
    "author":     ["پدیدآور", "نویسنده", "مؤلف", "author"],
    "translator": ["مترجم", "translator"],
    "publisher":  ["ناشر", "publisher"],
    "place":      ["محل نشر", "شهر"],
    "year":       ["سال نشر", "سال", "year"],
    "edition":    ["نوبت چاپ", "ویراست", "edition"],
    "pages":      ["تعداد صفحات", "شمار صفحات", "صفحه", "pages"],
    "isbn":       ["شابک", "isbn"],
    "congress":   ["رده‌بندی کنگره", "ردهٔ کنگره", "کنگره"],
    "dewey":      ["رده‌بندی دیویی", "ردهٔ دیویی", "دیویی"],
    "nlNumber":   ["شماره کتابشناسی ملی", "شمارهٔ کتابشناسی ملی", "کتابشناسی ملی"],
    "subjects":   ["موضوع", "موضوعات"],
    "category":   ["دسته", "دسته‌بندی", "گروه"],
    "channel":    ["نام کانال", "کانال", "channel"],
    "channelLink":["لینک کانال", "پیوند کانال"],
    "link":       ["لینک تلگرام", "لینک فایل", "لینک PDF", "پیوند", "لینک", "link"],
    "size":       ["حجم", "حجم (مگابایت)", "size"],
    "cover":      ["تصویر جلد", "لینک جلد", "جلد", "cover"],
    "main":       ["اصلی", "main"],
    "source":     ["منبع", "منبع اطلاعات"],
    "work":       ["شناسه اثر", "work"],
}

def clean(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()

def main(src, dst):
    wb = load_workbook(src, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = [clean(h).replace("‌", " ") for h in next(rows)]
    idx = {}
    for key, names in COLUMNS.items():
        for n in names:
            n2 = n.replace("‌", " ")
            if n2 in header:
                idx[key] = header.index(n2)
                break
    if "title" not in idx:
        sys.exit("ستون «عنوان» پیدا نشد. سرستون‌ها: %s" % header)
    books = []
    for r in rows:
        b = {}
        for key, i in idx.items():
            v = clean(r[i] if i < len(r) else "")
            if v:
                b[key] = v
        if not b.get("title"):
            continue
        if "subjects" in b:
            b["subjects"] = [s.strip() for s in b["subjects"].replace("؛", ";").split(";") if s.strip()]
        if "main" in b:
            b["main"] = True
        books.append(b)
    try:
        old = json.load(open(dst, encoding="utf-8"))
        authors, featured = old.get("authors", {}), old.get("featured", "")
    except Exception:
        authors, featured = {}, ""
    out = {"sample": False, "updated": datetime.date.today().isoformat(),
           "featured": featured, "authors": authors, "books": books}
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%d سطر نوشته شد ← %s" % (len(books), dst))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
