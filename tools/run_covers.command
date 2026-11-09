#!/bin/bash
# دانلود جلد کتاب‌ها — macOS/Linux: دوبار کلیک (یا: bash tools/run_covers.command)
cd "$(dirname "$0")/.." || exit 1
echo "==== دانلود جلد کتاب‌های کتابخانه ===="
command -v python3 >/dev/null || { echo "پایتون ۳ نصب نیست. از python.org نصبش کنید."; read -r; exit 1; }
python3 -m pip install --quiet --user telethon pillow 2>/dev/null || python3 -m pip install --quiet --break-system-packages telethon pillow
if [ ! -f tools/api.txt ]; then
  read -r -p "api_id را وارد کنید: " APIID
  read -r -p "api_hash را وارد کنید: " APIHASH
  echo "$APIID $APIHASH" > tools/api.txt
fi
read -r APIID APIHASH < tools/api.txt
python3 tools/fetch_covers.py --api-id "$APIID" --api-hash "$APIHASH" "$@"
echo; read -r -p "برای بستن Enter بزنید" _
